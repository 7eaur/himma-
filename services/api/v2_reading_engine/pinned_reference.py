"""Resolve reading reference and feedback mode from the pinned V2 release.

No student-provided text, task kind, language, or reference is authoritative.
The caller passes only an authenticated owned recording and question identity.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from .job_store import ReadingConflict, V2ReadingJob, enqueue_reading


_KIND_BY_EVIDENCE = {
    "syllable_reading": "letter",
    "sound_blending": "word",
    "simple_word_reading": "word",
    "long_word_reading": "word",
    "sentence_reading": "sentence",
    "connected_sentence_reading": "sentence",
    "short_text_reading": "text",
}
_EVALUATION_ROLES = {"pretest", "posttest", "independent_check", "support_check"}
_TRAINING_ROLES = {"guided_practice"}


@dataclass(frozen=True)
class PinnedReadingQuestion:
    question_id: str
    reference: str
    kind: str
    mode: str
    role: str


def _load_pinned_release(db: Session, content_release_id: int) -> dict:
    # Lazy import keeps pure DB policy tests independent of full FastAPI compiler.
    from v2_content.repository import get_pinned_release
    return get_pinned_release(db, content_release_id)


def resolve_pinned_reading(
    db: Session, *, content_release_id: int, question_id: str,
) -> PinnedReadingQuestion:
    """Resolve the *private* reading target of the actual immutable release."""
    release = _load_pinned_release(db, content_release_id)
    if not isinstance(release, dict) or not isinstance(release.get("questions"), list):
        raise ReadingConflict("Pinned V2 content release is unavailable")
    matching = [q for q in release["questions"]
                if isinstance(q, dict) and q.get("id") == question_id]
    if len(matching) != 1:
        raise ReadingConflict("Question ID missing or duplicated in pinned release")
    q = matching[0]
    if q.get("interaction") != "read_aloud":
        raise ReadingConflict("Question is not a reading activity")
    role = q.get("role")
    if role in _EVALUATION_ROLES:
        mode = "assessment"
    elif role in _TRAINING_ROLES:
        mode = "training"
    else:
        raise ReadingConflict("Unsupported V2 reading role")

    kind = _KIND_BY_EVIDENCE.get(q.get("evidence_type"))
    if kind is None:
        raise ReadingConflict("Unrecognized reading evidence type")
    rubric = (q.get("private_answer") or {}).get("rubric") or {}
    authored = q.get("reading_reference")
    rubric_reference = rubric.get("reference_text")
    reference = authored or rubric_reference
    if not isinstance(reference, str) or not reference.strip():
        raise ReadingConflict("Approved reading reference is missing")
    if authored and rubric_reference and authored != rubric_reference:
        raise ReadingConflict("Pinned reading references disagree")

    return PinnedReadingQuestion(
        question_id=question_id, reference=reference,
        kind=kind, mode=mode, role=role,
    )


def enqueue_pinned_reading(
    db: Session, *, student_id: int, audio_submission_id: int,
    content_release_id: int, question_id: str,
) -> V2ReadingJob:
    """Use server-owned reference, not text supplied by browser."""
    pinned = resolve_pinned_reading(
        db, content_release_id=content_release_id,
        question_id=question_id,
    )
    return enqueue_reading(
        db, student_id=student_id, audio_submission_id=audio_submission_id,
        content_release_id=content_release_id,
        question_id=pinned.question_id,
        reference_text=pinned.reference, reading_kind=pinned.kind,
        learning_mode=pinned.mode,
    )
