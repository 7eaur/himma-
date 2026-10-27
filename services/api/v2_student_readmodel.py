"""P09.1-B: read-only V2 learner source of truth (never V1 rewards/activities).

A projection of existing immutable V2 content, journey, sessions and evidence.
No GET creates journeys, awards stars, changes placement, or reads private answers.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.learning_models import LessonSession, PrivateContentBankSnapshot, StudentJourney
from db.models import AssessmentSession, Attempt, ContentRelease, Student, User
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


def _preferred_assessment(
    db: Session, student_id: int, kind: str,
) -> AssessmentSession | None:
    """Select one active attempt, otherwise one official attempt, without loading history."""
    base = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student_id,
        AssessmentSession.v2_state.is_not(None),
        AssessmentSession.session_type == kind,
    )
    active = base.filter(AssessmentSession.status == "in_progress").order_by(
        AssessmentSession.started_at.desc(), AssessmentSession.id.desc(),
    ).first()
    if active is not None:
        return active
    return base.filter(AssessmentSession.official_for_reporting.is_(True)).order_by(
        AssessmentSession.started_at.desc(), AssessmentSession.id.desc(),
    ).first()


def build_student_v2_home(db: Session, student: Student) -> dict:
    """One authorized student projection; safe for learner use and reuse by staff."""
    journey = db.query(StudentJourney).filter(StudentJourney.student_id == student.id).one_or_none()
    # The latest active attempt is shown, otherwise only the latest official
    # attempt. Each query returns at most one row, regardless of history size.
    selected_assessments = {
        kind: _preferred_assessment(db, student.id, kind)
        for kind in ("pretest", "posttest")
    }
    active_assessment = next(
        (row for row in selected_assessments.values() if row and row.status == "in_progress"),
        None,
    )
    by_kind = {
        kind: _assessment_summary(row)
        for kind, row in selected_assessments.items()
    }

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


def _supervisor_lesson_overview(db: Session, student: Student) -> dict:
    """Staff-only timeline from the student's pinned release; never include answer keys."""
    journey = db.query(StudentJourney).filter(StudentJourney.student_id == student.id).one_or_none()
    if journey is None:
        return {"state": "awaiting_journey", "items": [], "content_release_version": None}
    lessons, version = _release_lessons(db, journey.content_release_id)
    if lessons is None:
        return {"state": "unavailable", "items": [], "content_release_version": version}

    session_filter = (
        LessonSession.student_id == student.id,
        LessonSession.content_release_id == journey.content_release_id,
    )
    latest_ids = db.query(
        LessonSession.lesson_id,
        func.max(LessonSession.id).label("latest_id"),
    ).filter(*session_filter).group_by(LessonSession.lesson_id).subquery()
    latest_by_lesson = {
        row.lesson_id: row for row in db.query(LessonSession).join(
            latest_ids, LessonSession.id == latest_ids.c.latest_id,
        ).all()
    }
    completed_ids = {
        lesson_id for lesson_id, in db.query(LessonSession.lesson_id).filter(
            *session_filter, LessonSession.status == "completed",
        ).distinct().all()
    }
    placed = journey.placement_state in {"placed", "posttest_ready", "completed"}
    items = []
    for lesson in lessons:
        lesson_id = lesson["id"]
        current = latest_by_lesson.get(lesson_id)
        skipped = placed and int(lesson["level"][1]) < journey.current_level
        # Match the aggregate official count: completed attempts win over
        # unfinished retries, and placement skips never count as completion.
        if skipped:
            state = "skipped"
        elif lesson_id in completed_ids:
            state = "completed"
        elif current and current.status == "waiting_review":
            state = "waiting_review"
        elif current and current.status == "in_progress":
            state = "in_progress"
        elif lesson_id == journey.current_lesson_id and placed:
            state = "current"
        else:
            state = "not_started"
        items.append({
            "lesson_id": lesson_id,
            "title": lesson["title"],
            "level": lesson["level"],
            "state": state,
            "session_id": current.id if current and state in {"waiting_review", "in_progress"} else None,
        })
    return {"state": "ready", "content_release_version": version, "items": items}


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
    # Staff-only projection deliberately returns no access code, audio keys or answer keys.
    home = build_student_v2_home(db, student)
    history = []
    if home["current_action"]["action"] == "migration_review":
        # Explain the actual blocker to staff without credentials, answer keys,
        # or recording URLs. Presence of a session is not evidence of completion.
        for session in db.query(AssessmentSession).filter(
            AssessmentSession.student_id == student.id,
        ).order_by(AssessmentSession.id.desc()).all():
            history.append({
                "session_id": session.id,
                "kind": session.session_type,
                "status": session.status,
                "version": "v2" if session.v2_state is not None else "v1",
                "saved_attempts": db.query(Attempt.id).filter(Attempt.session_id == session.id).count(),
                "official": bool(session.official_for_reporting),
            })
    return {**home, "lesson_overview": _supervisor_lesson_overview(db, student),
            "onboarding_review": history}

@router.get("/admin/students/overview")
def supervisor_v2_cohort_overview(
    limit: int = Query(default=30, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    search: str = Query(default="", max_length=100),
    status: str = Query(default="all", pattern="^(all|active|inactive)$"),
    _supervisor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Staff-only, paginated, V2-only student list. Never returns login codes or V1 activity counts."""
    query = db.query(Student)
    if search.strip():
        # Search names only, not learner credentials.
        query = query.filter(Student.name.ilike(f"%{search.strip()}%"))
    if status == "active":
        query = query.filter(Student.is_active.is_(True))
    elif status == "inactive":
        query = query.filter(Student.is_active.is_(False))
    total = query.count()
    students = query.order_by(Student.id.desc()).offset(offset).limit(limit).all()
    items = []
    for student in students:
        state = build_student_v2_home(db, student)
        items.append({
            "id": student.id,
            "full_name": student.name,
            "grade_level": student.grade_level,
            "created_at": student.created_at,
            "status": "active" if student.is_active else "inactive",
            "current_action": state["current_action"],
            "journey": state["journey"],
            "progress": state["progress"],
            "data_status": state["data_status"],
        })
    return {
        "source": "himma_v2_readmodel",
        "total": total, "offset": offset, "limit": limit, "items": items,
    }
