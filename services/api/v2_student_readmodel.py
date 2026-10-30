"""P09.1-B: read-only V2 learner source of truth (never V1 rewards/activities).

A projection of existing immutable V2 content, journey, sessions and evidence.
No GET creates journeys, awards stars, changes placement, or reads private answers.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.learning_models import AdaptationDecision, AssessmentQuestionResponse, LessonQuestionResponse, LessonSession, PlacementDecisionV2, PrivateContentBankSnapshot, StudentJourney, SupportAssignment, V2ReviewRetryTask
from db.models import AssessmentSession, Attempt, ContentRelease, Student, User
from dependencies import get_current_user, get_db
from v2_journey_projection import JourneyFacts, load_journey_facts, next_action
from v2_lesson_runtime import _require_preview_student
from v2_content.repository import get_release
from v2_rewards import rewards_projection

router = APIRouter(prefix="/v2/student", tags=["v2-student-home"])


def _initial_level(journey: StudentJourney, lessons: list[dict], placement_level: int | None, completed_ids: set[str]) -> int:
    if placement_level is not None:
        return placement_level
    # Historical preview journeys may predate placement decisions. Completed
    # lower-level lessons remain learned evidence, never placement skips.
    return min([journey.current_level] + [int(row["level"][1]) for row in lessons if row["id"] in completed_ids])


def _placement_level(db: Session, journey: StudentJourney, lessons: list[dict]) -> int:
    decision = db.query(PlacementDecisionV2).filter(
        PlacementDecisionV2.student_id == journey.student_id,
        PlacementDecisionV2.content_release_id == journey.content_release_id,
    ).order_by(PlacementDecisionV2.id.desc()).first()
    if decision:
        return _initial_level(journey, lessons, decision.assigned_level, set())
    completed = {lesson_id for lesson_id, in db.query(LessonSession.lesson_id).filter(
        LessonSession.student_id == journey.student_id,
        LessonSession.content_release_id == journey.content_release_id,
        LessonSession.status == "completed",
    ).distinct().all()}
    return _initial_level(journey, lessons, None, completed)


def _load_release_lessons(db: Session, release_ids: set[int]) -> dict[int, tuple[list[dict] | None, str | None]]:
    """Fetch lesson metadata once per page, without loading private question banks."""
    if not release_ids:
        return {}
    rows = db.query(
        ContentRelease.id, ContentRelease.version, ContentRelease.checksum,
        PrivateContentBankSnapshot.payload_json["lessons"].label("lessons"),
    ).outerjoin(PrivateContentBankSnapshot, (
        (PrivateContentBankSnapshot.content_release_id == ContentRelease.id) &
        (PrivateContentBankSnapshot.checksum == ContentRelease.checksum)
    )).filter(ContentRelease.id.in_(release_ids)).all()
    result = {}
    for row in rows:
        lessons = row.lessons
        if not isinstance(lessons, list):
            current = get_release()
            lessons = current["lessons"] if current["version"] == row.version and current["checksum"] == row.checksum else None
        result[row.id] = (lessons, row.version)
    return result


def _release_lessons(db: Session, release_id: int) -> tuple[list[dict] | None, str | None]:
    return _load_release_lessons(db, {release_id}).get(release_id, (None, None))


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


def _projection_release_id(facts: JourneyFacts) -> int | None:
    if facts.journey:
        return facts.journey.content_release_id
    if facts.active_lesson:
        return facts.active_lesson.content_release_id
    # Preserve the home summary's pretest-first selection if corrupt data has
    # more than one active kind; next_action still chooses the latest attempt.
    for kind in ("pretest", "posttest"):
        row = facts.assessments.get(kind)
        if row and row.status == "in_progress":
            return row.content_release_id
    return None


def build_student_v2_home(
    db: Session, student: Student, *, include_rewards: bool = True,
    facts: JourneyFacts | None = None,
    releases: dict[int, tuple[list[dict] | None, str | None]] | None = None,
) -> dict:
    """One authorized projection, using request-scoped batch facts for staff lists."""
    if facts is None:
        facts = load_journey_facts(db, [student.id])[student.id]
    if facts.student_id != student.id:
        raise ValueError("student projection facts belong to a different account")
    journey, active_lesson = facts.journey, facts.active_lesson
    active_assessment = facts.active_assessment
    by_kind = {kind: _assessment_summary(facts.assessments.get(kind)) for kind in ("pretest", "posttest")}
    # All student-facing accounts now use a single V2 shell. Historical V1
    # evidence remains in its own tables; current_action blocks unsafe retakes.
    mode = "v2"
    version = None
    lessons = None
    release_id = _projection_release_id(facts)
    if release_id is not None:
        if releases is None:
            releases = _load_release_lessons(db, {release_id})
        lessons, version = releases.get(release_id, (None, None))

    levels = []
    progress = {
        "completed_lessons": 0,
        "assigned_lessons": None,
        "skipped_by_placement": 0,
        "pending_review": facts.pending_review_count,
        "display_percent": None,
    }
    if journey and lessons is not None:
        placed = journey.placement_state in {"placed", "posttest_ready", "completed"}
        initial_level = _initial_level(journey, lessons, facts.placement_level, facts.completed_ids)
        skipped_ids = {
            row["id"] for row in lessons
            if placed and int(row["level"][1]) < initial_level
        }
        assigned_ids = {row["id"] for row in lessons} - skipped_ids
        completed_ids = facts.completed_ids
        done = len(completed_ids & assigned_ids)
        progress = {
            "completed_lessons": done,
            "assigned_lessons": len(assigned_ids),
            "skipped_by_placement": len(skipped_ids),
            "pending_review": progress["pending_review"],
            "display_percent": round(done / len(assigned_ids) * 100, 1) if placed and assigned_ids else None,
        }
        if placed:
            for level in sorted({int(row["level"][1]) for row in lessons}):
                ids = {row["id"] for row in lessons if int(row["level"][1]) == level}
                assigned = ids & assigned_ids
                completed = len(assigned & completed_ids)
                state = ("skipped" if not assigned else "completed" if completed == len(assigned)
                         else "current" if level == journey.current_level else "locked")
                levels.append({"level": level, "state": state, "assigned_lessons": len(assigned),
                               "completed_lessons": completed,
                               "display_percent": round(completed / len(assigned) * 100, 1) if assigned else None})

    # A first-time learner starts V2 from an explicit POST. GET never enrolls,
    # duplicates a pretest, or changes any historical V1 records.
    action = next_action(facts)
    return {
        "mode": mode,
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
        "levels": levels,
        "assessments": by_kind,
        **({"rewards": rewards_projection(db, student.id, journey.content_release_id if journey else None)}
           if include_rewards else {}),
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
    initial_level = _placement_level(db, journey, lessons)
    items = []
    for lesson in lessons:
        lesson_id = lesson["id"]
        current = latest_by_lesson.get(lesson_id)
        skipped = placed and int(lesson["level"][1]) < initial_level
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
    # Staff-only, bounded academic timeline. These are automatic policy events,
    # not invitations for supervisors to edit a learner's placement or support.
    release_id = (db.query(StudentJourney.content_release_id).filter(
        StudentJourney.student_id == student.id,
    ).scalar())
    adaptation_rows = []
    support_rows = []
    if release_id is not None:
        decisions = db.query(AdaptationDecision).filter(
            AdaptationDecision.student_id == student.id,
            AdaptationDecision.content_release_id == release_id,
        ).order_by(AdaptationDecision.id.desc()).limit(30).all()
        adaptation_rows = [{
            "id": row.id,
            "kind": row.decision_kind,
            "reason_code": row.reason_code,
            "policy_version": row.policy_version,
            "unmastered_gap": row.reason_code == "support_gap_unresolved_continue_without_mastery",
            "created_at": row.created_at,
        } for row in decisions]
        supports = db.query(SupportAssignment).filter(
            SupportAssignment.student_id == student.id,
            SupportAssignment.content_release_id == release_id,
        ).order_by(SupportAssignment.id.desc()).limit(30).all()
        # The academic follow-up is keyed to the persisted, immutable failed
        # check decision, not assignment.status (resolved means activity ended).
        # Keep this read-only; no holding the child and no fabricated mastery.
        followup_ids = {
            assignment_id for assignment_id, in db.query(AdaptationDecision.support_assignment_id).filter(
                AdaptationDecision.student_id == student.id,
                AdaptationDecision.content_release_id == release_id,
                AdaptationDecision.reason_code == "support_gap_unresolved_continue_without_mastery",
                AdaptationDecision.support_assignment_id.is_not(None),
            ).all()
        }
        support_rows = [{
            "id": row.id,
            "lesson_id": row.source_lesson_id,
            "target_skill": row.target_skill,
            "focus": row.focus,
            "mode": row.mode,
            "status": row.status,
            "needs_followup": row.id in followup_ids,
            "created_at": row.created_at,
        } for row in supports]
    return {
        **home,
        "lesson_overview": _supervisor_lesson_overview(db, student),
        "onboarding_review": history,
        "adaptation_decisions": adaptation_rows,
        "support_assignments": support_rows,
    }

def _staff_home_batch(db: Session, students: list[Student]) -> dict[int, dict]:
    facts = load_journey_facts(db, [student.id for student in students])
    releases = _load_release_lessons(db, {
        release_id for item in facts.values()
        if (release_id := _projection_release_id(item)) is not None
    })
    return {
        student.id: build_student_v2_home(db, student, include_rewards=False,
                                        facts=facts[student.id], releases=releases)
        for student in students
    }


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
    homes = _staff_home_batch(db, students)
    items = []
    for student in students:
        state = homes[student.id]
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


@router.get("/admin/overview")
def supervisor_v2_dashboard(
    _supervisor: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """V2 operational counts across the cohort, independent of list pagination."""
    def journeys(state: str) -> int:
        return db.query(StudentJourney.id).filter(StudentJourney.placement_state == state).count()

    recent = []
    students = db.query(Student).order_by(Student.id.desc()).limit(6).all()
    homes = _staff_home_batch(db, students)
    for student in students:
        home = homes[student.id]
        recent.append({
            "id": student.id, "full_name": student.name,
            "status": "active" if student.is_active else "inactive",
            "journey": home["journey"], "current_action": home["current_action"],
            "progress": home["progress"], "data_status": home["data_status"],
        })
    # An unanswered rerecord request is work for the learner, not an
    # actionable reading review for the supervisor. Match V2 notifications.
    requested_assessment_ids = db.query(V2ReviewRetryTask.assessment_response_id).filter(
        V2ReviewRetryTask.status == "requested",
        V2ReviewRetryTask.assessment_response_id.is_not(None),
    )
    requested_lesson_ids = db.query(V2ReviewRetryTask.lesson_response_id).filter(
        V2ReviewRetryTask.status == "requested",
        V2ReviewRetryTask.lesson_response_id.is_not(None),
    )
    return {
        "source": "himma_v2_readmodel",
        "counts": {
            "students": db.query(Student.id).count(),
            "active_accounts": db.query(Student.id).filter(Student.is_active.is_(True)).count(),
            "learning": journeys("placed"),
            "ready_for_posttest": journeys("posttest_ready"),
            "completed": journeys("completed"),
            "assessment_reviews": db.query(AssessmentQuestionResponse.id).join(
                AssessmentSession, AssessmentSession.id == AssessmentQuestionResponse.assessment_session_id,
            ).join(Student, Student.id == AssessmentSession.student_id).filter(
                AssessmentQuestionResponse.status == "pending_review",
                AssessmentSession.v2_state.is_not(None),
                Student.is_active.is_(True),
                ~AssessmentQuestionResponse.id.in_(requested_assessment_ids),
            ).count(),
            "lesson_reviews": db.query(LessonQuestionResponse.id).join(
                LessonSession, LessonSession.id == LessonQuestionResponse.lesson_session_id,
            ).join(Student, Student.id == LessonSession.student_id).filter(
                LessonQuestionResponse.status == "pending_review",
                Student.is_active.is_(True),
                ~LessonQuestionResponse.id.in_(requested_lesson_ids),
            ).count(),
            "placements": db.query(AssessmentSession.id).filter(
                AssessmentSession.session_type == "pretest", AssessmentSession.v2_state == "placement_pending_review",
            ).count(),
        },
        "recent_students": recent,
    }
