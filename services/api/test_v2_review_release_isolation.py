"""A missing historical bank blocks its own evidence, never another learner's queue."""
from uuid import uuid4

import pytest

from conftest import TestingSessionLocal
from db.models import AssessmentSession, ContentRelease, Student
from db.learning_models import AssessmentQuestionResponse, LessonQuestionResponse, LessonSession
from v2_content.importer import register_candidate_release
from v2_content.repository import get_release


@pytest.mark.parametrize('kind', ['assessment', 'lesson'])
def test_missing_snapshot_is_visible_but_cannot_break_or_regrade_other_evidence(researcher_client, kind):
    with TestingSessionLocal() as db:
        release = register_candidate_release(db)
        missing = ContentRelease(version='missing-historical-bank', checksum='0'*64, is_immutable=True)
        db.add(missing)
        students = [db.query(Student).one(), Student(name='اصطناعي تاريخي', access_code='HIST099')]
        db.add(students[1])
        db.flush()
        role = 'pretest' if kind == 'assessment' else 'independent_check'
        q = next(q for q in get_release()['questions'] if q['role'] == role and q['interaction'] == 'read_aloud')
        response_ids = []
        for student, content in zip(students, [release, missing]):
            if kind == 'assessment':
                session = AssessmentSession(student_id=student.id, session_type='pretest', content_release_id=content.id,
                    status='in_progress', v2_state='waiting_review', v2_question_index=30)
            else:
                session = LessonSession(student_id=student.id, content_release_id=content.id, lesson_id=q['owner_id'],
                    status='waiting_review', stage='waiting_review')
            db.add(session)
            db.flush()
            if kind == 'assessment':
                row = AssessmentQuestionResponse(assessment_session_id=session.id, question_id=q['id'], role=role,
                    answer_json={}, submit_key=str(uuid4()), status='pending_review',
                    skill_group=q['skill_group'], evidence_type=q['evidence_type'])
            else:
                row = LessonQuestionResponse(lesson_session_id=session.id, question_id=q['id'], role=role,
                    answer_json={}, submit_key=str(uuid4()), status='pending_review')
            db.add(row)
            db.flush()
            response_ids.append(row.id)
        db.commit()
    endpoint = '/v2/assessments/admin/review-queue' if kind == 'assessment' else '/v2/review/lesson-queue'
    result = researcher_client.get(endpoint)
    assert result.status_code == 200, result.text
    data = result.json()
    assert [item['response_id'] for item in data['items']] == [response_ids[0]]
    assert len(data['blocked_items']) == 1
    blocked = data['blocked_items'][0]
    assert blocked['response_id'] == response_ids[1]
    assert blocked['reason'] == 'content_release_unavailable'
    assert blocked['release_version'] == 'missing-historical-bank'
    assert blocked['release_checksum'] == '0'*64
    assert data['next_offset'] is None
    for key in ('answer_json', 'audio_url', 'private_answer', 'rubric', 'storage_key'):
        assert key not in blocked
    # Mutation still resolves the original bank and fails closed.
    endpoint = (f'/v2/assessments/admin/responses/{response_ids[1]}/review' if kind == 'assessment'
                else f'/v2/review/lessons/{response_ids[1]}/decision')
    denied = researcher_client.post(endpoint, json={'is_correct': True, 'note': 'لا تغيير للدليل'})
    assert denied.status_code == 409, denied.text
    with TestingSessionLocal() as db:
        model = AssessmentQuestionResponse if kind == 'assessment' else LessonQuestionResponse
        assert all(row.status == 'pending_review' and row.is_correct is None for row in db.query(model).all())
