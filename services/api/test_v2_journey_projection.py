"""Regression for bounded cohort reads and the shared journey policy."""
from sqlalchemy import event

from conftest import TestingSessionLocal, engine
from db.learning_models import (
    AssessmentQuestionResponse, LessonQuestionResponse, LessonSession,
    PlacementDecisionV2, StudentJourney, V2ReviewRetryTask,
)
from db.models import AssessmentRetakeAuthorization, AssessmentSession, Student, User
from v2_content.importer import register_candidate_release
from v2_journey_projection import JourneyFacts, load_journey_facts, next_action
from v2_student_readmodel import build_student_v2_home, supervisor_v2_cohort_overview


def _cohort(db, limit):
    return supervisor_v2_cohort_overview(limit=limit, offset=0, search="", status="all", _supervisor=None, db=db)


def test_cohort_query_count_is_bounded_for_1_30_50_students_and_omits_private_banks():
    with TestingSessionLocal() as db:
        release = register_candidate_release(db)
        original = db.query(Student).one()
        students = [original] + [Student(name=f"Synthetic learner {i}", access_code=f"PROJ{i:03}") for i in range(49)]
        db.add_all(students[1:]); db.flush()
        for student in students:
            db.add(StudentJourney(student_id=student.id, content_release_id=release.id,
                                  placement_state="in_progress", current_level=1))
            # Long unofficial history must not be materialized by the page.
            db.add_all([AssessmentSession(
                student_id=student.id, content_release_id=release.id, session_type="pretest",
                status="completed", v2_state="completed", official_for_reporting=False,
                final_score=99, assessment_attempt_no=attempt,
            ) for attempt in range(1, 5)])
        db.commit()
    counts = []
    for limit in (1, 30, 50):
        sql, loaded = [], []
        def capture(_conn, _cursor, statement, _params, _context, _many):
            if statement.lstrip().upper().startswith("SELECT"):
                sql.append(statement)
        def materialized(_session, row):
            if isinstance(row, AssessmentSession):
                loaded.append(row.id)
        event.listen(engine, "before_cursor_execute", capture)
        try:
            with TestingSessionLocal() as db:
                event.listen(db, "loaded_as_persistent", materialized)
                result = _cohort(db, limit)
        finally:
            event.remove(engine, "before_cursor_execute", capture)
        assert len(result["items"]) == limit
        assert all(row["current_action"]["action"] == "start_pretest" for row in result["items"])
        assert all(row["progress"]["display_percent"] is None for row in result["items"])
        assert loaded == []  # None of the 200 unofficial attempts is a preferred record.
        assert not any("answer_json" in statement or "replacement_json" in statement for statement in sql)
        assert not any("private_content_bank_snapshots.payload_json AS" in statement for statement in sql)
        assert all("access_code" not in row for row in result["items"])
        counts.append(len(sql))
    assert len(set(counts)) == 1, counts
    assert max(counts) <= 13, counts  # Bounded page reads, not one readmodel per row.


