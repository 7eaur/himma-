from uuid import uuid4

import pytest

from conftest import TestingSessionLocal
from db.learning_models import (
    AdaptationDecision,
    LessonQuestionResponse,
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
from v2_adaptation_runtime import _complete_lesson, _open_support, finish_support_check, student_adaptation_payload
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
    assert held.kind == "additional_check"
    assert (held.support_id, held.focus) == ("SUP-02", "kasra")


def test_all_independent_questions_have_one_mapping_or_the_declared_hold():
    questions = [row for row in compile_release()["questions"] if row["role"] == "independent_check"]
    missing = [row["id"] for row in questions if resolve_focus(row) is None]
    assert missing == []


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


def test_repeated_gap_opens_targeted_practice_and_failed_check_continues_without_false_mastery(student_client):
    session_id = _start_at_independent(student_client)
    result = _complete_current_stage(student_client, session_id, [False, False, True, True])
    assert result["lesson"]["session"]["stage"] == "support_practice"
    practice_total = result["lesson"]["interaction"]["progress"]["total"]
    result = _complete_current_stage(student_client, session_id, [True] * practice_total)
    assert result["lesson"]["session"]["stage"] == "support_check"
    result = _complete_current_stage(student_client, session_id, [False, True])
    assert result["lesson"]["session"]["stage"] == "outcome"
    assert result["lesson"]["adaptation"]["mastery_demonstrated"] is False
    assert "تقوية هذه المهارة" in result["lesson"]["adaptation"]["message"]
    with TestingSessionLocal() as db:
        assignment = db.query(SupportAssignment).one()
        assert assignment.status == "resolved"  # detour ended; mastery was NOT claimed
        decisions = db.query(AdaptationDecision).order_by(AdaptationDecision.id).all()
        assert len(decisions) == 2
        assert decisions[-1].reason_code == "support_gap_unresolved_continue_without_mastery"
        assert decisions[-1].explanation_json["skill_mastery"] == "not_demonstrated"
        assert db.query(StudentJourney).one().current_lesson_id == "L1-02"
    from v2_rewards import rewards_projection
    from db.v2_reward_models import V2RewardGrant
    with TestingSessionLocal() as db:
        assert not db.query(V2RewardGrant).filter(V2RewardGrant.milestone == "lesson_complete").first()


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
    result = evaluate_support([_signal(1, correct=False)], was_additional_check=False)
    assert result.kind == "next_lesson"
    assert result.reason_code == "support_gap_unresolved_continue_without_mastery"
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


def test_different_independent_focus_gaps_are_checked_automatically_in_sequence(student_client):
    # L1-03 assesses damma, kasra, fatha, kasra. Two distinct failed
    # focuses must not be collapsed into only the first selected detour.
    session_id = _start_at_independent(student_client, "L1-03")
    first = _complete_current_stage(student_client, session_id, [False, False, True, True])
    assert first["lesson"]["session"]["stage"] == "additional_check"
    assert first["lesson"]["adaptation"]["support"]["focus"] == "damma"
    next_focus = _complete_current_stage(student_client, session_id, [True, True])
    assert next_focus["lesson"]["session"]["stage"] == "additional_check"
    assert next_focus["lesson"]["adaptation"]["support"]["focus"] == "kasra"
    completed = _complete_current_stage(student_client, session_id, [True, True])
    assert completed["lesson"]["session"]["stage"] == "outcome"
    with TestingSessionLocal() as db:
        assignments = db.query(SupportAssignment).order_by(SupportAssignment.id).all()
        assert [(a.focus, a.status) for a in assignments] == [
            ("damma", "resolved"), ("kasra", "resolved")]
        assert db.query(StudentJourney).one().current_lesson_id == "L1-04"


def _synthetic_support_evidence(db, session, assignment, question_id, *, pending=False, correct=True):
    """Isolated DB evidence: never generate student audio or touch production data."""
    from v2_content.repository import get_pinned_release
    question = next(row for row in get_pinned_release(db, session.content_release_id)["questions"] if row["id"] == question_id)
    response = LessonQuestionResponse(
        lesson_session_id=session.id, question_id=question_id, role=question["role"],
        answer_json={"synthetic_test_evidence": True}, submit_key=str(uuid4()),
        attempt_no=1, status="pending_review" if pending else "graded",
        is_correct=None if pending else correct,
        support_assignment_id=assignment.id, hint_used=False,
    )
    db.add(response)
    db.flush()
    evidence = SkillEvidence(
        response_id=response.id, lesson_session_id=session.id, student_id=session.student_id,
        content_release_id=session.content_release_id, support_assignment_id=assignment.id,
        question_id=question_id, source_kind="support", role=question["role"],
        skill_group=question["skill_group"], evidence_type=question["evidence_type"],
        review_status=response.status, is_correct=response.is_correct,
        hint_used=False, counts_for_mastery=not pending and question["role"] == "support_check",
        policy_version=POLICY_VERSION,
    )
    db.add(evidence)
    db.flush()
    return response, evidence


def test_empty_or_partial_support_evidence_cannot_autopass(student_client):
    from fastapi import HTTPException
    with pytest.raises(ValueError, match="without any evidence"):
        evaluate_independent([], {})
    with pytest.raises(ValueError, match="without any evidence"):
        evaluate_support([], was_additional_check=False)
    session_id = _start_at_independent(student_client, lesson_id="L1-04")
    with TestingSessionLocal() as db:
        session = db.get(LessonSession, session_id)
        assignment = _open_support(db, session, PolicyDecision(
            kind="targeted_support", reason_code="synthetic", evidence_ids=(),
            support_id="SUP-03", focus="syllable_reading",
        ))
        session.stage = "support_check"
        with pytest.raises(HTTPException) as err:
            finish_support_check(db, session, assignment)
        assert err.value.status_code == 409
        assert session.status == "in_progress"


def test_pending_support_practice_reading_blocks_promotion_until_review(student_client):
    session_id = _start_at_independent(student_client, lesson_id="L1-04")
    with TestingSessionLocal() as db:
        session = db.get(LessonSession, session_id)
        assignment = _open_support(db, session, PolicyDecision(
            kind="targeted_support", reason_code="synthetic", evidence_ids=(),
            support_id="SUP-03", focus="syllable_reading",
        ))
        session.stage = "support_check"
        for question_id in assignment.check_question_ids:
            _synthetic_support_evidence(db, session, assignment, question_id, correct=True)
        original, proof = _synthetic_support_evidence(
            db, session, assignment, assignment.practice_question_ids[0], pending=True
        )
        decision = finish_support_check(db, session, assignment)
        assert decision.decision_kind == "waiting_review"
        assert session.stage == session.status == "waiting_review"
        assert db.query(StudentJourney).one().current_lesson_id == "L1-04"
        assignment_id, proof_id, response_id = assignment.id, proof.id, original.id
        db.commit()
    with TestingSessionLocal() as db:
        session = db.get(LessonSession, session_id)
        assignment = db.get(SupportAssignment, assignment_id)
        proof = db.get(SkillEvidence, proof_id)
        original = db.get(LessonQuestionResponse, response_id)
        original.status = proof.review_status = "graded"
        original.is_correct = proof.is_correct = True
        # Match the supervisor review endpoint, which flushes before querying pending evidence.
        # Test sessions intentionally disable autoflush.
        db.flush()
        resumed = finish_support_check(db, session, assignment, decision_key="support:after-reviewed-reading")
        assert resumed.decision_kind == "next_lesson"
        assert session.stage == "complete" and session.status == "completed"
        assert db.query(StudentJourney).one().current_lesson_id == "L1-05"


def test_reviewed_additional_check_failure_restores_active_support_session(student_client):
    session_id = _start_at_independent(student_client, lesson_id="L1-04")
    with TestingSessionLocal() as db:
        session = db.get(LessonSession, session_id)
        assignment = _open_support(db, session, PolicyDecision(
            kind="additional_check", reason_code="synthetic", evidence_ids=(),
            support_id="SUP-03", focus="syllable_reading",
        ))
        session.stage = "additional_check"
        pending, proof = _synthetic_support_evidence(
            db, session, assignment, assignment.check_question_ids[0], pending=True
        )
        _synthetic_support_evidence(db, session, assignment, assignment.check_question_ids[1], correct=False)
        first = finish_support_check(db, session, assignment)
        assert first.decision_kind == "waiting_review"
        assert session.status == "waiting_review"
        assignment_id, response_id, proof_id = assignment.id, pending.id, proof.id
        db.commit()
    with TestingSessionLocal() as db:
        session = db.get(LessonSession, session_id)
        assignment = db.get(SupportAssignment, assignment_id)
        pending = db.get(LessonQuestionResponse, response_id)
        proof = db.get(SkillEvidence, proof_id)
        pending.status = proof.review_status = "graded"
        pending.is_correct = proof.is_correct = False
        # Persist the reviewed evidence in this transaction before checking the SQL status filter.
        db.flush()
        resumed = finish_support_check(db, session, assignment, decision_key="support:reviewed:check")
        assert resumed.decision_kind == "targeted_support"
        assert session.stage == "support_practice" and session.status == "in_progress"
        assert assignment.mode == "targeted_support" and assignment.status == "active"
        assert session.step_index == 0


def test_support_practice_wrong_answers_do_not_skip_check_or_change_level(student_client):
    session_id = _start_at_independent(student_client)
    result = _complete_current_stage(student_client, session_id, [False, False, True, True])
    assert result["lesson"]["session"]["stage"] == "support_practice"
    for attempt in range(3):
        wrong = _submit_current(student_client, session_id, correct=False)
        assert wrong["submission"]["retry_required"] is True
        assert wrong["lesson"]["session"]["stage"] == "support_practice"
        assert wrong["lesson"]["interaction"]["progress"]["index"] == 1
    accepted = _submit_current(student_client, session_id, correct=True)
    assert accepted["submission"]["retry_required"] is False
    assert accepted["lesson"]["interaction"]["progress"]["index"] == 2
    with TestingSessionLocal() as db:
        assert db.query(StudentJourney).one().current_level == 1


def test_outcome_reports_unresolved_earlier_focus_even_if_later_focus_passes(student_client):
    """The final decision alone cannot erase an earlier failed support focus."""
    session_id = _start_at_independent(student_client)
    with TestingSessionLocal() as db:
        session = db.get(LessonSession, session_id)
        session.stage, session.status = "complete", "completed"
        for key, reason in (
            ("first-focus", "support_gap_unresolved_continue_without_mastery"),
            ("second-focus", "support_check_resolved_gap"),
        ):
            db.add(AdaptationDecision(
                lesson_session_id=session.id, student_id=session.student_id,
                content_release_id=session.content_release_id, decision_key=key,
                decision_kind="next_lesson", reason_code=reason,
                evidence_ids=[], explanation_json={}, policy_version=POLICY_VERSION,
            ))
        db.flush()
        view = student_adaptation_payload(db, session)
        assert view["state"] == "next_lesson"
        assert view["mastery_demonstrated"] is False
        assert "سنواصل تقوية هذه المهارة" in view["message"]
