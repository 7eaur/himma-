"""Supervisors cannot override another live human-review claim."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt

from conftest import TestingSessionLocal
from db.learning_models import AssessmentQuestionResponse, StudentJourney, V2ReviewClaim
from db.models import AssessmentSession, Student, User
from test_v2_lesson_review import reading as _reading_response, listened, queued
from v2_content.importer import register_candidate_release
from v2_content.repository import get_release


def _login(client, username: str):
    response = client.post("/auth/login", json={
        "username": username, "password": "test-only-researcher-password",
    })
    assert response.status_code == 200, response.text


def _add_second_researcher():
    with TestingSessionLocal() as db:
        second = User(
            username="researcher2",
            password_hash=bcrypt.hashpw(
                b"test-only-researcher-password", bcrypt.gensalt()
            ).decode("utf-8"),
            role="researcher",
        )
        db.add(second)
        db.commit()
        return second.id


def test_two_supervisors_claim_and_release_lesson_without_overriding(student_client, monkeypatch):
    _, response_id, _ = _reading_response(student_client, monkeypatch)
    first_id = None
    _add_second_researcher()
    _login(student_client, "researcher1")
    first_id = student_client.post(
        f"/v2/review-claims/admin/lesson/{response_id}/claim",
    )
    assert first_id.status_code == 200, first_id.text
    assert first_id.json()["status"] == "claimed"

    _login(student_client, "researcher2")
    second_claim = student_client.post(
        f"/v2/review-claims/admin/lesson/{response_id}/claim",
    )
    assert second_claim.status_code == 409, second_claim.text
    denied_grade = student_client.post(
        f"/v2/review/lessons/{response_id}/decision",
        json={"is_correct": True, "note": "قرار مشرف غير المالك"},
    )
    assert denied_grade.status_code == 409
    denied_retry = student_client.post(
        f"/v2/retries/admin/lesson/{response_id}/request",
        json={"reason": "المالك الآخر يحجز هذه الإجابة الآن"},
    )
    assert denied_retry.status_code == 409
    assert student_client.delete(
        f"/v2/review-claims/admin/lesson/{response_id}/claim",
    ).status_code == 409

    _login(student_client, "researcher1")
    released = student_client.delete(
        f"/v2/review-claims/admin/lesson/{response_id}/claim",
    )
    assert released.status_code == 200, released.text
    _login(student_client, "researcher2")
    owned = student_client.post(
        f"/v2/review-claims/admin/lesson/{response_id}/claim",
    )
    assert owned.status_code == 200, owned.text
    listened(student_client, response_id, queued(student_client, response_id))
    graded = student_client.post(
        f"/v2/review/lessons/{response_id}/decision",
        json={"is_correct": True, "note": "مطابق لمعيار القراءة بعد الاستماع للدليل"},
    )
    assert graded.status_code == 200, graded.text
    assert student_client.post(
        f"/v2/review-claims/admin/lesson/{response_id}/claim",
    ).status_code == 409
    with TestingSessionLocal() as db:
        row = db.query(V2ReviewClaim).filter(
            V2ReviewClaim.lesson_response_id == response_id
        ).one()
        assert row.expires_at is not None


def test_expired_claim_can_be_reassigned_to_new_researcher(student_client, monkeypatch):
    _, response_id, _ = _reading_response(student_client, monkeypatch)
    new_id = _add_second_researcher()
    _login(student_client, "researcher1")
    assert student_client.post(
        f"/v2/review-claims/admin/lesson/{response_id}/claim",
    ).status_code == 200
    with TestingSessionLocal() as db:
        claim = db.query(V2ReviewClaim).filter(
            V2ReviewClaim.lesson_response_id == response_id,
        ).one()
        claim.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    _login(student_client, "researcher2")
    claimed = student_client.post(
        f"/v2/review-claims/admin/lesson/{response_id}/claim",
    )
    assert claimed.status_code == 200, claimed.text
    with TestingSessionLocal() as db:
        claim = db.query(V2ReviewClaim).filter(
            V2ReviewClaim.lesson_response_id == response_id,
        ).one()
        assert claim.reviewer_id == new_id


def test_assessment_claim_prevents_second_supervisor_request(student_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(
            student_id=student.id, content_release_id=release.id,
            placement_state="in_progress",
        ))
        session = AssessmentSession(
            student_id=student.id, content_release_id=release.id,
            session_type="pretest", status="in_progress",
            v2_state="waiting_review", v2_question_index=30,
            assessment_attempt_no=1, v2_policy_version="test",
        )
        db.add(session); db.flush()
        question = next(q for q in get_release()["questions"]
                        if q["role"] == "pretest" and q["interaction"] == "read_aloud")
        response = AssessmentQuestionResponse(
            assessment_session_id=session.id, question_id=question["id"],
            role="pretest", answer_json={"audio_storage_key": f"audio/{student.id}/synthetic.webm"},
            submit_key=str(uuid4()), status="pending_review", is_correct=None,
            skill_group=question["skill_group"],
            evidence_type=question["evidence_type"],
        )
        db.add(response); db.commit()
        response_id = response.id
    _add_second_researcher()
    _login(student_client, "researcher1")
    assert student_client.post(
        f"/v2/review-claims/admin/assessment/{response_id}/claim",
    ).status_code == 200
    _login(student_client, "researcher2")
    denied = student_client.post(
        f"/v2/retries/admin/assessment/{response_id}/request",
        json={"reason": "لا يجوز تجاوز المشرف صاحب الحجز"},
    )
    assert denied.status_code == 409
