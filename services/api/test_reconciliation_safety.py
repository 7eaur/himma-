"""Regressions for the first official reconciliation slice."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from activities import _score_submission
from db.database import SessionLocal
from db.models import User
from study_capacity import student_limit


def test_capacity_is_configurable_and_counts_existing_students(researcher_client, monkeypatch):
    monkeypatch.setenv("HIMMA_MAX_STUDENTS", "2")
    assert researcher_client.get("/researcher/student-capacity").json() == {"total": 1, "limit": 2, "remaining": 1}
    assert researcher_client.post("/researcher/students", json={"full_name": "طالب تجريبي", "grade_level": 3}).status_code == 201
    assert researcher_client.post("/researcher/students", json={"full_name": "طالب زائد", "grade_level": 3}).status_code == 409
    assert researcher_client.get("/researcher/student-capacity").json()["remaining"] == 0


@pytest.mark.parametrize("value", ["0", "-1", "invalid"])
def test_invalid_capacity_is_not_silently_accepted(monkeypatch, value):
    monkeypatch.setenv("HIMMA_MAX_STUDENTS", value)
    with pytest.raises(ValueError):
        student_limit()


def test_student_cannot_inspect_study_capacity(student_client):
    assert student_client.get("/researcher/student-capacity").status_code == 403


def test_me_rechecks_current_database_role(researcher_client):
    with SessionLocal() as db:
        db.query(User).filter(User.username == "researcher1").one().role = "revoked"
        db.commit()
    assert researcher_client.get("/me").status_code == 401


def test_multi_select_uses_correctness_not_display_position():
    item = SimpleNamespace(template_data={"canonical_interaction_type": "choose_many"}, interaction_type="choose_many")
    step = SimpleNamespace(options=[SimpleNamespace(id=n, order_index=n, is_correct=n in {2, 4}) for n in range(1, 5)])
    assert _score_submission(item, step, [4, 2]) is True
    assert _score_submission(item, step, [1, 2]) is False
    with pytest.raises(HTTPException):
        _score_submission(item, step, [2, 2])


def test_legacy_assessment_response_does_not_expose_answer_metadata():
    from schemas import ContentItemResponse
    result = ContentItemResponse.model_validate({
        "id": 1, "stable_key": "test", "kind": "pretest_question", "interaction_type": "choose_one",
        "template_data": {"criterion": "secret answer", "db_runtime": {"source_item": {"criterion": "secret answer"}}},
    }).model_dump()
    assert "template_data" not in result
