"""Reopen ONE ungraded legacy lesson reading; preserve all academic history.

Run from services/api. Dry-run by default; --apply requires explicit identity.
No grades, completed lessons, media files or accounts are deleted.
"""
from __future__ import annotations
import argparse
import json
from sqlalchemy import select
from db.database import SessionLocal
from db.models import Student, AudioSubmission, AuditLog
from db.learning_models import LessonSession, LessonQuestionResponse, SkillEvidence, V2ReviewRetryTask
from db.v2_reading_models import V2ReadingJob
from v2_content.repository import get_pinned_release
from v2_reading_engine.pinned_reference import enqueue_pinned_reading
from v2_reading_engine.runtime import native_runtime_configuration

def recover(db, student_id, expected_name, expected_lesson, apply=False):
    student = db.get(Student, student_id, with_for_update=True)
    if student is None or student.name.strip() != expected_name.strip():
        raise ValueError("Student identity does not match")
    if native_runtime_configuration() is None:
        raise ValueError("Native reading must be configured")
    rows = db.execute(select(LessonQuestionResponse, LessonSession).join(
        LessonSession, LessonSession.id == LessonQuestionResponse.lesson_session_id
    ).where(LessonSession.student_id == student_id,
            LessonQuestionResponse.status == "pending_review").with_for_update()).all()
    if len(rows) != 1:
        raise ValueError("Expected exactly one pending reading")
    answer, session = rows[0]
    if (session.lesson_id != expected_lesson or answer.is_correct is not None
            or answer.question_score_fraction is not None or answer.support_assignment_id is not None
            or answer.role not in {"guided_practice", "independent_check"}
            or session.status not in {"in_progress", "waiting_review"}):
        raise ValueError("Only an active, ungraded ordinary lesson reading can reopen")
    proof = db.scalar(select(SkillEvidence).where(SkillEvidence.response_id == answer.id))
    if proof is None or proof.review_status != "pending_review":
        raise ValueError("Pending skill evidence is required")
    if db.scalar(select(V2ReviewRetryTask.id).where(
        V2ReviewRetryTask.lesson_response_id == answer.id,
        V2ReviewRetryTask.status.in_(("requested", "submitted")))):
        raise ValueError("Resolve the existing manual retry first")
    newer = db.scalar(select(LessonQuestionResponse.id).where(
        LessonQuestionResponse.lesson_session_id == session.id,
        LessonQuestionResponse.id > answer.id).limit(1))
    if newer is not None:
        raise ValueError("A later answer exists; refusing to roll it back")
    release = get_pinned_release(db, session.content_release_id)
    lesson = next(q for q in release["lessons"] if q["id"] == session.lesson_id)
    ids = lesson["practice_question_ids" if answer.role == "guided_practice" else "check_question_ids"]
    index = ids.index(answer.question_id)
    job = db.scalar(select(V2ReadingJob).where(
        V2ReadingJob.lesson_response_id == answer.id, V2ReadingJob.is_current.is_(True)))
    if job is not None:
        if job.status == "retry_audio" and session.stage == answer.role and session.step_index == index:
            return {"status": "already_reopened", "job_id": job.id}
        raise ValueError("Reading is already owned by the native engine")
    audio = db.scalar(select(AudioSubmission).where(
        AudioSubmission.lesson_response_id == answer.id,
        AudioSubmission.status == "pending_review").order_by(AudioSubmission.id.desc()).limit(1))
    if audio is None:
        raise ValueError("No pending audio is available")
    result = {"status": "dry_run", "lesson_id": session.lesson_id,
              "question_id": answer.question_id, "stage": answer.role, "step_index": index}
    if not apply:
        return result
    job = enqueue_pinned_reading(db, student_id=student_id, audio_submission_id=audio.id,
        content_release_id=session.content_release_id, question_id=answer.question_id)
    # Explicit owner-requested replacement, never an invented score or provider decision.
    job.status = "retry_audio"
    job.last_error_code = "owner_requested_rerecord"
    session.status = "in_progress"
    session.stage = answer.role
    session.step_index = index
    session.return_to = None
    session.version += 1
    audio.status = "rerecord_required"
    db.add(AuditLog(actor_role="system", actor_id=0, action="v2_owner_reopen_pending_reading",
        entity_type="reading_job", entity_id=str(job.id),
        details="Owner requested last pending reading replacement; grades and completed lessons preserved"))
    db.flush()
    return {**result, "status": "reopened", "job_id": job.id}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--student-id", type=int, required=True)
    parser.add_argument("--expected-name", required=True)
    parser.add_argument("--expected-lesson", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    with SessionLocal.begin() as db:
        result = recover(db, args.student_id, args.expected_name, args.expected_lesson, args.apply)
    print("READING_RECOVERY " + json.dumps(result, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
