"""P09.1-B: read-only V2 learner source of truth (never V1 rewards/activities).

A projection of existing immutable V2 content, journey, sessions and evidence.
No GET creates journeys, awards stars, changes placement, or reads private answers.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.learning_models import LessonSession, PrivateContentBankSnapshot, StudentJourney
from db.models import AssessmentSession, ContentRelease, Student, User
from dependencies import get_current_user, get_db
from v2_assessment_runtime import current_action
from v2_lesson_runtime import _require_preview_student
from v2_content.repository import get_release

router = APIRouter(prefix="/v2/student", tags=["v2-student-home"])


def _release_lessons(db: Session, release_id: int) -> tuple[list[dict] | None, str | None]:
    row = db.query(ContentRelease).filter(ContentRelease.id == release_id).one_or_none()
    if row is None:
        return None, None
    pinned = db.query(PrivateContentBankSnapshot).filter(
        PrivateContentBankSnapshot.content_release_id == release_id,
        PrivateContentBankSnapshot.checksum == row.checksum,
    ).one_or_none()
    if pinned and isinstance(pinned.payload_json, dict):
        lessons = pinned.payload_json.get("lessons")
        if isinstance(lessons, list):
            return lessons, row.version
    # The only permitted fallback is the *same* compiled release checksum.
    # Never silently measure an old student's progress against a newer bank.
    current = get_release()
    if current["version"] == row.version and current["checksum"] == row.checksum:
        return current["lessons"], row.version
    return None, row.version


def _assessment_summary(session: AssessmentSession | None) -> dict | None:
    if session is None:
        return None
    approved = session.status == "completed" and bool(session.official_for_reporting)
    return {
        "state": session.v2_state,
        "session_id": session.id,
        "official": approved,
        "score_percent": float(session.final_score) if approved and session.final_score is not None else None,
    }


def build_student_v2_home(db: Session, student: Student) -> dict:
    """One authorized student projection; safe for learner use and reuse by staff."""
    journey = db.query(StudentJourney).filter(StudentJourney.student_id == student.id).one_or_none()
    assessments = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.v2_state.is_not(None),
        AssessmentSession.session_type.in_(("pretest", "posttest")),
    ).order_by(AssessmentSession.started_at.desc(), AssessmentSession.id.desc()).all()
    active_assessment = next((x for x in assessments if x.status == "in_progress"), None)
    # The latest active attempt is shown, otherwise only official attempts.
    by_kind = {}
    for kind in ("pretest", "posttest"):
        best = next((x for x in assessments if x.session_type == kind and x.status == "in_progress"), None)
        if best is None:
            best = next((x for x in assessments if x.session_type == kind and x.official_for_reporting), None)
        by_kind[kind] = _assessment_summary(best)

    active_lesson = db.query(LessonSession).filter(
        LessonSession.student_id == student.id,
        LessonSession.status.in_(("in_progress", "waiting_review")),
    ).one_or_none()
    # All student-facing accounts now use a single V2 shell. Historical V1
    # evidence remains in its own tables; current_action blocks unsafe retakes.
    mode = "v2"
    version = None
    lessons = None
    if journey:
        lessons, version = _release_lessons(db, journey.content_release_id)
    elif active_lesson:
        lessons, version = _release_lessons(db, active_lesson.content_release_id)
    elif active_assessment and active_assessment.content_release_id:
        lessons, version = _release_lessons(db, active_assessment.content_release_id)

    progress = {
        "completed_lessons": 0,
        "assigned_lessons": None,
        "skipped_by_placement": 0,
        "pending_review": int(bool(active_lesson and active_lesson.status == "waiting_review")),
        "display_percent": None,
    }
    if journey and lessons is not None:
        placed = journey.placement_state in {"placed", "posttest_ready", "completed"}
        skipped_ids = {
            row["id"] for row in lessons
            if placed and int(row["level"][1]) < journey.current_level
        }
        assigned_ids = {row["id"] for row in lessons} - skipped_ids
        completed_ids = {
            row.lesson_id for row in db.query(LessonSession).filter(
                LessonSession.student_id == student.id,
                LessonSession.content_release_id == journey.content_release_id,
                LessonSession.status == "completed",
            ).all()
        }
        done = len(completed_ids & assigned_ids)
        progress = {
            "completed_lessons": done,
            "assigned_lessons": len(assigned_ids),
            "skipped_by_placement": len(skipped_ids),
            "pending_review": progress["pending_review"],
            "display_percent": round(done / len(assigned_ids) * 100, 1) if placed and assigned_ids else None,
        }

    # A first-time learner starts V2 from an explicit POST. GET never enrolls,
    # duplicates a pretest, or changes any historical V1 records.
    action = current_action(student=student, db=db)
    return {
        "mode": mode,
        "test_only": True,
        "student": {"id": student.id, "full_name": student.name, "grade_level": student.grade_level},
        "current_action": action,
        "journey": ({
            "placement_state": journey.placement_state,
            "current_level": journey.current_level,
            "current_lesson_id": journey.current_lesson_id,
            "status": journey.status,
            "content_release_version": version,
        } if journey else None),
        "progress": progress,
        "assessments": by_kind,
        "rewards": {"state": "not_implemented_v2"},
        "data_status": "partial" if (journey or active_assessment or active_lesson) and lessons is None else "ready",
    }


@router.get("/home")
def student_v2_home(
    student: Student = Depends(_require_preview_student),
    db: Session = Depends(get_db),
):
    return build_student_v2_home(db, student)


@router.get("/admin/students/{student_id}/home")
def supervisor_student_v2_home(
    student_id: int,
    _supervisor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).one_or_none()
    if student is None:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")
    # Staff-only projection deliberately returns no access code or audio keys.
    return build_student_v2_home(db, student)
