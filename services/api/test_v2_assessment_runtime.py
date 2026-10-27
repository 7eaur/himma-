from uuid import uuid4

import pytest
from pydantic import ValidationError

from conftest import TestingSessionLocal
from db.learning_models import AssessmentQuestionResponse, PlacementDecisionV2, StudentJourney, PrivateContentBankSnapshot
from db.models import AssessmentSession, Attempt, AudioSubmission, AuditLog, ContentItem, Skill, Student
from assessment_retake import mark_official_completed_attempt
from v2_content.contracts import PRIVATE_KEYS
from v2_content.repository import get_question, get_release
from v2_content.importer import register_candidate_release
from test_v2_legacy_writing_fixture import legacy_writing_release
from v2_assessment_runtime import PlacementRequest, ReviewRequest, _recommended_level
from v2_lesson_review import LessonDecision
from v2_retry_runtime import RetryRequest


def _ack_assessment_audio(client, response_id: int) -> int:
    item = next(
        row for row in client.get("/v2/assessments/admin/review-queue").json()["items"]
        if row["response_id"] == response_id
    )
    audio_id = item["audio_submission_id"]
    assert audio_id is not None
    acknowledged = client.post(
        f"/v2/assessments/admin/responses/{response_id}/audio-completed",
        json={"audio_submission_id": audio_id},
    )
    assert acknowledged.status_code == 200, acknowledged.text
    return audio_id


def test_review_models_strip_edges_and_reject_whitespace_only():
    cases = (
        (ReviewRequest, "note", "قرار واضح"),
        (LessonDecision, "note", "قرار واضح"),
        (PlacementRequest, "reason", "سبب تربوي واضح"),
        (RetryRequest, "reason", "سبب إعادة واضح"),
    )
    for model, field, value in cases:
        payload = {field: f"  {value}  "}
        if model in (ReviewRequest, LessonDecision):
            payload["is_correct"] = True
        if model is PlacementRequest:
            payload["assigned_level"] = 1
        assert getattr(model(**payload), field) == value
        with pytest.raises(ValidationError):
            model(**{**payload, field: " " * 20})


def _all_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_keys(child)


def test_assessment_bank_is_parallel_distinct_30_plus_30():
    release = get_release()
    pre = [q for q in release["questions"] if q["role"] == "pretest"]
    post = [q for q in release["questions"] if q["role"] == "posttest"]
    assert len(pre) == len(post) == 30
    assert {q["id"] for q in pre}.isdisjoint({q["id"] for q in post})
    assert {q["skill_group"] for q in pre} == {q["skill_group"] for q in post}


def test_pretest_starts_resumes_and_never_leaks_private_answer(student_client):
    started = student_client.post("/v2/assessments/pretest/start")
    assert started.status_code == 200
    payload = started.json()
    assert payload["session"]["progress"] == {"answered": 0, "total": 30}
    assert payload["interaction"]["progress"]["stage"] == "pretest"
    assert PRIVATE_KEYS.isdisjoint(set(_all_keys(payload)))
    resumed = student_client.post("/v2/assessments/pretest/start")
    assert resumed.status_code == 200
    assert resumed.json()["session"]["session_id"] == payload["session"]["session_id"]
    restored = student_client.get(f'/v2/assessments/sessions/{payload["session"]["session_id"]}')
    assert restored.status_code == 200
    assert restored.json()["interaction"]["question"]["question_id"] == payload["interaction"]["question"]["question_id"]


def test_objective_answer_is_private_idempotent_and_advances(student_client):
    payload = student_client.post("/v2/assessments/pretest/start").json()
    session_id = payload["session"]["session_id"]
    question = get_question(payload["interaction"]["question"]["question_id"])
    key = str(uuid4())
    response = student_client.post(f"/v2/assessments/sessions/{session_id}/answers", json={"submit_key": key, "selected_option_ids": question["private_answer"]["correct_option_ids"]})
    assert response.status_code == 200
    assert "correct" not in response.json()["submission"]
    assert response.json()["assessment"]["session"]["progress"]["answered"] == 1
    replay = student_client.post(f"/v2/assessments/sessions/{session_id}/answers", json={"submit_key": key, "selected_option_ids": question["private_answer"]["correct_option_ids"]})
    assert replay.status_code == 200
    assert replay.json()["status"] == "replayed"
    with TestingSessionLocal() as db:
        assert db.query(AssessmentQuestionResponse).one().is_correct is True


