"""Continue an official V2 lesson or assessment after ONE native voice grade.

Called by academic_apply within its locked database transaction. Never
creates a second review decision or trusts a browser-supplied score.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.learning_models import AssessmentQuestionResponse, LessonQuestionResponse, LessonSession, SkillEvidence
from db.models import AssessmentSession
from .job_store import ReadingConflict


def continue_native_academic_journey(
    db: Session,
    response: AssessmentQuestionResponse | LessonQuestionResponse,
    session: AssessmentSession | LessonSession,
) -> None:
    if isinstance(session, AssessmentSession):
        from v2_assessment_runtime import _current, _finish_if_ready
        if not isinstance(response, AssessmentQuestionResponse):
            raise ReadingConflict("Assessment response type mismatch")
        if session.v2_state != "answering" or session.status != "in_progress":
            raise ReadingConflict("Assessment no longer accepts this reading")
        if _current(db, session)["id"] != response.question_id:
            raise ReadingConflict("Assessment answer is not the active question")
        session.v2_question_index += 1
        _finish_if_ready(db, session)
        return

    if not isinstance(session, LessonSession) or not isinstance(response, LessonQuestionResponse):
        raise ReadingConflict("Unexpected reading academic context")
    from v2_interaction_runtime import _advance, _current_question, _question_ids
    from v2_adaptation_runtime import active_support_assignment
    from v2_rewards import reconcile_rewards
    if session.status != "in_progress":
        raise ReadingConflict("Lesson is not active")
    if _current_question(db, session)["id"] != response.question_id:
        raise ReadingConflict("Reading answer is no longer the current step")
    assignment = active_support_assignment(db, session.id)
    if (response.support_assignment_id or None) != (assignment.id if assignment else None):
        raise ReadingConflict("Reading support assignment changed during analysis")

    guided = session.stage in {"guided_practice", "support_practice"}
    if guided and response.is_correct is False:
        response.hint_used = True
        evidence = db.scalar(select(SkillEvidence).where(
            SkillEvidence.response_id == response.id).with_for_update())
        if evidence is None:
            raise ReadingConflict("Missing V2 skill evidence")
        evidence.hint_used = True
        # Approved support has a bounded worked-example path after three
        # inaccurate academic *attempts*. Unrecognized audio is not an attempt.
        if session.stage != "support_practice" or response.attempt_no < 3:
            reconcile_rewards(db, session.student_id, lesson_session_id=session.id)
            return

    _advance(
        session, len(_question_ids(db, session)),
        db=db, assignment=assignment,
    )
    reconcile_rewards(db, session.student_id, lesson_session_id=session.id)
