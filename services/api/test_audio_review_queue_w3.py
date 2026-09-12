"""W3 regression coverage for the supervisor audio-review queue.

The queue must be filterable by student, expose enough context for a safe
review decision, and only surface the latest uploaded recording. Grading or
requesting a rerecord must preserve immutable submission history while
removing the reviewed recording from the pending queue.
"""

import seed
from db.database import SessionLocal
from db.models import AssessmentSession, Attempt, AttemptResponse, AudioSubmission, ContentItem, Student


def _create_pending_submission(db, *, student: Student, storage_key: str) -> tuple[int, int]:
    audio_item = (
        db.query(ContentItem)
        .filter(
            ContentItem.kind == "pretest_question",
            ContentItem.interaction_type == "read_aloud",
        )
        .order_by(ContentItem.order_index, ContentItem.id)
        .first()
    )
    assert audio_item is not None
    assert audio_item.steps

    session = AssessmentSession(student_id=student.id, session_type="pretest", status="in_progress")
    db.add(session)
    db.flush()

    attempt = Attempt(session_id=session.id, item_id=audio_item.id, status="completed")
    db.add(attempt)
    db.flush()

    response = AttemptResponse(attempt_id=attempt.id, step_id=audio_item.steps[0].id)
    db.add(response)
    db.flush()

    submission = AudioSubmission(
        response_id=response.id,
        storage_key=storage_key,
        file_size=2048,
        mime_type="audio/webm",
        status="uploaded",
    )
    db.add(submission)
    db.commit()
    return response.id, submission.id


def test_filtered_audio_queue_preserves_review_lifecycle_and_metadata(researcher_client):
    seed.run_seed()
    db = SessionLocal()
    try:
        first_student = Student(
            access_code="947261",
            name="طالب مراجعة أول",
            grade_level=3,
            current_level=1,
            is_active=True,
        )
        second_student = Student(
            access_code="947262",
            name="طالب مراجعة ثان",
            grade_level=3,
            current_level=1,
            is_active=True,
        )
        db.add_all([first_student, second_student])
        db.flush()

        first_response_id, first_submission_id = _create_pending_submission(
            db,
            student=first_student,
            storage_key="tests/w3-filtered-first.webm",
        )
        _, second_submission_id = _create_pending_submission(
            db,
            student=second_student,
            storage_key="tests/w3-filtered-second.webm",
        )
        first_student_id = first_student.id
        second_student_id = second_student.id
    finally:
        db.close()

    filtered = researcher_client.get(f"/review/pending-audio?student_id={first_student_id}")
    assert filtered.status_code == 200
    rows = filtered.json()
    assert len(rows) == 1
    assert rows[0]["id"] == first_submission_id
    assert rows[0]["student_id"] == first_student_id
    assert rows[0]["student_name"] == "طالب مراجعة أول"
    assert rows[0]["session_type"] == "pretest"
    assert rows[0]["item_title"]
    assert rows[0]["expected_reading_text"]
    assert rows[0]["status"] == "uploaded"

    unfiltered = researcher_client.get("/review/pending-audio")
    assert unfiltered.status_code == 200
    pending_ids = {row["id"] for row in unfiltered.json()}
    assert first_submission_id in pending_ids
    assert second_submission_id in pending_ids

    rejected = researcher_client.post(
        f"/review/audio/{first_submission_id}/grade",
        json={"is_valid": False},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rerecord_required"
    assert researcher_client.get(
        f"/review/pending-audio?student_id={first_student_id}"
    ).json() == []

    db = SessionLocal()
    try:
        historical = db.query(AudioSubmission).filter(AudioSubmission.id == first_submission_id).one()
        assert historical.status == "rerecord_required"
        replacement = AudioSubmission(
            response_id=first_response_id,
            storage_key="tests/w3-filtered-rerecord.webm",
            file_size=3072,
            mime_type="audio/webm",
            status="uploaded",
        )
        db.add(replacement)
        db.commit()
        db.refresh(replacement)
        replacement_id = replacement.id
    finally:
        db.close()

    replacement_queue = researcher_client.get(
        f"/review/pending-audio?student_id={first_student_id}"
    )
    assert replacement_queue.status_code == 200
    assert [row["id"] for row in replacement_queue.json()] == [replacement_id]

    graded = researcher_client.post(
        f"/review/audio/{replacement_id}/grade",
        json={
            "is_valid": True,
            "target_units": 10,
            "deletions": 0,
            "substitutions": 0,
            "insertions": 0,
            "pronunciation_notes": "واضح",
            "fluency_notes": "مستقر",
        },
    )
    assert graded.status_code == 200
    assert graded.json()["status"] == "graded"
    assert researcher_client.get(
        f"/review/pending-audio?student_id={first_student_id}"
    ).json() == []

    db = SessionLocal()
    try:
        statuses = {
            row.id: row.status
            for row in db.query(AudioSubmission)
            .filter(AudioSubmission.response_id == first_response_id)
            .order_by(AudioSubmission.id)
            .all()
        }
        assert statuses[first_submission_id] == "rerecord_required"
        assert statuses[replacement_id] == "graded"
        second = db.query(AudioSubmission).filter(AudioSubmission.id == second_submission_id).one()
        assert second.status == "uploaded"
        assert second.response.attempt.session.student_id == second_student_id
    finally:
        db.close()
