"""Exact historical-bank restoration; insert-only, never remap a learner's evidence."""
from __future__ import annotations

import gzip
from hashlib import sha256
import json
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.learning_models import PrivateContentBankSnapshot
from db.models import AuditLog, ContentRelease

RECOVERY_ROOT = Path(__file__).with_name("historical_releases")
RECOVERY_SOURCES = {
    "b78f8b01cdf00b9b0c9e311fb424d24c1bb286a0066fefb48fb6639235c2b085":
        "2100143cda6d2b06d76009951d59f02dd07f497e",
}


def known_recovery(checksum: str | None) -> bool:
    return checksum in RECOVERY_SOURCES


def restore_original_snapshot(db: Session, release_id: int, actor_id: int) -> dict:
    row = db.query(ContentRelease).filter(ContentRelease.id == release_id).with_for_update().one_or_none()
    if row is None or not known_recovery(row.checksum):
        raise HTTPException(status_code=409, detail="لا توجد نسخة أصلية مطابقة موثقة لهذا الإصدار")
    checksum = row.checksum
    path = RECOVERY_ROOT / f"{checksum}.json.gz"
    try:
        release = json.loads(gzip.decompress(path.read_bytes()))
        payload = {key: value for key, value in release.items() if key not in {"version", "checksum"}}
        digest = sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise HTTPException(status_code=409, detail="تعذر التحقق من ملف النسخة الأصلية") from error
    if digest != checksum or release.get("checksum") != checksum or release.get("version") != row.version:
        raise HTTPException(status_code=409, detail="بصمة النسخة الأصلية لا تطابق سجل الإصدار؛ لم تتغير البيانات")
    snapshot_payload = {key: release[key] for key in ("version", "checksum", "lessons", "supports", "questions", "media")}
    existing = db.query(PrivateContentBankSnapshot).filter(PrivateContentBankSnapshot.content_release_id == row.id).one_or_none()
    if existing is not None:
        if existing.checksum != checksum or existing.payload_json != snapshot_payload:
            raise HTTPException(status_code=409, detail="توجد نسخة محفوظة مختلفة؛ الاستبدال ممنوع")
        return {"status": "already_present", "release_id": row.id}
    db.add(PrivateContentBankSnapshot(content_release_id=row.id, checksum=checksum, payload_json=snapshot_payload))
    db.add(AuditLog(actor_role="researcher", actor_id=actor_id,
                    action="v2.content.snapshot_restored", entity_type="content_release", entity_id=str(row.id),
                    details=json.dumps({"checksum": checksum, "source_commit": RECOVERY_SOURCES[checksum]}, sort_keys=True)))
    db.flush()
    return {"status": "restored", "release_id": row.id}