def test_student_cannot_open_or_answer_another_students_v2_session(student_client):
    """Ownership is checked before reading an answer or replaying an accepted key."""
    first = student_client.post("/v2/assessments/pretest/start")
    assert first.status_code == 200
    first_id = first.json()["session"]["session_id"]
    question = get_question(first.json()["interaction"]["question"]["question_id"])
    answer = {
        "submit_key": str(uuid4()),
        "selected_option_ids": [question["options"][0]["id"]],
    }
    first_url = f"/v2/assessments/sessions/{first_id}"
    saved = student_client.post(f"{first_url}/answers", json=answer)
    assert saved.status_code == 200
    assert saved.json()["assessment"]["session"]["progress"]["answered"] == 1

    with TestingSessionLocal() as db:
        db.add(Student(access_code="STU002", name="طالب تجريبي آخر", current_level=1))
        db.commit()

    second_login = student_client.post("/auth/student-login", json={"access_code": "STU002"})
    assert second_login.status_code == 200
    hidden = student_client.get(first_url)
    missing = student_client.get("/v2/assessments/sessions/999999999")
    assert hidden.status_code == missing.status_code == 404
    assert hidden.json() == missing.json()
    assert "private_answer" not in hidden.text
    # Even a valid answer and the owner's already-accepted idempotency key
    # must not reveal a replay, response state or private assessment data.
    rejected = student_client.post(f"{first_url}/answers", json=answer)
    unknown = student_client.post(
        "/v2/assessments/sessions/999999999/answers", json=answer,
    )
    assert rejected.status_code == unknown.status_code == 404
    assert rejected.json() == unknown.json()
    second = student_client.post("/v2/assessments/pretest/start")
    assert second.status_code == 200
    assert second.json()["session"]["session_id"] != first_id

    assert student_client.post("/auth/student-login", json={"access_code": "STU001"}).status_code == 200
    restored = student_client.get(first_url)
    assert restored.status_code == 200
    assert restored.json()["session"]["progress"]["answered"] == 1
    replay = student_client.post(f"{first_url}/answers", json=answer)
    assert replay.status_code == 200
    assert replay.json()["status"] == "replayed"
    with TestingSessionLocal() as db:
        assert db.query(AssessmentQuestionResponse).filter(
            AssessmentQuestionResponse.assessment_session_id == first_id,
        ).count() == 1
        assert db.query(AssessmentQuestionResponse).count() == 1


def test_v2_session_endpoints_hide_legacy_v1_attempts(student_client):
    """A known V1 session id must be indistinguishable from a missing V2 id."""
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        legacy = AssessmentSession(
            student_id=student.id, session_type="pretest", status="in_progress",
            assessment_attempt_no=1,
        )
        db.add(legacy)
        db.commit()
        legacy_id = legacy.id

    legacy_url = f"/v2/assessments/sessions/{legacy_id}"
    missing_url = "/v2/assessments/sessions/999999999"
    for suffix, method, payload in (
        ("", "get", None),
        ("/answers", "post", {"submit_key": str(uuid4()), "selected_option_ids": ["synthetic"]}),
    ):
        response = getattr(student_client, method)(
            f"{legacy_url}{suffix}", **({"json": payload} if payload else {}),
        )
        missing = getattr(student_client, method)(
            f"{missing_url}{suffix}", **({"json": payload} if payload else {}),
        )
        assert response.status_code == missing.status_code == 404
        assert response.json() == missing.json()
    with TestingSessionLocal() as db:
        assert db.query(AssessmentQuestionResponse).count() == 0


