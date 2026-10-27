"""A10/W2 regression for explicit speech dead-letter recovery."""

from datetime import datetime, timedelta, timezone

from conftest import TestingSessionLocal
from db.models import AuditLog, User
from speech_analysis import retry_job
from speech_pipeline import enqueue_submission
from test_speech_pipeline import _submission


def test_dead_letter_manual_recovery_starts_fresh_audited_retry_cycle():
    db = TestingSessionLocal()
    try:
        audio = _submission(db)
        job = enqueue_submission(db, audio.id)
        job.status = "dead_letter"
        job.attempt_count = job.max_attempts
        job.next_attempt_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        job.lease_owner = "abandoned-worker"
        job.lease_expires_at = datetime.now(timezone.utc) + timedelta(minutes=2)
        job.last_error_code = "temporary_provider_error"
        job.last_error_message = "temporary outage"
        db.commit()

        researcher = db.query(User).filter(User.role == "researcher").one()
        result = retry_job(job.id, db=db, researcher=researcher)
        db.refresh(job)

        assert result == {"job_id": job.id, "status": "queued", "attempt_count": 0}
        assert job.status == "queued"
        assert job.attempt_count == 0
        assert job.next_attempt_at is None
        assert job.lease_owner is None
        assert job.lease_expires_at is None
        assert job.last_error_code is None
        assert job.last_error_message is None

        audit = db.query(AuditLog).filter(
            AuditLog.action == "retry_speech_analysis",
            AuditLog.entity_type == "SpeechAnalysisJob",
            AuditLog.entity_id == str(job.id),
        ).one()
        assert "status=dead_letter" in (audit.details or "")
        assert f"previous_attempt_count={job.max_attempts}" in (audit.details or "")
    finally:
        db.close()
