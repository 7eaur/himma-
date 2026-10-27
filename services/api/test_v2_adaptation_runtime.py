from uuid import uuid4

import pytest

from conftest import TestingSessionLocal
from db.learning_models import (
    AdaptationDecision,
    LessonSession,
    PrivateContentBankSnapshot,
    SkillEvidence,
    StudentJourney,
    SupportAssignment,
)
from db.models import Student
from v2_adaptation_policy import (
    POLICY_VERSION,
    EvidenceSignal,
    PolicyDecision,
    evaluate_independent,
    evaluate_support,
    resolve_focus,
)
from v2_adaptation_runtime import _complete_lesson, _open_support
from v2_content.compiler import compile_release
from v2_content.importer import register_candidate_release
from v2_content.repository import get_question
from test_v2_lesson_runtime import _place_fixture


def _start_at_independent(student_client, lesson_id="L1-01"):
    _place_fixture(level=int(lesson_id[1]), cursor=lesson_id)
    started = student_client.post(f"/v2/lessons/{lesson_id}/start")
    assert started.status_code == 200, started.text
    session_id = started.json()["session"]["session_id"]
    with TestingSessionLocal() as db:
        session = db.query(LessonSession).filter(LessonSession.id == session_id).one()
        session.stage = "independent_check"
        session.step_index = 0
        db.commit()
    return session_id


