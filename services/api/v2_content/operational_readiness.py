"""Read-only readiness for the explicitly enabled D28 trial prototype.

Check the compiled bank used for new journeys and every retained pinned bank
used by existing journeys, assessments and lessons. Never seed, activate,
repair or replace a student's original release from an unauthenticated probe.
"""
from __future__ import annotations

from hashlib import sha256

from sqlalchemy import or_, select, union

from db.database import SessionLocal
from db.learning_models import LessonSession, StudentJourney
from db.models import AssessmentSession, ContentRelease
from .compiler import RELEASE_SCHEMA, _canonical
from .media import MediaProvider
from .readiness import media_readiness_contract, usage_map
from .repository import get_pinned_release, get_release


def _media_ready(bank: dict) -> bool:
    ids = [asset["id"] for asset in bank["media"]]
    if len(ids) != len(set(ids)) or not set(usage_map(bank)).issubset(ids):
        return False
    # No generic fixture may satisfy operational readiness, even in trial.
    return media_readiness_contract(
        bank, provider=MediaProvider(fixture_enabled=False),
    )["publishable"]


def _pinned_bank_ready(db, row: ContentRelease) -> bool:
    bank = get_pinned_release(db, row.id)
    manifest = row.manifest_json or {}
    # Private snapshots intentionally omit public metadata. Reconstruct the
    # original compiler payload to detect edits to answers as well as labels.
    payload = {
        "schema_version": row.schema_version,
        "state": manifest.get("state"),
        "sources": manifest.get("sources"),
        "counts": manifest.get("counts"),
        **{key: bank[key] for key in ("lessons", "supports", "questions", "media")},
    }
    return (
        row.schema_version == RELEASE_SCHEMA
        and sha256(_canonical(payload)).hexdigest() == row.checksum
        and _media_ready({**bank, "state": manifest.get("state")})
    )


def content_ready() -> bool:
    db = SessionLocal()
    try:
        # Compilation validates counts, skills, interactions and all ownership/
        # question bindings. Cached source compilation is immutable per process;
        # media presence and pinned DB content are checked on every probe.
        current = get_release()
        if not _media_ready(current):
            return False
        current_rows = db.query(ContentRelease).filter(or_(
            ContentRelease.version == current["version"],
            ContentRelease.checksum == current["checksum"],
        )).all()
        if any(row.version != current["version"] or row.checksum != current["checksum"]
               for row in current_rows):
            return False
        # Registration is deliberately lazy at first assessment start. An empty
        # installation can be ready without writing a candidate from this probe.
        pinned_ids = union(
            select(StudentJourney.content_release_id),
            select(LessonSession.content_release_id),
            select(AssessmentSession.content_release_id).where(
                AssessmentSession.v2_state.is_not(None)),
        )
        ids = set(db.execute(pinned_ids).scalars()) | {row.id for row in current_rows}
        rows = db.query(ContentRelease).filter(ContentRelease.id.in_(ids)).all() if ids else []
        return len(rows) == len(ids) and all(_pinned_bank_ready(db, row) for row in rows)
    except Exception:
        # No DB details, private keys, paths or dependency errors in public /ready.
        return False
    finally:
        db.close()


def approved_media_ready() -> bool:
    """Check deployed V2 dependencies instead of the unrelated V1 audio pack."""
    try:
        return _media_ready(get_release())
    except Exception:
        return False
