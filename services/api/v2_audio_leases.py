"""Durable V2 audio upload binding and leasing, independent of S3 clients.

Exactly one canonical implementation is shared by the legacy upload API
and the native reading engine to prevent mismatched retry semantics.
"""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from db.models import AudioUploadLease


def audio_upload_binding(kind: str, container_id: int, question_id: str) -> str:
    """Return a stable, non-secret scope for one upload/answer workflow."""
    if kind not in {"lesson", "assessment", "retry"}:
        raise ValueError("Unsupported audio upload context")
    if container_id <= 0 or not question_id or ":" in question_id:
        raise ValueError("Invalid audio upload context")
    binding_key = f"{kind}:{container_id}:{question_id}"
    if len(binding_key) > 255:
        raise ValueError("Audio upload context is too long")
    return binding_key


def track_new_audio_upload(
    db: Session, *, student_id: int, storage_key: str, binding_key: str,
) -> None:
    """Register S3 content as unsubmitted until an answer transaction accepts it."""
    if not storage_key.startswith(f"audio/{student_id}/"):
        raise ValueError("Audio upload student mismatch")
    if not binding_key:
        raise ValueError("Audio upload context is required")
    lease = db.query(AudioUploadLease).filter(AudioUploadLease.storage_key == storage_key).one_or_none()
    if lease is not None:
        if lease.student_id != student_id or lease.state not in ("temporary", "submitted"):
            raise ValueError("Audio upload no longer available or owned by another student")
        if lease.binding_key != binding_key:
            raise ValueError("Audio upload is bound to a different question")
        return
    db.add(AudioUploadLease(
        student_id=student_id,
        storage_key=storage_key,
        binding_key=binding_key,
        state="temporary",
    ))
    db.flush()


def mark_audio_submitted(
    db: Session, *, student_id: int, storage_key: str, binding_key: str,
) -> None:
    """Accept only the upload created for this exact workflow and question."""
    lease = db.query(AudioUploadLease).filter(AudioUploadLease.storage_key == storage_key).with_for_update().one_or_none()
    if lease is None:
        raise ValueError("Audio upload lease is missing")
    if lease.student_id != student_id or lease.state not in ("temporary", "submitted"):
        raise ValueError("This audio upload is no longer available")
    if lease.binding_key != binding_key:
        raise ValueError("Audio upload is bound to a different question")
    lease.state = "submitted"
    lease.submitted_at = datetime.now(timezone.utc)


