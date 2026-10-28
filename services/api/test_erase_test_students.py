from unittest.mock import Mock

import pytest

from conftest import TestingSessionLocal
from db.models import AssessmentSession, AudioSubmission, Student, User
from db.learning_models import AssessmentQuestionResponse
from db.auth_models import AuthSessionState
from erase_test_students import erasure_plan, execute_erasure, public_plan


def fixture(db):
    child = Student(access_code="ERASE-TEST", name="Disposable fixture", is_active=False)
    db.add(child); db.flush()
    session = AssessmentSession(student_id=child.id, session_type="pretest", status="in_progress", v2_state="answering")
    db.add(session); db.flush()
    response = AssessmentQuestionResponse(assessment_session_id=session.id, question_id="V2-PRE-Q06", role="pretest",
        answer_json={"audio_storage_key": f"audio/{child.id}/test.wav"}, submit_key="erase-test-answer", status="pending_review",
        skill_group="S3", evidence_type="syllable_reading")
    db.add(response); db.flush()
    db.add(AudioSubmission(assessment_response_id=response.id, storage_key=f"audio/{child.id}/test.wav",
        file_size=80, mime_type="audio/wav", status="pending_review"))
    db.add(AuthSessionState(actor_role="student",actor_id=child.id,auth_epoch=1))
    db.commit()
    return child.id


def test_dry_run_is_private_and_wrong_scope_or_fingerprint_cannot_delete():
    with TestingSessionLocal() as db:
        child_id=fixture(db)
        with pytest.raises(ValueError,match="Cohort changed"):
            erasure_plan(db,[child_id],3)
        plan=erasure_plan(db,[child_id],2)
        assert plan["counts"]["assessment_question_responses"] == 1
        assert plan["audio_objects"] == 1
        assert "Disposable" not in str(public_plan(plan)) and "test.wav" not in str(public_plan(plan))
        delete_audio=Mock()
        with pytest.raises(ValueError,match="fingerprint"):
            execute_erasure(db,plan,"wrong",delete_audio)
        delete_audio.assert_not_called()
        assert db.query(Student).count()==2


def test_erases_only_authorized_child_graph_preserving_other_accounts_and_staff():
    with TestingSessionLocal() as db:
        child_id=fixture(db)
        plan=erasure_plan(db,[child_id],2)
        delete_audio=Mock()
        result=execute_erasure(db,plan,plan["fingerprint"],delete_audio)
        assert result["status"]=="deleted"
        delete_audio.assert_called_once_with(f"audio/{child_id}/test.wav",child_id)
        assert db.query(Student).count()==1 and db.query(User).count()==1
        assert db.query(AssessmentSession).count()==0
        assert db.query(AssessmentQuestionResponse).count()==0
        assert db.query(AudioSubmission).count()==0
        assert db.query(AuthSessionState).filter(AuthSessionState.actor_role=="student",AuthSessionState.actor_id==child_id).count()==0
        assert erasure_plan(db,[child_id],2)["already_absent"] is True


def test_active_account_or_changed_evidence_requires_a_new_plan():
    with TestingSessionLocal() as db:
        child_id=fixture(db)
        plan=erasure_plan(db,[child_id],2)
        child=db.get(Student,child_id); child.is_active=True; db.commit()
        with pytest.raises(ValueError,match="changed since"):
            execute_erasure(db,plan,plan["fingerprint"],Mock())
        fresh=erasure_plan(db,[child_id],2)
        with pytest.raises(ValueError,match="Deactivate"):
            execute_erasure(db,fresh,fresh["fingerprint"],Mock())
        assert db.query(Student).count()==2


def test_storage_outage_keeps_all_database_evidence_and_accounts_inactive():
    with TestingSessionLocal() as db:
        child_id=fixture(db)
        plan=erasure_plan(db,[child_id],2)
        with pytest.raises(RuntimeError,match="storage unavailable"):
            execute_erasure(db,plan,plan["fingerprint"],Mock(side_effect=RuntimeError("storage unavailable")))
        db.rollback()
        assert db.query(AudioSubmission).count()==1
        assert db.get(Student,child_id).is_active is False


def test_regular_seed_cannot_recreate_demo_students_even_with_a_stale_flag(monkeypatch):
    import db.seed as seed_module
    monkeypatch.setattr(seed_module,"SessionLocal",TestingSessionLocal)
    monkeypatch.setenv("ADMIN_USERNAME","researcher1")
    monkeypatch.setenv("ADMIN_PASSWORD","test-only-unused-existing-admin")
    monkeypatch.setenv("SEED_DEMO_STUDENTS","true")
    seed_module.seed()
    with TestingSessionLocal() as db:
        assert db.query(Student).count()==1
        assert db.query(User).count()==1


def test_deployed_v2_distribution_rejects_legacy_routes_even_before_first_pretest(monkeypatch):
    from fastapi import HTTPException
    import v1_student_guard
    monkeypatch.setattr(v1_student_guard,"protected_runtime",lambda:True)
    with TestingSessionLocal() as db:
        with pytest.raises(HTTPException) as rejected:
            v1_student_guard.require_legacy_student(db,db.query(Student).one())
        assert rejected.value.status_code==409


def test_orphan_audio_is_scoped_and_a_changed_object_listing_cannot_be_erased():
    with TestingSessionLocal() as db:
        child_id=fixture(db)
        keys=[f"audio/{child_id}/orphan.wav"]
        listing=lambda _:keys
        plan=erasure_plan(db,[child_id],2,list_audio=listing)
        assert plan["audio_objects"]==2
        keys.append(f"audio/{child_id}/new-upload.wav")
        with pytest.raises(ValueError,match="changed since"):
            execute_erasure(db,plan,plan["fingerprint"],Mock())
        with pytest.raises(ValueError,match="escaped"):
            erasure_plan(db,[child_id],2,list_audio=lambda _:["audio/999/unrelated.wav"])

def test_absent_authorized_ids_never_mask_unrelated_accounts_or_orphan_audio():
    with TestingSessionLocal() as db:
        child_id = fixture(db)
        missing_id = child_id + 1000
        with pytest.raises(ValueError, match="authorized IDs absent"):
            erasure_plan(db, [missing_id], 2)
        with pytest.raises(ValueError, match="Private audio remains"):
            erasure_plan(
                db, [missing_id], 3,
                list_audio=lambda student_id: [f"audio/{student_id}/orphan.webm"],
            )
