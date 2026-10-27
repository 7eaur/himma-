import pytest
from conftest import TestingSessionLocal
from db.learning_models import LessonSession, LessonQuestionResponse, StudentJourney
from db.models import AssessmentSession, AuditLog, Student
from v2_content.importer import register_candidate_release
from v2_content.repository import get_release

BASE=''
STUDENT_ID=None

@pytest.fixture(autouse=True)
def account_fixture_ids(setup_database):
    global BASE, STUDENT_ID
    with TestingSessionLocal() as db:
        STUDENT_ID=db.query(Student).one().id
    BASE=f'/v2/student/admin/students/{STUDENT_ID}'



def _ready(*, complete=True):
    with TestingSessionLocal() as db:
        release=register_candidate_release(db)
        student=db.query(Student).one()
        db.add(StudentJourney(student_id=student.id,content_release_id=release.id,current_level=3,placement_state='posttest_ready'))
        db.add(AssessmentSession(student_id=student.id,session_type='pretest',status='completed',v2_state='completed',
            final_score=50,official_for_reporting=True,content_release_id=release.id))
        for lesson in get_release()['lessons']:
            if complete or lesson['id']!='L1-01':
                db.add(LessonSession(student_id=student.id,content_release_id=release.id,lesson_id=lesson['id'],status='completed',stage='complete'))
        db.commit()


def test_account_identity_never_fetches_credentials_or_v1_metrics(researcher_client):
    with TestingSessionLocal() as db:
        audit_count = db.query(AuditLog).count()
    for _ in range(2):
        response=researcher_client.get(BASE+'/account')
        assert response.status_code==200
        assert response.json()['source']=='himma_v2_account'
        assert set(response.json())=={'source','id','full_name','grade_level','status','created_at','posttest_enabled'}
        assert response.headers['cache-control']=='private, no-store'
    with TestingSessionLocal() as db:
        assert db.query(AuditLog).count()==audit_count and db.query(StudentJourney).count()==0


def test_v2_admissions_create_account_without_v1_academic_records(researcher_client):
    result=researcher_client.post('/v2/student/admin/students',json={'full_name':'طالب اصطناعي جديد','grade_level':3,'access_code':'529374'})
    assert result.status_code==201, result.text
    assert result.headers['cache-control']=='private, no-store'
    assert set(result.json())=={'source','id','access_code'}
    assert result.json()['source']=='himma_v2_account'
    assert result.json()['access_code']=='529374'
    student_id=result.json()['id']
    home=researcher_client.get(f'/v2/student/admin/students/{student_id}/home')
    assert home.status_code==200 and home.json()['current_action']['action']=='start_pretest'
    with TestingSessionLocal() as db:
        assert db.query(Student).count()==2
        assert db.query(StudentJourney).count()==0
        assert db.query(AssessmentSession).count()==0


def test_account_updates_preserve_all_academic_history_and_omit_secret(researcher_client):
    _ready()
    result=researcher_client.patch(BASE+'/account',json={'full_name':'اسم اصطناعي جديد','is_active':False})
    assert result.status_code==200 and result.json()['status']=='inactive'
    assert 'access_code' not in result.text and 'core_completed_items' not in result.text
    with TestingSessionLocal() as db:
        assert db.query(AssessmentSession).count()==1
        assert db.query(LessonSession).count()==19
        assert db.query(StudentJourney).one().placement_state=='posttest_ready'
        assert db.query(Student).one().access_code=='STU001'


def test_reveal_is_explicit_private_and_audited_without_logging_the_code(researcher_client):
    result=researcher_client.post(BASE+'/access-code/reveal')
    assert result.status_code==200 and result.json()=={'student_id':STUDENT_ID,'access_code':'STU001'}
    assert result.headers['cache-control']=='private, no-store'
    with TestingSessionLocal() as db:
        audit=db.query(AuditLog).filter(AuditLog.action=='v2.student.access_code.revealed').one()
        assert audit.action=='v2.student.access_code.revealed'
        assert 'STU001' not in (audit.details or '')