def test_voice_review_completion_automatically_places_student_without_staff_decision(researcher_client, monkeypatch):
    import storage
    monkeypatch.setattr(storage, "verify_audio", lambda *args, **kwargs: None)
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(student_id=student.id, content_release_id=release.id, placement_state="in_progress", current_level=1))
        session = AssessmentSession(student_id=student.id, content_release_id=release.id, session_type="pretest", status="in_progress", v2_state="waiting_review", v2_question_index=30, v2_policy_version="test", assessment_attempt_no=1)
        db.add(session); db.flush()
        questions = [q for q in get_release()["questions"] if q["role"] == "pretest"]
        for q in questions:
            response = AssessmentQuestionResponse(
                assessment_session_id=session.id, question_id=q["id"], role="pretest", answer_json={"audio_storage_key": f"audio/{student.id}/test.webm"} if q["interaction"] == "read_aloud" else {"test": True},
                submit_key=str(uuid4()), status="pending_review" if q["interaction"] == "read_aloud" else "graded",
                is_correct=None if q["interaction"] == "read_aloud" else True,
                skill_group=q["skill_group"], evidence_type=q["evidence_type"],
            )
            db.add(response)
            db.flush()
            if q["interaction"] == "read_aloud":
                db.add(AudioSubmission(assessment_response_id=response.id, storage_key=f"audio/{student.id}/test.webm", file_size=2048, mime_type="audio/webm", status="pending_review"))
        db.commit()
        pending_ids = [r.id for r in db.query(AssessmentQuestionResponse).filter(AssessmentQuestionResponse.status == "pending_review").all()]
        session_id = session.id
    # Same TestClient cookie is now researcher after the researcher fixture logs in.
    for response_id in pending_ids:
        _ack_assessment_audio(researcher_client, response_id)
        reviewed = researcher_client.post(f"/v2/assessments/admin/responses/{response_id}/review", json={"is_correct": True, "note": "مراجعة بشرية واضحة"})
        assert reviewed.status_code == 200
    with TestingSessionLocal() as db:
        session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).one()
        journey = db.query(StudentJourney).one()
        assert session.v2_state == "completed"
        assert session.assigned_level == 3 and session.official_for_reporting is True
        assert journey.current_level == 3 and journey.current_lesson_id.startswith("L3-")
        decision = db.query(PlacementDecisionV2).one()
        assert decision.decided_by is None and decision.assigned_level == 3
        assert decision.policy_version.endswith("threshold-50-80-v1")
        audit = db.query(AuditLog).filter(AuditLog.action == "v2_automatic_placement").one()
        assert audit.actor_role == "system" and "recommended=3" in audit.details
    duplicate = researcher_client.post(f"/v2/assessments/admin/sessions/{session_id}/placement",
        json={"assigned_level": 1, "reason": "محاولة تجاوز القرار التلقائي المعتمد"})
    assert duplicate.status_code == 409


def test_staff_cannot_choose_a_level_before_autonomous_reconciliation(researcher_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(student_id=student.id, content_release_id=release.id,
                              placement_state="in_progress", current_level=1))
        session = AssessmentSession(student_id=student.id, content_release_id=release.id,
            session_type="pretest", status="in_progress",
            v2_state="placement_pending_review", v2_question_index=30,
            assessment_attempt_no=1)
        db.add(session)
        db.commit()
        session_id = session.id
    forbidden = researcher_client.post(
        f"/v2/assessments/admin/sessions/{session_id}/placement",
        json={"assigned_level": 3, "reason": "التسكين القديم اليدوي غير مسموح"},
    )
    assert forbidden.status_code == 409
    with TestingSessionLocal() as db:
        assert db.query(PlacementDecisionV2).count() == 0
        assert db.query(StudentJourney).one().placement_state == "in_progress"


def test_legacy_ready_pretest_reconciles_to_system_placement_once(student_client, monkeypatch):
    import storage
    monkeypatch.setattr(storage, "verify_audio", lambda *args, **kwargs: None)
    """Persisted review queue is recovered with no researcher actor or retake."""
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(student_id=student.id, content_release_id=release.id,
                              current_level=1, placement_state="in_progress"))
        session = AssessmentSession(
            student_id=student.id, content_release_id=release.id, session_type="pretest",
            status="in_progress", v2_state="placement_pending_review", v2_question_index=30,
            assessment_attempt_no=1, v2_policy_version="older-human-placement",
        )
        db.add(session); db.flush()
        for question in (q for q in get_release()["questions"] if q["role"] == "pretest"):
            answer = AssessmentQuestionResponse(
                assessment_session_id=session.id, question_id=question["id"],
                role="pretest", answer_json={"synthetic": True}, submit_key=str(uuid4()),
                status="graded", is_correct=True, skill_group=question["skill_group"],
                evidence_type=question["evidence_type"],
            )
            db.add(answer); db.flush()
            if question["interaction"] == "read_aloud":
                db.add(AudioSubmission(
                    assessment_response_id=answer.id,
                    storage_key=f"synthetic/{student.id}/{question['id']}.webm",
                    file_size=2048, mime_type="audio/webm", status="graded",
                ))
        session_id = session.id
        db.commit()
    response = student_client.post(f"/v2/assessments/sessions/{session_id}/finalize-placement")
    assert response.status_code == 200, response.text
    assert response.json()["session"]["state"] == "completed"
    replay = student_client.post(f"/v2/assessments/sessions/{session_id}/finalize-placement")
    assert replay.status_code == 200
    with TestingSessionLocal() as db:
        assert db.query(PlacementDecisionV2).count() == 1
        assert db.query(PlacementDecisionV2).one().decided_by is None
        assert db.query(AssessmentSession).one().official_for_reporting is True
        assert db.query(StudentJourney).one().current_level == 3


