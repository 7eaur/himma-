"""The backend refuses to claim legacy review APIs are safe to remove blindly."""
from db.learning_models import AssessmentQuestionResponse, V2ReviewRetryTask
from db.models import User
from test_v2_reading_job_store import db, enqueue_assessment, new_v2_assessment
from v2_reading_engine.cutover_audit import native_cutover_audit


def test_existing_unbound_student_audio_blocks_staff_review_route_removal(db):
    student, release, response, audio = new_v2_assessment(db)
    before = native_cutover_audit(db)
    assert before["legacy_assessment_pending"] == 1
    assert before["native_jobs_waiting"] == 0
    assert before["can_retire_manual_routes"] is False
    assert response.is_correct is None
    job = enqueue_assessment(db, student, release, response, audio)
    after = native_cutover_audit(db)
    assert after["legacy_assessment_pending"] == 0
    assert after["native_jobs_waiting"] == 1
    assert after["can_retire_manual_routes"] is True
    assert response.status == "pending_review" and job.status == "queued"


def test_staff_requested_rerecord_blocks_cutover_even_when_voice_job_exists(db):
    student, release, response, audio = new_v2_assessment(db)
    enqueue_assessment(db, student, release, response, audio)
    reviewer = User(username="native-cutover-operator", password_hash="test-only")
    db.add(reviewer)
    db.flush()
    task = V2ReviewRetryTask(
        assessment_response_id=response.id, student_id=student.id,
        requested_by=reviewer.id, request_kind="rerecord",
        status="requested", reason="test-only outstanding review",
    )
    db.add(task)
    db.flush()
    assert native_cutover_audit(db)["can_retire_manual_routes"] is False
    task.status = "resolved"
    assert native_cutover_audit(db)["can_retire_manual_routes"] is True


def test_native_cutover_audit_is_read_only_and_returns_no_student_information(db):
    student, release, response, audio = new_v2_assessment(db)
    before = db.query(AssessmentQuestionResponse).count()
    first = native_cutover_audit(db)
    second = native_cutover_audit(db)
    assert first == second and first["legacy_assessment_pending"] == 1
    assert db.query(AssessmentQuestionResponse).count() == before
    serialized = repr(first)
    assert student.name not in serialized
    assert audio.storage_key not in serialized