def _submit_current(student_client, session_id, *, correct):
    current = student_client.get(f"/v2/lessons/sessions/{session_id}/interaction")
    assert current.status_code == 200, current.text
    question_id = current.json()["interaction"]["question"]["question_id"]
    question = get_question(question_id)
    expected = list(question["private_answer"]["correct_option_ids"])
    option_ids = [row["id"] for row in question["options"]]
    if correct:
        selected = expected
    elif question["interaction"] in {"sequence", "build_word"}:
        selected = list(reversed(expected))
    else:
        selected = [next(value for value in option_ids if value not in expected)]
    response = student_client.post(
        f"/v2/lessons/sessions/{session_id}/answers",
        json={"submit_key": str(uuid4()), "selected_option_ids": selected},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _complete_current_stage(student_client, session_id, correctness):
    result = None
    for correct in correctness:
        result = _submit_current(student_client, session_id, correct=correct)
    return result


def _signal(number, *, correct, review="graded", question="q"):
    return EvidenceSignal(
        evidence_id=number,
        question_id=question,
        lesson_id="L1-01",
        skill_group="S1",
        evidence_type="letter_to_sound",
        error_focus="sound_mapping",
        is_correct=correct,
        review_status=review,
    )


def test_policy_is_versioned_and_does_not_reuse_v1_score_thresholds():
    assert POLICY_VERSION.startswith("himma-v2-adaptation/")
    source = __import__("inspect").getsource(__import__("v2_adaptation_policy"))
    assert "0.7" not in source
    assert "0.8" not in source
    assert "0.85" not in source


def test_policy_distinguishes_stable_single_repeated_pending_and_unmapped():
    question = get_question("L1-01-IC-A01")
    questions = {question["id"]: question}
    assert evaluate_independent([_signal(1, correct=True, question=question["id"])], questions).kind == "next_lesson"
    single = evaluate_independent([_signal(1, correct=False, question=question["id"])], questions)
    assert (single.kind, single.support_id, single.focus) == ("additional_check", "SUP-01", "sound_mapping")
    repeated = evaluate_independent([
        _signal(1, correct=False, question=question["id"]),
        _signal(2, correct=False, question=question["id"]),
    ], questions)
    assert repeated.kind == "targeted_support"
    assert evaluate_independent([_signal(1, correct=None, review="pending_review", question=question["id"])], questions).kind == "waiting_review"

    unmapped = get_question("L1-03-IC-A04")
    held = evaluate_independent([EvidenceSignal(
        evidence_id=3,
        question_id=unmapped["id"],
        lesson_id="L1-03",
        skill_group="S2",
        evidence_type=unmapped["evidence_type"],
        error_focus=unmapped["error_focus"],
        is_correct=False,
        review_status="graded",
    )], {unmapped["id"]: unmapped})
    assert held.kind == "supervisor_hold"
    assert held.reason_code == "authoring_focus_mapping_missing"


def test_all_independent_questions_have_one_mapping_or_the_declared_hold():
    questions = [row for row in compile_release()["questions"] if row["role"] == "independent_check"]
    missing = [row["id"] for row in questions if resolve_focus(row) is None]
    assert missing == ["L1-03-IC-A04"]


def test_clean_independent_check_advances_once_and_read_status_is_pure(student_client):
    session_id = _start_at_independent(student_client)
    result = _complete_current_stage(student_client, session_id, [True, True, True, True])
    assert result["lesson"]["session"]["stage"] == "outcome"
    with TestingSessionLocal() as db:
        session = db.query(LessonSession).filter(LessonSession.id == session_id).one()
        journey = db.query(StudentJourney).filter(StudentJourney.student_id == session.student_id).one()
        assert journey.current_lesson_id == "L1-02"
        assert db.query(SkillEvidence).filter(SkillEvidence.counts_for_mastery.is_(True)).count() == 4
        before = db.query(AdaptationDecision).count()
    first = student_client.get(f"/v2/adaptation/sessions/{session_id}/status")
    second = student_client.get(f"/v2/adaptation/sessions/{session_id}/status")
    assert first.status_code == second.status_code == 200
    with TestingSessionLocal() as db:
        assert db.query(AdaptationDecision).count() == before


def test_completion_follows_pinned_lesson_order_when_current_bank_changes(student_client, monkeypatch):
    session_id = _start_at_independent(student_client)
    import v2_adaptation_runtime as adaptation
    import v2_content.repository as repository
    original = repository.get_release()
    monkeypatch.setattr(adaptation, "get_release", lambda: {
        **original, "lessons": list(reversed(original["lessons"])), "version": "future-release",
    }, raising=False)
    with TestingSessionLocal() as db:
        session = db.get(LessonSession, session_id)
        _complete_lesson(db, session)
        journey = db.query(StudentJourney).filter_by(student_id=session.student_id).one()
        assert journey.current_lesson_id == "L1-02"
        assert journey.content_release_id == session.content_release_id
        db.commit()


def test_completion_refuses_missing_pinned_bank_without_advancing(student_client):
    session_id = _start_at_independent(student_client)
    with TestingSessionLocal() as db:
        session = db.get(LessonSession, session_id)
        snapshot = db.get(PrivateContentBankSnapshot, session.content_release_id)
        snapshot.checksum = "f" * 64
        db.flush()
        with pytest.raises(RuntimeError, match="pinned lesson bank unavailable"):
            _complete_lesson(db, session)
        journey = db.query(StudentJourney).filter_by(student_id=session.student_id).one()
        assert journey.current_lesson_id == "L1-01"
        assert session.status != "completed"


def test_one_gap_gets_two_alternate_checks_then_returns_to_next_lesson(student_client):
    session_id = _start_at_independent(student_client)
    result = _complete_current_stage(student_client, session_id, [False, True, True, True])
    assert result["lesson"]["session"]["stage"] == "additional_check"
    assert result["lesson"]["adaptation"]["support"]["support_id"] == "SUP-01"
    assert result["lesson"]["adaptation"]["support"]["focus"] == "sound_mapping"
    result = _complete_current_stage(student_client, session_id, [True, True])
    assert result["lesson"]["session"]["stage"] == "outcome"
    with TestingSessionLocal() as db:
        assignment = db.query(SupportAssignment).one()
        assert assignment.status == "resolved"
        assert assignment.return_to["lesson_id"] == "L1-01"
        assert db.query(StudentJourney).one().current_lesson_id == "L1-02"


def test_repeated_gap_opens_targeted_practice_and_failed_check_escalates_once(student_client):
    session_id = _start_at_independent(student_client)
    result = _complete_current_stage(student_client, session_id, [False, False, True, True])
    assert result["lesson"]["session"]["stage"] == "support_practice"
    practice_total = result["lesson"]["interaction"]["progress"]["total"]
    result = _complete_current_stage(student_client, session_id, [True] * practice_total)
    assert result["lesson"]["session"]["stage"] == "support_check"
    result = _complete_current_stage(student_client, session_id, [False, True])
    assert result["lesson"]["session"]["stage"] == "supervisor_hold"
    assert result["lesson"]["adaptation"]["state"] == "supervisor_hold"
    with TestingSessionLocal() as db:
        assignment = db.query(SupportAssignment).one()
        assert assignment.status == "escalated"
        assert db.query(AdaptationDecision).count() == 2


def test_additional_check_failure_expands_to_support_without_second_assignment(student_client):
    session_id = _start_at_independent(student_client)
    _complete_current_stage(student_client, session_id, [False, True, True, True])
    result = _complete_current_stage(student_client, session_id, [False, True])
    assert result["lesson"]["session"]["stage"] == "support_practice"
    with TestingSessionLocal() as db:
        assert db.query(SupportAssignment).count() == 1
        assignment = db.query(SupportAssignment).one()
        assert assignment.mode == "targeted_support"
        assert assignment.verification_round == 1


def test_support_policy_is_bounded_and_pending_is_neutral():
    assert evaluate_support([_signal(1, correct=True)], was_additional_check=False).kind == "next_lesson"
    assert evaluate_support([_signal(1, correct=False)], was_additional_check=False).kind == "supervisor_hold"
    assert evaluate_support([_signal(1, correct=False)], was_additional_check=True).kind == "targeted_support"
    assert evaluate_support([_signal(1, correct=None, review="pending_review")], was_additional_check=False).kind == "waiting_review"


def test_lower_level_support_does_not_demote_current_journey():
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        student.current_level = 2
        journey = StudentJourney(
            student_id=student.id,
            content_release_id=release.id,
            current_level=2,
            current_lesson_id="L2-01",
            placement_state="placed",
        )
        session = LessonSession(
            student_id=student.id,
            content_release_id=release.id,
            lesson_id="L2-01",
            stage="independent_check",
        )
        db.add_all([journey, session])
        db.flush()
        assignment = _open_support(db, session, PolicyDecision(
            kind="targeted_support",
            reason_code="test_prior_level_gap",
            evidence_ids=(),
            support_id="SUP-01",
            focus="sound_mapping",
        ))
        assert assignment.source_level == 2
        assert assignment.support_level == 1
        assert journey.current_level == 2