def test_pretest_recovery_rejects_missing_graded_audio_even_when_all_flags_are_graded(student_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(student_id=student.id, content_release_id=release.id,
                              placement_state="in_progress", current_level=1))
        session = AssessmentSession(student_id=student.id, content_release_id=release.id,
            session_type="pretest", status="in_progress", v2_state="placement_pending_review",
            v2_question_index=30, assessment_attempt_no=1)
        db.add(session); db.flush()
        for question in (q for q in get_release()["questions"] if q["role"] == "pretest"):
            db.add(AssessmentQuestionResponse(
                assessment_session_id=session.id, question_id=question["id"],
                role="pretest", answer_json={"synthetic": True}, submit_key=str(uuid4()),
                status="graded", is_correct=True, skill_group=question["skill_group"],
                evidence_type=question["evidence_type"],
            ))
        session_id = session.id
        db.commit()
    result = student_client.post(f"/v2/assessments/sessions/{session_id}/finalize-placement")
    assert result.status_code == 409
    with TestingSessionLocal() as db:
        assert db.query(PlacementDecisionV2).count() == 0
        assert db.query(StudentJourney).one().placement_state == "in_progress"


def test_pretest_reconciliation_rejects_unreviewed_voice_without_placement(student_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(student_id=student.id, content_release_id=release.id, placement_state="in_progress"))
        session = AssessmentSession(student_id=student.id, content_release_id=release.id,
            session_type="pretest", status="in_progress", v2_state="placement_pending_review",
            v2_question_index=30, assessment_attempt_no=1)
        db.add(session); db.flush()
        for index, question in enumerate(q for q in get_release()["questions"] if q["role"] == "pretest"):
            pending = index == 0
            db.add(AssessmentQuestionResponse(
                assessment_session_id=session.id, question_id=question["id"], role="pretest",
                answer_json={"synthetic": True}, submit_key=str(uuid4()),
                status="pending_review" if pending else "graded",
                is_correct=None if pending else True, skill_group=question["skill_group"],
                evidence_type=question["evidence_type"],
            ))
        session_id = session.id
        db.commit()
    result = student_client.post(f"/v2/assessments/sessions/{session_id}/finalize-placement")
    assert result.status_code == 409
    with TestingSessionLocal() as db:
        assert db.query(PlacementDecisionV2).count() == 0
        assert db.query(StudentJourney).one().placement_state == "in_progress"


def test_reports_use_null_for_missing_and_student_cannot_open_admin(student_client):
    assert student_client.get("/v2/assessments/admin/reports/summary").status_code == 403
    assert student_client.get("/v2/assessments/current-action").json()["action"] == "start_pretest"


def test_posttest_gate_requires_ready_journey_and_explicit_enable(student_client):
    blocked = student_client.post("/v2/assessments/posttest/start")
    assert blocked.status_code == 409


def test_v2_admin_queues_reject_student(student_client):
    assert student_client.get("/v2/assessments/admin/review-queue").status_code == 403
    assert student_client.get("/v2/assessments/admin/placement-queue").status_code == 403


