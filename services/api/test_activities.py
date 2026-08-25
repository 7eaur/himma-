"""Stage 2 closure tests for the real learning activity runtime."""

from datetime import datetime, timezone

import seed
from db.database import SessionLocal
from db.models import AssessmentSession, Attempt, AttemptResponse, ContentItem, ContentOption, Student


def _complete_pretest(access_code: str = "STU001", level: int = 1) -> int:
    db = SessionLocal()
    student = db.query(Student).filter(Student.access_code == access_code).one()
    student.current_level = level
    existing = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.session_type == "pretest",
    ).first()
    if not existing:
        db.add(
            AssessmentSession(
                student_id=student.id,
                session_type="pretest",
                status="completed",
                assigned_level=level,
                completed_at=datetime.now(timezone.utc),
            )
        )
    else:
        existing.status = "completed"
        existing.assigned_level = level
        existing.completed_at = datetime.now(timezone.utc)
    db.commit()
    student_id = student.id
    db.close()
    return student_id


def _ordered_option_ids(step_id: int) -> list[int]:
    db = SessionLocal()
    ids = [
        row.id
        for row in db.query(ContentOption)
        .filter(ContentOption.step_id == step_id)
        .order_by(ContentOption.order_index)
        .all()
    ]
    db.close()
    return ids


def _correct_option_id(step_id: int) -> int:
    db = SessionLocal()
    row = db.query(ContentOption).filter(
        ContentOption.step_id == step_id,
        ContentOption.is_correct.is_(True),
    ).first()
    assert row is not None
    option_id = row.id
    db.close()
    return option_id


def _mark_audio_round_reviewed(session_id: int, item_id: int, step_id: int) -> None:
    """Finish an audio round at the assessment-review boundary for this lifecycle test.

    Audio upload/review itself has dedicated coverage. This helper keeps the older
    Stage-2 "exactly ten core activities" regression focused on routing/resume and
    avoids pretending a read-aloud round has a multiple-choice option.
    """
    db = SessionLocal()
    attempt = db.query(Attempt).filter(
        Attempt.session_id == session_id,
        Attempt.item_id == item_id,
        Attempt.status == "in_progress",
    ).one()
    existing = db.query(AttemptResponse).filter(
        AttemptResponse.attempt_id == attempt.id,
        AttemptResponse.step_id == step_id,
    ).first()
    if not existing:
        db.add(
            AttemptResponse(
                attempt_id=attempt.id,
                step_id=step_id,
                selected_option_id=None,
                is_correct=True,
                elapsed_seconds=1,
            )
        )
        db.commit()
    db.close()


class TestActivityLifecycle:
    def test_learning_requires_completed_pretest(self, student_client):
        status = student_client.get("/activities/status")
        assert status.status_code == 200
        assert status.json()["available"] is False
        assert status.json()["reason"] == "pretest_required"

        start = student_client.post("/activities/start")
        assert start.status_code == 409

    def test_level_one_executes_exactly_ten_core_activities_and_resumes(self, student_client):
        seed.run_seed()
        _complete_pretest(level=1)

        started = student_client.post("/activities/start")
        assert started.status_code == 200
        session_id = started.json()["session_id"]
        assert started.json()["level_id"] == 1
        assert started.json()["total_items"] == 10

        resumed = student_client.post("/activities/start")
        assert resumed.status_code == 200
        assert resumed.json()["session_id"] == session_id

        seen_items: list[str] = []
        safety = 0
        while True:
            safety += 1
            assert safety < 80, "Core learning path did not terminate"
            response = student_client.get(f"/activities/session/{session_id}/next")
            assert response.status_code == 200
            activity = response.json()
            if activity is None:
                break

            if not seen_items or seen_items[-1] != activity["item"]["canonical_id"]:
                seen_items.append(activity["item"]["canonical_id"])

            step = activity["step"]
            interaction = activity["item"]["interaction_type"]
            if interaction in {"read_aloud", "timed_read_aloud"} and not step["media_gaps"]:
                _mark_audio_round_reviewed(session_id, activity["item"]["id"], step["id"])
                continue

            if step["media_gaps"]:
                payload = {
                    "step_id": step["id"],
                    "selected_option_ids": [],
                    "hint_used": False,
                    "elapsed_seconds": 1,
                    "declared_media_gap_skip": True,
                }
            elif interaction in {"sequence", "memory_sequence", "path_sequence", "build_word"}:
                payload = {
                    "step_id": step["id"],
                    "selected_option_ids": _ordered_option_ids(step["id"]),
                    "hint_used": False,
                    "elapsed_seconds": 1,
                    "declared_media_gap_skip": False,
                }
            else:
                payload = {
                    "step_id": step["id"],
                    "selected_option_ids": [_correct_option_id(step["id"])],
                    "hint_used": False,
                    "elapsed_seconds": 1,
                    "declared_media_gap_skip": False,
                }

            key = f"activity-test-{session_id}-{step['id']}-{activity['attempts_used'] + 1}"
            submitted = student_client.post(
                f"/activities/session/{session_id}/attempt/{activity['item']['id']}/submit",
                json=payload,
                headers={"Idempotency-Key": key},
            )
            assert submitted.status_code == 200, submitted.text

        assert seen_items == [f"L1-CORE-{index:02d}" for index in range(1, 11)]
        progress = student_client.get(f"/activities/session/{session_id}/progress")
        assert progress.status_code == 200
        assert progress.json()["status"] == "completed"
        assert progress.json()["completed_items"] == 10
        assert progress.json()["total_items"] == 10

        profile = student_client.get("/profile")
        assert profile.status_code == 200
        assert profile.json()["next_action"] == "learning"

    def test_structured_activity_submission_is_idempotent(self, student_client):
        seed.run_seed()
        _complete_pretest(level=1)
        session_id = student_client.post("/activities/start").json()["session_id"]
        activity = student_client.get(f"/activities/session/{session_id}/next").json()
        step = activity["step"]
        payload = {
            "step_id": step["id"],
            "selected_option_ids": [_correct_option_id(step["id"])],
            "hint_used": False,
            "elapsed_seconds": 3,
            "declared_media_gap_skip": False,
        }
        headers = {"Idempotency-Key": "activity-idempotency-0001"}
        first = student_client.post(
            f"/activities/session/{session_id}/attempt/{activity['item']['id']}/submit",
            json=payload,
            headers=headers,
        )
        replay = student_client.post(
            f"/activities/session/{session_id}/attempt/{activity['item']['id']}/submit",
            json=payload,
            headers=headers,
        )
        assert first.status_code == 200
        assert replay.status_code == 200
        assert replay.json() == first.json()

    def test_only_assigned_level_core_items_are_selected(self, student_client):
        seed.run_seed()
        _complete_pretest(level=3)
        session_id = student_client.post("/activities/start").json()["session_id"]
        activity = student_client.get(f"/activities/session/{session_id}/next").json()
        assert activity["item"]["level_id"] == 3
        assert activity["item"]["canonical_id"] == "L3-CORE-01"
        assert activity["item"]["interaction_type"] == "read_aloud"

        db = SessionLocal()
        assert db.query(ContentItem).filter(
            ContentItem.kind == "core_activity",
            ContentItem.level_id == 3,
        ).count() == 10
        db.close()
