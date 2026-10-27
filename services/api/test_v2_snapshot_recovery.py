"""Recover one original immutable bank without changing a learner's evidence."""
import gzip
import json
from uuid import uuid4

from conftest import TestingSessionLocal
from db.learning_models import AssessmentQuestionResponse, PrivateContentBankSnapshot
from db.models import AssessmentSession, AuditLog, ContentRelease, Student
from v2_content import recovery

CHECKSUM = 'b78f8b01cdf00b9b0c9e311fb424d24c1bb286a0066fefb48fb6639235c2b085'


def _historical_row():
    release = json.loads(gzip.decompress((recovery.RECOVERY_ROOT / f'{CHECKSUM}.json.gz').read_bytes()))
    with TestingSessionLocal() as db:
        row = ContentRelease(version=release['version'], checksum=CHECKSUM, is_immutable=True, is_active=False)
        db.add(row)
        db.commit()
        return row.id, release


def test_exact_original_restore_is_idempotent_and_keeps_evidence_and_release_unchanged(researcher_client):
    release_id, original = _historical_row()
    question = next(q for q in original['questions'] if q['role'] == 'pretest' and q['interaction'] == 'read_aloud')
    with TestingSessionLocal() as db:
        student = db.query(Student).one()
        session = AssessmentSession(student_id=student.id, content_release_id=release_id, session_type='pretest',
            status='in_progress', v2_state='waiting_review', v2_question_index=30)
        db.add(session)
        db.flush()
        session_id = session.id
        answer = {'evidence_marker': 'unchanged-synthetic-evidence'}
        response = AssessmentQuestionResponse(assessment_session_id=session.id, question_id=question['id'],
            role='pretest', answer_json=answer, submit_key=str(uuid4()), status='pending_review',
            skill_group=question['skill_group'], evidence_type=question['evidence_type'])
        db.add(response)
        db.commit()
        response_id = response.id
    queue = '/v2/assessments/admin/review-queue'
    before = researcher_client.get(queue).json()
    assert before['items'] == [] and before['blocked_items'][0]['recoverable'] is True
    endpoint = f'/v2/content/admin/releases/{release_id}/restore-original-snapshot'
    for status in ['restored', 'already_present']:
        result = researcher_client.post(endpoint)
        assert result.status_code == 200, result.text
        assert result.json()['status'] == status
        assert 'private_answer' not in result.text
    after = researcher_client.get(queue).json()
    assert after['blocked_items'] == [] and after['items'][0]['response_id'] == response_id
    assert after['items'][0]['prompt'] == question['prompt']
    with TestingSessionLocal() as db:
        assert db.query(PrivateContentBankSnapshot).count() == 1
        assert db.query(AuditLog).filter(AuditLog.action == 'v2.content.snapshot_restored').count() == 1
        saved = db.get(AssessmentQuestionResponse, response_id)
        assert saved.answer_json == answer and saved.status == 'pending_review' and saved.is_correct is None
        assert db.get(AssessmentSession, session_id).content_release_id == release_id
        assert db.get(ContentRelease, release_id).is_active is False


def test_student_cannot_restore_snapshot(student_client):
    assert student_client.post('/v2/content/admin/releases/1/restore-original-snapshot').status_code == 403


def test_unknown_bank_is_not_replaced_by_current_release(researcher_client):
    with TestingSessionLocal() as db:
        row = ContentRelease(version='unrecoverable', checksum='f'*64)
        db.add(row)
        db.commit()
        release_id = row.id
    assert researcher_client.post(f'/v2/content/admin/releases/{release_id}/restore-original-snapshot').status_code == 409
    with TestingSessionLocal() as db:
        assert db.query(PrivateContentBankSnapshot).count() == 0


def test_restore_refuses_to_overwrite_an_existing_different_snapshot(researcher_client):
    release_id, _ = _historical_row()
    with TestingSessionLocal() as db:
        db.add(PrivateContentBankSnapshot(content_release_id=release_id, checksum=CHECKSUM, payload_json={'changed': True}))
        db.commit()
    assert researcher_client.post(f'/v2/content/admin/releases/{release_id}/restore-original-snapshot').status_code == 409
    with TestingSessionLocal() as db:
        assert db.query(PrivateContentBankSnapshot).one().payload_json == {'changed': True}


def test_restore_recomputes_full_digest_and_rejects_tampered_bundle(researcher_client, monkeypatch, tmp_path):
    release_id, release = _historical_row()
    release['questions'][0]['prompt'] = 'tampered synthetic prompt'
    (tmp_path / f'{CHECKSUM}.json.gz').write_bytes(gzip.compress(json.dumps(release).encode()))
    monkeypatch.setattr(recovery, 'RECOVERY_ROOT', tmp_path)
    assert researcher_client.post(f'/v2/content/admin/releases/{release_id}/restore-original-snapshot').status_code == 409
    with TestingSessionLocal() as db:
        assert db.query(PrivateContentBankSnapshot).count() == 0