def test_mixed_cohort_preserves_official_scores_retries_pinned_progress_and_retake_ownership():
    with TestingSessionLocal() as db:
        release = register_candidate_release(db)
        reviewer = db.query(User).one()
        fresh = db.query(Student).one()
        fresh.name = "fresh"
        learning = Student(name="learning", access_code="PROJ-L", current_level=3)
        assessment_retry = Student(name="assessment retry", access_code="PROJ-A")
        legacy = Student(name="legacy", access_code="PROJ-V1")
        retake = Student(name="retake", access_code="PROJ-RE")
        inconsistent = Student(name="inconsistent", access_code="PROJ-BAD")
        ready = Student(name="ready", access_code="PROJ-POST")
        db.add_all([learning, assessment_retry, legacy, retake, inconsistent, ready]); db.flush()
        placed = StudentJourney(student_id=learning.id, content_release_id=release.id,
                                placement_state="placed", current_level=2, current_lesson_id="L2-02")
        db.add_all([placed, StudentJourney(student_id=inconsistent.id, content_release_id=release.id,
                    placement_state="placed", current_level=2),
                    StudentJourney(student_id=ready.id, content_release_id=release.id,
                    placement_state="posttest_ready", current_level=3)])
        official = AssessmentSession(student_id=learning.id, content_release_id=release.id,
            session_type="pretest", status="completed", v2_state="completed",
            official_for_reporting=True, final_score=70, assigned_level=2)
        pending = AssessmentSession(student_id=assessment_retry.id, content_release_id=release.id,
            session_type="pretest", status="in_progress", v2_state="waiting_review")
        legacy_pre = AssessmentSession(student_id=legacy.id, session_type="pretest", status="completed")
        retake_pre = AssessmentSession(student_id=retake.id, session_type="pretest", status="completed")
        db.add_all([official, pending, legacy_pre, retake_pre]); db.flush()
        db.add(PlacementDecisionV2(student_id=learning.id, assessment_session_id=official.id,
            content_release_id=release.id, assigned_level=2, reason="Synthetic official placement",
            policy_version="test"))
        # A later, unapproved high score cannot replace the official 70%.
        db.add(AssessmentSession(student_id=learning.id, content_release_id=release.id,
            session_type="pretest", status="completed", v2_state="completed",
            official_for_reporting=False, final_score=99, assessment_attempt_no=2))
        db.add_all([LessonSession(student_id=learning.id, content_release_id=release.id,
                                 lesson_id="L2-01", status="completed", stage="complete") for _ in range(2)])
        lesson = LessonSession(student_id=learning.id, content_release_id=release.id,
                               lesson_id="L2-02", status="waiting_review", stage="waiting_review")
        db.add(lesson); db.flush()
        lesson_response = LessonQuestionResponse(lesson_session_id=lesson.id, question_id="synthetic-lesson",
            role="independent_check", answer_json={"answer":"private-answer"},
            submit_key="synthetic-lesson-key", status="pending_review")
        assessment_response = AssessmentQuestionResponse(assessment_session_id=pending.id,
            question_id="synthetic-pretest", role="pretest", skill_group="S1", evidence_type="reading",
            answer_json={"audio_storage_key":"private-audio"}, submit_key="synthetic-assessment-key", status="pending_review")
        db.add_all([lesson_response, assessment_response]); db.flush()
        lesson_task = V2ReviewRetryTask(student_id=learning.id, requested_by=reviewer.id,
            lesson_response_id=lesson_response.id, request_kind="rerecord", status="requested", reason="Synthetic retry")
        db.add_all([lesson_task, V2ReviewRetryTask(student_id=assessment_retry.id, requested_by=reviewer.id,
            assessment_response_id=assessment_response.id, request_kind="rerecord", status="requested", reason="Synthetic retry")])
        db.add(AssessmentRetakeAuthorization(student_id=retake.id, session_type="pretest",
            previous_session_id=retake_pre.id, status="pending", reason="Synthetic retake", authorized_by=reviewer.id))
        # A malformed reference to another learner must not enable a retake.
        db.add(AssessmentRetakeAuthorization(student_id=legacy.id, session_type="pretest",
            previous_session_id=retake_pre.id, status="pending", reason="Wrong owner", authorized_by=reviewer.id))
        db.commit()
        learning_id, task_id = learning.id, lesson_task.id
    with TestingSessionLocal() as db:
        students = db.query(Student).order_by(Student.id.desc()).all()
        statements = []
        def capture(_conn, _cursor, statement, _params, _context, _many):
            if statement.lstrip().upper().startswith("SELECT"):
                statements.append(statement)
        event.listen(engine, "before_cursor_execute", capture)
        try:
            data = _cohort(db, 50)
        finally:
            event.remove(engine, "before_cursor_execute", capture)
        assert len(statements) <= 13, len(statements)
        by_name = {row["full_name"]: row for row in data["items"]}
        expected = {"fresh":"start_pretest", "learning":"rerecord_required",
                    "assessment retry":"rerecord_required", "legacy":"migration_review",
                    "retake":"start_pretest", "inconsistent":"placement_review", "ready":"start_posttest"}
        assert {name: row["current_action"]["action"] for name, row in by_name.items()} == expected
        assert by_name["learning"]["current_action"]["href"] == f"/student/retry/{task_id}"
        assert by_name["learning"]["progress"]["completed_lessons"] == 1
        assert by_name["learning"]["journey"]["current_level"] == 2  # Never Student.current_level.
        assert by_name["learning"]["progress"]["pending_review"] == 1
        for student in students:
            single = build_student_v2_home(db, student, include_rewards=False)
            assert single["current_action"] == by_name[student.name]["current_action"]
            assert single["progress"] == by_name[student.name]["progress"]
        single = build_student_v2_home(db, db.get(Student, learning_id), include_rewards=False)
        assert single["assessments"]["pretest"]["score_percent"] == 70
        assert "private-answer" not in str(data) and "private-audio" not in str(data)
        db.get(V2ReviewRetryTask, task_id).status = "submitted"; db.commit()
        facts = load_journey_facts(db, [learning_id])[learning_id]
        assert next_action(facts)["action"] == "lesson"


def test_retry_linkage_cannot_target_another_students_session():
    import pytest
    from fastapi import HTTPException
    from v2_journey_projection import JourneyFacts
    facts = JourneyFacts(student_id=1, retry={"task_id":7, "kind":"lesson", "status":"pending_review",
                                            "session_id":12, "owner_id":2})
    with pytest.raises(HTTPException) as failure:
        next_action(facts)
    assert failure.value.status_code == 409


def test_loaded_retry_with_foreign_response_is_rejected_before_returning_a_link():
    import pytest
    from fastapi import HTTPException
    with TestingSessionLocal() as db:
        owner = db.query(Student).one()
        other = Student(name="Other synthetic account", access_code="PROJ-OTHER")
        db.add(other); db.flush()
        release = register_candidate_release(db)
        session = AssessmentSession(student_id=other.id, content_release_id=release.id,
                                    session_type="pretest", status="in_progress", v2_state="waiting_review")
        db.add(session); db.flush()
        response = AssessmentQuestionResponse(assessment_session_id=session.id, question_id="synthetic-cross-owner",
            role="pretest", skill_group="S1", evidence_type="reading", answer_json={},
            submit_key="cross-owner-key", status="pending_review")
        db.add(response); db.flush()
        db.add(V2ReviewRetryTask(student_id=owner.id, requested_by=db.query(User).one().id,
            assessment_response_id=response.id, request_kind="rerecord", status="requested", reason="Synthetic malformed task"))
        db.commit()
        owner_id = owner.id
    with TestingSessionLocal() as db:
        facts = load_journey_facts(db, [owner_id])[owner_id]
        with pytest.raises(HTTPException) as failure:
            next_action(facts)
        assert failure.value.status_code == 409

def test_completed_journey_offers_no_dead_end_next_action():
    """A learner who finished the posttest must not be routed into an empty lesson map."""
    journey = StudentJourney(student_id=51, content_release_id=17,
                             placement_state="completed", current_level=3)
    facts = JourneyFacts(student_id=51, journey=journey)
    action = next_action(facts)
    assert action == {"action": "complete", "href": None, "label": "اكتملت الرحلة"}
