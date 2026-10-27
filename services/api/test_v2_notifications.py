from conftest import TestingSessionLocal
from db.learning_models import AssessmentQuestionResponse, LessonQuestionResponse, LessonSession, SupportAssignment
from db.models import AssessmentSession, Student
from db.notification_models import ResearcherNotification
from v2_content.importer import register_candidate_release


def _pending():
    with TestingSessionLocal() as db:
        release = register_candidate_release(db)
        student = db.query(Student).one()
        assessment = AssessmentSession(student_id=student.id, session_type='pretest', v2_state='waiting_review', content_release_id=release.id)
        lesson = LessonSession(student_id=student.id, content_release_id=release.id, lesson_id='L1-01', stage='waiting_review', status='waiting_review')
        db.add_all([assessment, lesson]); db.flush()
        response = AssessmentQuestionResponse(assessment_session_id=assessment.id, question_id='synthetic-review', role='pretest',
            answer_json={'audio_storage_key':'private-secret-do-not-expose'}, submit_key='synthetic-1', status='pending_review', skill_group='S1', evidence_type='reading')
        db.add(response)
        db.add(LessonQuestionResponse(lesson_session_id=lesson.id, question_id='synthetic-lesson', role='independent_check',
            answer_json={'answer':'private-answer'}, submit_key='synthetic-2', status='pending_review'))
        db.add(ResearcherNotification(notification_type='old',title='تاريخ قديم',message='legacy',href='/admin/audio-review',dedupe_key='legacy-synthetic'))
        db.commit()
        return response.id, student.id


def test_v2_inbox_is_read_only_and_excludes_legacy_and_private_evidence(researcher_client):
    _pending()
    for _ in range(2):
        response = researcher_client.get('/v2/notifications?limit=1')
        assert response.status_code == 200
        body = response.json()
        assert body['source'] == 'himma_v2_attention' and body['unread_count'] == body['total_count'] == 2
        assert len(body['items']) == 1 and body['items'][0]['href'].startswith('/admin/v2-')
        assert 'private' not in response.text and 'legacy' not in response.text
    with TestingSessionLocal() as db:
        assert db.query(ResearcherNotification).count() == 1
        assert db.query(AssessmentQuestionResponse).one().status == 'pending_review'


def test_v2_read_ack_persists_is_idempotent_and_never_leaks_into_v1(researcher_client):
    response_id, _ = _pending()
    path = f'/v2/notifications/assessment:{response_id}/read'
    for _ in range(2):
        assert researcher_client.post(path).json()['is_read'] is True
    assert researcher_client.get('/v2/notifications').json()['unread_count'] == 1
    legacy = researcher_client.get('/researcher/notifications').json()
    assert legacy['unread_count'] == 1 and len(legacy['items']) == 1
    with TestingSessionLocal() as db:
        marker = db.query(ResearcherNotification).filter(ResearcherNotification.dedupe_key.startswith('v2:')).one()
        assert marker.read_at is not None
        assert researcher_client.post(f'/researcher/notifications/{marker.id}/read').status_code == 404
        assert db.query(AssessmentQuestionResponse).one().status == 'pending_review'


def test_read_all_only_acknowledges_current_v2_work(researcher_client):
    _pending()
    assert researcher_client.post('/v2/notifications/read-all').json()['updated'] == 2
    assert researcher_client.post('/v2/notifications/read-all').json()['updated'] == 0
    assert researcher_client.get('/v2/notifications').json()['unread_count'] == 0
    assert researcher_client.get('/researcher/notifications').json()['unread_count'] == 1
    with TestingSessionLocal() as db:
        assert db.query(ResearcherNotification).count() == 3


def test_resolved_work_disappears_without_get_mutation_or_arbitrary_read_keys(researcher_client):
    response_id, student_id = _pending()
    with TestingSessionLocal() as db:
        db.query(AssessmentQuestionResponse).one().status = 'graded'
        db.query(AssessmentQuestionResponse).one().is_correct = False
        db.commit()
    assert researcher_client.get('/v2/notifications').json()['total_count'] == 1
    for key in [f'assessment:{response_id}', 'unknown:999999']:
        assert researcher_client.post(f'/v2/notifications/{key}/read').status_code == 404
    with TestingSessionLocal() as db:
        assert db.query(ResearcherNotification).count() == 1
        db.get(Student, student_id).is_active = False; db.commit()
    assert researcher_client.get('/v2/notifications').json()['total_count'] == 0


def test_placement_and_support_escalation_appear_from_persisted_state(researcher_client):
    _pending()
    with TestingSessionLocal() as db:
        session = db.query(AssessmentSession).one(); session.v2_state = 'placement_pending_review'
        lesson = db.query(LessonSession).one()
        db.add(SupportAssignment(lesson_session_id=lesson.id, student_id=lesson.student_id, content_release_id=lesson.content_release_id,
            support_id='SUP-01', focus='synthetic', target_skill='S1', source_lesson_id='L1-01',source_level=1,support_level=1,
            mode='targeted_support', status='escalated', return_to={},policy_version='synthetic'))
        db.commit()
    items = researcher_client.get('/v2/notifications').json()['items']
    assert {item['type'] for item in items} == {'assessment_review','lesson_review','placement_review','support_escalation'}
    assert next(item['href'] for item in items if item['type']=='support_escalation').startswith('/admin/students/')


def test_student_cannot_read_or_ack_supervisor_inbox(student_client):
    for method, path in [('get','/v2/notifications'), ('post','/v2/notifications/read-all'), ('post','/v2/notifications/assessment:1/read')]:
        assert getattr(student_client, method)(path).status_code == 403