def test_code_update_does_not_return_a_secret_or_change_history(researcher_client):
    _ready()
    result=researcher_client.post(BASE+'/access-code',json={'access_code':'529374'})
    assert result.status_code==200 and '529374' not in result.text
    assert researcher_client.post(BASE+'/access-code/reveal').json()['access_code']=='529374'
    with TestingSessionLocal() as db:
        assert db.query(AssessmentSession).one().final_score==50
        assert all('529374' not in (row.details or '') for row in db.query(AuditLog).all())


def test_v2_posttest_enable_uses_actual_v2_completion_without_any_v1_activity(researcher_client):
    _ready()
    for _ in range(2):
        result=researcher_client.post(BASE+'/posttest-access',json={'enabled':True})
        assert result.status_code==200, result.text
        assert result.json()['posttest_enabled'] is True
    with TestingSessionLocal() as db:
        assert db.query(AuditLog).filter(AuditLog.action=='v2.student.posttest_access.updated').count()==1
    assert researcher_client.get(f'/v2/student/admin/students/{STUDENT_ID}/home').json()['current_action']['action']=='start_posttest'
    assert researcher_client.post(BASE+'/posttest-access',json={'enabled':False}).json()['posttest_enabled'] is False


def test_ready_label_alone_does_not_override_missing_lessons(researcher_client):
    _ready(complete=False)
    assert researcher_client.post(BASE+'/posttest-access',json={'enabled':True}).status_code==409
    with TestingSessionLocal() as db:
        assert db.query(Student).one().posttest_enabled is False


def test_orphan_pending_review_still_blocks_posttest_even_when_sessions_claim_completed(researcher_client):
    _ready()
    with TestingSessionLocal() as db:
        lesson=db.query(LessonSession).first()
        db.add(LessonQuestionResponse(lesson_session_id=lesson.id,question_id='synthetic-pending',role='independent_check',
            answer_json={},submit_key='pending',status='pending_review'))
        db.commit()
    assert researcher_client.post(BASE+'/posttest-access',json={'enabled':True}).status_code==409


def test_legacy_account_cannot_open_v2_posttest_and_archive_never_returns_code(researcher_client):
    assert researcher_client.post(BASE+'/posttest-access',json={'enabled':True}).status_code==409
    response=researcher_client.get(BASE+'/historical-account')
    assert response.status_code==200 and response.json()['source']=='himma_v1_archived_account'
    assert 'access_code' not in response.text


def test_v2_posttest_cannot_be_toggled_during_or_after_assessment(researcher_client):
    _ready()
    with TestingSessionLocal() as db:
        release=register_candidate_release(db)
        db.add(AssessmentSession(student_id=STUDENT_ID,session_type='posttest',status='in_progress',v2_state='answering',content_release_id=release.id))
        db.commit()
    for enabled in [True,False]:
        assert researcher_client.post(BASE+'/posttest-access',json={'enabled':enabled}).status_code==409


def test_student_cannot_use_staff_account_or_reveal_endpoints(student_client):
    for method,suffix,body in [('get','account',None),('get','historical-account',None),('post','access-code/reveal',None),
        ('post','access-code',{'access_code':'529374'}),('patch','account',{'is_active':False}),('post','posttest-access',{'enabled':True})]:
        assert getattr(student_client,method)(BASE+'/'+suffix,**({'json':body} if body is not None else {})).status_code==403


def test_legacy_posttest_endpoint_cannot_mutate_v2_access_flag(researcher_client):
    _ready()
    assert researcher_client.post(BASE+'/posttest-access',json={'enabled':True}).status_code==200
    blocked=researcher_client.post(f'/researcher/students/{STUDENT_ID}/posttest-access',json={'enabled':False})
    assert blocked.status_code==409
    with TestingSessionLocal() as db:
        assert db.query(Student).one().posttest_enabled is True


def test_official_pretest_from_another_bank_never_enables_v2_posttest(researcher_client):
    from db.models import ContentRelease
    _ready()
    with TestingSessionLocal() as db:
        other=ContentRelease(version='other-account-bank',checksum='a'*64)
        db.add(other);db.flush()
        db.query(AssessmentSession).one().content_release_id=other.id
        db.commit()
    assert researcher_client.post(BASE+'/posttest-access',json={'enabled':True}).status_code==409
