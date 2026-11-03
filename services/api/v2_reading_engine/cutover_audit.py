"""Read-only release gate for removal of pre-cutover human-review APIs.

Return counts only: no child identities, recordings, transcriptions or raw SQL
data. All statements are SELECTs; absolutely no data changes.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.learning_models import (
    AssessmentQuestionResponse, LessonQuestionResponse, V2ReviewRetryTask,
)
from db.v2_reading_models import V2ReadingJob


def native_cutover_audit(db: Session) -> dict[str, int | bool]:
    """Count pending responses that have NO current native reading job."""
    pending_lesson = db.scalar(
        select(func.count(LessonQuestionResponse.id)).where(
            LessonQuestionResponse.status == "pending_review",
            ~select(V2ReadingJob.id).where(
                V2ReadingJob.lesson_response_id == LessonQuestionResponse.id,
                V2ReadingJob.is_current.is_(True),
            ).exists(),
        )
    ) or 0
    pending_assessment = db.scalar(
        select(func.count(AssessmentQuestionResponse.id)).where(
            AssessmentQuestionResponse.status == "pending_review",
            ~select(V2ReadingJob.id).where(
                V2ReadingJob.assessment_response_id == AssessmentQuestionResponse.id,
                V2ReadingJob.is_current.is_(True),
            ).exists(),
        )
    ) or 0
    active_staff_retry = db.scalar(
        select(func.count(V2ReviewRetryTask.id)).where(
            V2ReviewRetryTask.status.in_(("requested", "submitted")),
        )
    ) or 0
    pending_native = db.scalar(
        select(func.count(V2ReadingJob.id)).where(
            V2ReadingJob.is_current.is_(True),
            V2ReadingJob.status.in_((
                "queued", "processing", "retry_wait", "evidence_ready",
                "retry_audio", "service_unavailable",
            )),
        )
    ) or 0
    return {
        "legacy_lesson_pending": int(pending_lesson),
        "legacy_assessment_pending": int(pending_assessment),
        "active_manual_retry_tasks": int(active_staff_retry),
        "native_jobs_waiting": int(pending_native),
        "can_retire_manual_routes": not bool(
            pending_lesson or pending_assessment or active_staff_retry
        ),
    }


def main() -> int:
    """Use the ORIGINAL project's existing DB connection (no extra service)."""
    import json

    from db.database import SessionLocal

    with SessionLocal() as db:
        result = native_cutover_audit(db)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["can_retire_manual_routes"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