def test_archived_writing_queue_is_pinned_and_private(researcher_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        old_release = legacy_writing_release("V2-PRE-Q12")
        release = register_candidate_release(db, old_release)
        session = AssessmentSession(student_id=student.id, content_release_id=release.id,
            session_type="pretest", status="in_progress", v2_state="waiting_review", v2_question_index=30)
        db.add(session); db.flush()
        q = next(q for q in old_release["questions"] if q["id"] == "V2-PRE-Q12")
        response = AssessmentQuestionResponse(
            assessment_session_id=session.id, question_id=q["id"], role="pretest",
            answer_json={"text_response": "كتابة الطالب"},
            submit_key=str(uuid4()), status="pending_review", is_correct=None,
            skill_group=q["skill_group"], evidence_type=q["evidence_type"],
        )
        db.add(response); db.commit()
        response_id = response.id
    queue = researcher_client.get("/v2/assessments/admin/review-queue").json()
    item = next(item for item in queue["items"] if item["response_id"] == response_id)
    assert item["evidence_ready"] is True
    assert item["text_response"] == "كتابة الطالب"
    assert item["prompt"] and item["rubric"]
    assert "audio_storage_key" not in str(item)
    assert researcher_client.get(f"/v2/assessments/admin/responses/{response_id}/audio").status_code == 404
    assert researcher_client.get("/v2/assessments/admin/review-queue?limit=101").status_code == 422


def test_review_refuses_missing_actual_student_evidence(researcher_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        session = AssessmentSession(student_id=student.id, content_release_id=release.id, session_type="pretest", status="in_progress", v2_state="waiting_review", v2_question_index=30)
        db.add(session); db.flush()
        q = next(q for q in get_release()["questions"] if q["role"] == "pretest" and q["interaction"] == "read_aloud")
        response = AssessmentQuestionResponse(assessment_session_id=session.id, question_id=q["id"], role="pretest", answer_json={"audio_storage_key": "audio/999/missing.webm"},
            submit_key=str(uuid4()), status="pending_review", is_correct=None, skill_group=q["skill_group"], evidence_type=q["evidence_type"])
        db.add(response); db.commit()
        response_id = response.id
    denied = researcher_client.post(f"/v2/assessments/admin/responses/{response_id}/review", json={"is_correct": True, "note": "لا يوجد تسجيل"})
    assert denied.status_code == 409


def test_pinned_assessment_snapshot_survives_candidate_bank_rotation(student_client, monkeypatch):
    started = student_client.post("/v2/assessments/pretest/start").json()
    session_id = started["session"]["session_id"]
    with TestingSessionLocal() as db:
        session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).one()
        release = register_candidate_release(db)
        assert "bank_snapshot" not in (release.manifest_json or {})
        assert db.query(PrivateContentBankSnapshot).filter(PrivateContentBankSnapshot.content_release_id == release.id).one_or_none() is not None
        db.commit()
    import v2_assessment_runtime as runtime
    monkeypatch.setattr(runtime, "get_release", lambda: {"checksum": "different", "version": "future"})
    resumed = student_client.get(f"/v2/assessments/sessions/{session_id}")
    assert resumed.status_code == 200
    assert resumed.json()["interaction"]["question"]["question_id"] == started["interaction"]["question"]["question_id"]

def test_shared_official_selection_preserves_history_and_report_average(researcher_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        original = AssessmentSession(student_id=student.id, session_type="pretest", status="completed",
            assessment_attempt_no=1, v2_state="completed", official_for_reporting=False, final_score=20)
        newer = AssessmentSession(student_id=student.id, session_type="pretest", status="completed",
            assessment_attempt_no=2, v2_state="completed", official_for_reporting=False, final_score=80)
        db.add_all([original, newer]); db.flush()
        newer.supersedes_session_id = original.id
        mark_official_completed_attempt(db, original)
        db.commit()
        mark_official_completed_attempt(db, newer)
        db.commit()
        history = db.query(AssessmentSession).filter(AssessmentSession.student_id == student.id).order_by(AssessmentSession.assessment_attempt_no).all()
        assert len(history) == 2
        assert [row.official_for_reporting for row in history] == [False, True]
        assert newer.supersedes_session_id == original.id
    report = researcher_client.get("/v2/assessments/admin/reports/summary")
    assert report.status_code == 200
    assert report.json()["averages"]["pretest"] == 80.0


def test_private_audio_stream_resolves_only_linked_assessment_evidence(researcher_client, monkeypatch):
    from fastapi.responses import Response
    import recordings
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        session = AssessmentSession(student_id=student.id, content_release_id=release.id, session_type="pretest",
            status="in_progress", v2_state="waiting_review", v2_question_index=30)
        db.add(session); db.flush()
        q = next(q for q in get_release()["questions"] if q["role"] == "pretest" and q["interaction"] == "read_aloud")
        row = AssessmentQuestionResponse(assessment_session_id=session.id, question_id=q["id"], role="pretest",
            answer_json={"audio_storage_key": f"audio/{student.id}/owned.webm"}, submit_key=str(uuid4()),
            status="pending_review", is_correct=None, skill_group=q["skill_group"], evidence_type=q["evidence_type"])
        db.add(row); db.flush()
        db.add(AudioSubmission(assessment_response_id=row.id, storage_key=f"audio/{student.id}/owned.webm",
            file_size=2000, mime_type="audio/webm", status="pending_review"))
        response_id = row.id
        student_id = student.id
        db.commit()
    checked = []
    def fake_play_by_key(*, key, range_header, researcher):
        checked.append((key, range_header, researcher.role))
        return Response(b"test-audio", media_type="audio/webm")
    monkeypatch.setattr(recordings, "play_by_key", fake_play_by_key)
    result = researcher_client.get(f"/v2/assessments/admin/responses/{response_id}/audio", headers={"Range": "bytes=0-2"})
    assert result.status_code == 200
    assert checked == [(f"audio/{student_id}/owned.webm", "bytes=0-2", "researcher")]
    monkeypatch.setattr("v2_assessment_runtime.storage.verify_audio", lambda *_args, **_kwargs: None)
    denied = researcher_client.post(
        f"/v2/assessments/admin/responses/{response_id}/review",
        json={"is_correct": True, "note": "تشغيل جزئي لا يكفي"},
    )
    assert denied.status_code == 409
    item = next(
        row for row in researcher_client.get("/v2/assessments/admin/review-queue").json()["items"]
        if row["response_id"] == response_id
    )
    assert item["audio_playback_completed"] is False
    audio_id = item["audio_submission_id"]
    stale = researcher_client.post(
        f"/v2/assessments/admin/responses/{response_id}/audio-completed",
        json={"audio_submission_id": audio_id + 999},
    )
    assert stale.status_code == 409
    for _ in range(2):
        acknowledged = researcher_client.post(
            f"/v2/assessments/admin/responses/{response_id}/audio-completed",
            json={"audio_submission_id": audio_id},
        )
        assert acknowledged.status_code == 200, acknowledged.text
    queue_after = researcher_client.get("/v2/assessments/admin/review-queue").json()["items"]
    assert next(row for row in queue_after if row["response_id"] == response_id)["audio_playback_completed"] is True
    monkeypatch.setattr("v2_assessment_runtime._finish_if_ready", lambda *_args, **_kwargs: None)
    reviewed = researcher_client.post(
        f"/v2/assessments/admin/responses/{response_id}/review",
        json={"is_correct": True, "note": "اكتمل تشغيل التسجيل ومراجعته"},
    )
    assert reviewed.status_code == 200, reviewed.text
    with TestingSessionLocal() as db:
        assert db.query(AuditLog).filter(
            AuditLog.action == "v2_review_audio_playback_completed",
            AuditLog.entity_id == str(response_id),
        ).count() == 1
    assert researcher_client.get("/v2/assessments/admin/responses/999999/audio").status_code == 404

def test_v2_pretest_does_not_bypass_completed_v1_history(student_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        old = AssessmentSession(student_id=student.id, session_type="pretest", status="completed",
            assessment_attempt_no=1, official_for_reporting=True, final_score=75)
        db.add(old)
        db.commit()
    started = student_client.post("/v2/assessments/pretest/start")
    assert started.status_code == 409
    assert "تفويض" in started.json()["detail"]
    with TestingSessionLocal() as db:
        assert db.query(AssessmentSession).count() == 1

def test_reading_review_requires_unchanged_private_object(researcher_client, monkeypatch):
    import storage
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        session = AssessmentSession(student_id=student.id, content_release_id=release.id, session_type="pretest",
            status="in_progress", v2_state="waiting_review", v2_question_index=30)
        db.add(session); db.flush()
        q = next(q for q in get_release()["questions"] if q["role"] == "pretest" and q["interaction"] == "read_aloud")
        response = AssessmentQuestionResponse(assessment_session_id=session.id, question_id=q["id"], role="pretest",
            answer_json={"audio_storage_key": f"audio/{student.id}/lost.webm"}, submit_key=str(uuid4()),
            status="pending_review", is_correct=None, skill_group=q["skill_group"], evidence_type=q["evidence_type"])
        db.add(response); db.flush()
        db.add(AudioSubmission(assessment_response_id=response.id, storage_key=f"audio/{student.id}/lost.webm",
            file_size=5120, mime_type="audio/webm", status="pending_review"))
        response_id = response.id
        db.commit()
    def missing(*_args, **_kwargs):
        raise ValueError("missing")
    monkeypatch.setattr(storage, "verify_audio", missing)
    response = researcher_client.post(f"/v2/assessments/admin/responses/{response_id}/review",
        json={"is_correct": True, "note": "استماع ومراجعة"})
    assert response.status_code == 409
    with TestingSessionLocal() as db:
        row = db.query(AssessmentQuestionResponse).filter(AssessmentQuestionResponse.id == response_id).one()
        assert row.status == "pending_review" and row.is_correct is None


def test_pretest_access_matrix_requires_student_authentication(client):
    """401 without a session, 403 for a supervisor, then 200 for the student."""
    assert client.post("/v2/assessments/pretest/start").status_code == 401
    assert client.get("/v2/assessments/sessions/1").status_code == 401
    assert client.post(
        "/v2/assessments/sessions/1/answers",
        json={"submit_key": str(uuid4()), "selected_option_ids": ["synthetic"]},
    ).status_code == 401

    researcher = client.post("/auth/login", json={
        "username": "researcher1", "password": "test-only-researcher-password",
    })
    assert researcher.status_code == 200
    assert client.post("/v2/assessments/pretest/start").status_code == 403
    assert client.get("/v2/assessments/sessions/1").status_code == 403
    assert client.post(
        "/v2/assessments/sessions/1/answers",
        json={"submit_key": str(uuid4()), "selected_option_ids": ["synthetic"]},
    ).status_code == 403

    assert client.post("/auth/student-login", json={"access_code": "STU001"}).status_code == 200
    started = client.post("/v2/assessments/pretest/start")
    assert started.status_code == 200
    assert started.json()["session"]["progress"]["answered"] == 0


def test_pretest_invalid_answer_and_reused_key_conflict_do_not_advance(student_client):
    """422 validation and 409 key conflict cannot consume a second question."""
    started = student_client.post("/v2/assessments/pretest/start")
    assert started.status_code == 200
    session_id = started.json()["session"]["session_id"]
    question = get_question(started.json()["interaction"]["question"]["question_id"])
    assert len(question["options"]) >= 2
    options = [item["id"] for item in question["options"]]
    url = f"/v2/assessments/sessions/{session_id}/answers"
    key = str(uuid4())

    assert student_client.post(url, json={
        "submit_key": "bad", "selected_option_ids": [options[0]],
    }).status_code == 422
    assert student_client.post(url, json={
        "submit_key": str(uuid4()), "selected_option_ids": ["unknown-option"],
    }).status_code == 422
    assert student_client.get(f"/v2/assessments/sessions/{session_id}").json()["session"]["progress"]["answered"] == 0

    accepted = student_client.post(url, json={
        "submit_key": key, "selected_option_ids": [options[0]],
    })
    assert accepted.status_code == 200
    assert accepted.json()["assessment"]["session"]["progress"]["answered"] == 1
    replay = student_client.post(url, json={
        "submit_key": key, "selected_option_ids": [options[0]],
    })
    assert replay.status_code == 200 and replay.json()["status"] == "replayed"
    conflict = student_client.post(url, json={
        "submit_key": key, "selected_option_ids": [options[1]],
    })
    assert conflict.status_code == 409
    assert student_client.get(f"/v2/assessments/sessions/{session_id}").json()["session"]["progress"]["answered"] == 1
    with TestingSessionLocal() as db:
        assert db.query(AssessmentQuestionResponse).filter(
            AssessmentQuestionResponse.assessment_session_id == session_id,
        ).count() == 1


def test_pretest_start_refuses_existing_v1_active_session(student_client):
    """Do not create a parallel V2 session over a historical V1 attempt."""
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        db.add(AssessmentSession(
            student_id=student.id, session_type="pretest", status="in_progress",
            assessment_attempt_no=1, elapsed_seconds=1,
        ))
        db.commit()
    blocked = student_client.post("/v2/assessments/pretest/start")
    assert blocked.status_code == 409
    assert student_client.get("/v2/assessments/current-action").json()["action"] == "migration_review"
    with TestingSessionLocal() as db:
        assert db.query(AssessmentSession).count() == 1


def test_pretest_503_preview_gate_keeps_answer_and_session_resumable(student_client, monkeypatch):
    """Temporary preview denial must not consume a question or duplicate an answer."""
    import v2_lesson_runtime as lesson_runtime

    started = student_client.post("/v2/assessments/pretest/start")
    assert started.status_code == 200
    session_id = started.json()["session"]["session_id"]
    question = get_question(started.json()["interaction"]["question"]["question_id"])
    assert question["options"]
    url = f"/v2/assessments/sessions/{session_id}/answers"
    answer = {"submit_key": str(uuid4()), "selected_option_ids": [question["options"][0]["id"]]}

    monkeypatch.setattr(lesson_runtime, "protected_runtime", lambda: True)
    monkeypatch.setattr(lesson_runtime, "trial_v2_preview_allowed", lambda: False)
    assert student_client.post("/v2/assessments/pretest/start").status_code == 503
    assert student_client.get(f"/v2/assessments/sessions/{session_id}").status_code == 503
    assert student_client.post(url, json=answer).status_code == 503

    monkeypatch.setattr(lesson_runtime, "protected_runtime", lambda: False)
    resumed = student_client.get(f"/v2/assessments/sessions/{session_id}")
    assert resumed.status_code == 200
    assert resumed.json()["session"]["progress"]["answered"] == 0
    assert student_client.post("/v2/assessments/pretest/start").json()["session"]["session_id"] == session_id
    saved = student_client.post(url, json=answer)
    assert saved.status_code == 200
    assert saved.json()["assessment"]["session"]["progress"]["answered"] == 1
    assert student_client.post(url, json=answer).json()["status"] == "replayed"
    with TestingSessionLocal() as db:
        assert db.query(AssessmentQuestionResponse).filter(
            AssessmentQuestionResponse.assessment_session_id == session_id,
        ).count() == 1


def test_untouched_legacy_pretest_is_adopted_on_explicit_start_with_audited_history(student_client):
    import json
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == 'STU001').one()
        shell = AssessmentSession(student_id=student.id, session_type='pretest', status='in_progress')
        db.add(shell)
        db.commit()
        session_id = shell.id
        started_at = shell.started_at
    assert student_client.get('/v2/assessments/current-action').json()['action'] == 'start_pretest'
    with TestingSessionLocal() as db:
        assert db.query(StudentJourney).count() == 0
        assert db.get(AssessmentSession, session_id).v2_state is None
    started = student_client.post('/v2/assessments/pretest/start')
    assert started.status_code == 200, started.text
    assert started.json()['session']['session_id'] == session_id
    assert started.json()['interaction']['progress']['index'] == 1
    replay = student_client.post('/v2/assessments/pretest/start')
    assert replay.status_code == 200 and replay.json()['session']['session_id'] == session_id
    with TestingSessionLocal() as db:
        assert db.query(AssessmentSession).count() == db.query(StudentJourney).count() == 1
        row = db.get(AssessmentSession, session_id)
        assert row.started_at == started_at and row.final_score is None
        audit = db.query(AuditLog).filter(AuditLog.action == 'v2.pretest.empty_legacy_adopted').one()
        original = json.loads(audit.details)
        assert original['id'] == session_id and original['v2_state'] is None
        assert original['status'] == 'in_progress' and original['final_score'] is None


@pytest.mark.parametrize('metadata', [
    {'elapsed_seconds': 1}, {'final_score': 0}, {'assigned_level': 1},
    {'official_for_reporting': True}, {'v2_question_index': 1}, {'v2_result_json': {}},
    {'status': 'completed'}, {'session_type': 'core'}, {'session_type': 'posttest'},
])
def test_legacy_evidence_is_never_reclassified_as_a_new_pretest(student_client, metadata):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == 'STU001').one()
        db.add(AssessmentSession(student_id=student.id, **{
            'session_type': 'pretest', 'status': 'in_progress', **metadata,
        }))
        db.commit()
    assert student_client.get('/v2/assessments/current-action').json()['action'] == 'migration_review'
    assert student_client.post('/v2/assessments/pretest/start').status_code == 409
    with TestingSessionLocal() as db:
        assert db.query(StudentJourney).count() == 0
        assert db.query(AssessmentSession).count() == 1
        assert db.query(AssessmentSession).one().v2_state is None


def test_even_unanswered_v1_attempt_prevents_shell_adoption(student_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == 'STU001').one()
        skill = Skill(skill_key='W1-LEGACY-SKILL', name='مهارة اصطناعية', level_id=1)
        db.add(skill)
        db.flush()
        item = ContentItem(stable_key='W1-LEGACY-TEST', kind='pretest_question', level_id=1,
                           skill_id=skill.id, interaction_type='choose_one', order_index=1,
                           version='test', checksum='a'*64)
        shell = AssessmentSession(student_id=student.id, session_type='pretest', status='in_progress')
        db.add_all([item, shell])
        db.flush()
        db.add(Attempt(session_id=shell.id, item_id=item.id, status='in_progress'))
        db.commit()
    assert student_client.get('/v2/assessments/current-action').json()['action'] == 'migration_review'
    assert student_client.post('/v2/assessments/pretest/start').status_code == 409
    with TestingSessionLocal() as db:
        assert db.query(Attempt).count() == 1
        assert db.query(StudentJourney).count() == 0


@pytest.mark.parametrize(
    ("percentage", "level"),
    [(0, 1), (49.99, 1), (50, 2), (79.99, 2), (80, 3), (100, 3)],
)
def test_approved_placement_percentage_boundaries(percentage, level):
    assert _recommended_level(percentage) == level


def test_missing_or_invalid_result_cannot_produce_placement_recommendation():
    assert _recommended_level(None) is None
    with pytest.raises(ValueError):
        _recommended_level(100.01)
    with pytest.raises(ValueError):
        _recommended_level(-0.01)
