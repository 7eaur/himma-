from datetime import datetime, timezone
from uuid import uuid4

import pytest
from conftest import TestingSessionLocal
from db.learning_models import AdaptationDecision, LessonProgressEvent, LessonQuestionResponse, LessonSession, PlacementDecisionV2, PrivateContentBankSnapshot, StudentJourney, SupportAssignment
from db.models import AuditLog, AssessmentSession, Student, User
from db.v2_reward_models import V2RewardGrant
from v2_content.importer import register_candidate_release
from v2_content.repository import get_release
from v2_rewards import reconcile_rewards, rewards_projection
from test_v2_lesson_runtime import _place_fixture


STUDENT_ID=None
USER_ID=None

@pytest.fixture(autouse=True)
def reward_fixture_ids(setup_database):
    global STUDENT_ID, USER_ID
    with TestingSessionLocal() as db:
        STUDENT_ID=db.query(Student).one().id
        USER_ID=db.query(User).one().id


def _fixture(db, *, level=1):
    release=register_candidate_release(db)
    student=db.query(Student).one()
    journey=StudentJourney(student_id=student.id,content_release_id=release.id,current_level=level,current_lesson_id=f'L{level}-01',placement_state='placed')
    db.add(journey);db.flush()
    official=AssessmentSession(
        student_id=student.id,content_release_id=release.id,
        session_type='pretest',status='completed',v2_state='completed',
        official_for_reporting=True,assigned_level=level,final_score=80,
        assessment_attempt_no=1,
    )
    db.add(official);db.flush()
    db.add(PlacementDecisionV2(
        student_id=student.id,content_release_id=release.id,
        assessment_session_id=official.id,assigned_level=level,
        reason='V2 test official placement',policy_version='test-placement',
        decided_by=USER_ID,
    ))
    db.flush()
    return student,release,journey


def _lesson(db,student,release,lesson_id='L1-01', *, video=True,gp=True,completed=True,pending=False):
    now=datetime.now(timezone.utc)
    session=LessonSession(student_id=student.id,content_release_id=release.id,lesson_id=lesson_id,
        stage='complete' if completed else 'independent_check',status='completed' if completed else 'in_progress',
        intro_seen=video,video_seen=video,video_completed_at=now if video else None,completed_at=now if completed else None)
    db.add(session);db.flush()
    for question in get_release()['questions']:
        if question.get('owner_id')!=lesson_id or question['role'] not in {'guided_practice','independent_check'}:
            continue
        if question['role']=='guided_practice' and not gp:
            continue
        db.add(LessonQuestionResponse(lesson_session_id=session.id,question_id=question['id'],role=question['role'],
            answer_json={},submit_key=str(uuid4()),status='pending_review' if pending and question['role']=='independent_check' else 'graded',
            is_correct=None if pending and question['role']=='independent_check' else False))
    db.flush();return session


def test_without_official_pretest_or_placement_even_completed_rows_award_no_stars(researcher_client):
    with TestingSessionLocal() as db:
        student,release,_=_fixture(db)
        _lesson(db,student,release)
        decision=db.query(PlacementDecisionV2).filter(
            PlacementDecisionV2.student_id==student.id,
        ).one()
        pre=db.get(AssessmentSession,decision.assessment_session_id)
        pre.official_for_reporting=False
        assert reconcile_rewards(db,student.id)=={
            'state':'placement_unverified','inserted':0,
        }
        assert db.query(V2RewardGrant).count()==0
        pre.official_for_reporting=True
        pre.assigned_level=3
        assert reconcile_rewards(db,student.id)['inserted']==0
        assert db.query(V2RewardGrant).count()==0


def test_three_real_milestones_award_once_without_v1_scores_or_accuracy_bonuses(researcher_client):
    with TestingSessionLocal() as db:
        student,release,_=_fixture(db)
        _lesson(db,student,release)
        assert reconcile_rewards(db,student.id)['inserted']==3
        assert reconcile_rewards(db,student.id)['inserted']==0
        projection=rewards_projection(db,student.id,release.id)
        assert projection['total_stars']==3 and projection['badges']==[]
        assert projection['lessons'][0]['stars']==3
        assert db.query(AuditLog).filter(AuditLog.action=='v2.reward.granted').count()==3
        db.commit()
    for _ in range(2):
        assert researcher_client.get(f'/v2/student/admin/students/{STUDENT_ID}/home').json()['rewards']['total_stars']==3
    with TestingSessionLocal() as db:
        assert db.query(V2RewardGrant).count()==3


def test_pending_reading_never_awards_completion_star_until_graded(researcher_client):
    with TestingSessionLocal() as db:
        student,release,_=_fixture(db)
        session=_lesson(db,student,release,pending=True)
        assert reconcile_rewards(db,student.id)['inserted']==2
        assert rewards_projection(db,student.id,release.id)['total_stars']==2
        for row in db.query(LessonQuestionResponse).filter(LessonQuestionResponse.lesson_session_id==session.id,LessonQuestionResponse.role=='independent_check').all():
            row.status='graded';row.is_correct=False
        assert reconcile_rewards(db,student.id)['inserted']==1
        assert reconcile_rewards(db,student.id)['inserted']==0


def test_unresolved_support_withholds_completion_without_deducting_earned_stars(researcher_client):
    with TestingSessionLocal() as db:
        student,release,_=_fixture(db);session=_lesson(db,student,release)
        support=SupportAssignment(student_id=student.id,content_release_id=release.id,lesson_session_id=session.id,
            support_id='SUP-01',focus='test',target_skill='S1',source_lesson_id='L1-01',source_level=1,support_level=1,
            mode='targeted_support',status='active',return_to={},policy_version='test')
        db.add(support)
        assert reconcile_rewards(db,student.id)['inserted']==2
        support.status='resolved'
        db.flush()
        # Ending a support detour is not independent evidence of mastery.
        assert reconcile_rewards(db,student.id)['inserted']==0
        db.add(AdaptationDecision(
            lesson_session_id=session.id,student_id=student.id,
            content_release_id=release.id,support_assignment_id=support.id,
            decision_key='support-verified-test',decision_kind='next_lesson',
            reason_code='support_check_resolved_gap',evidence_ids=[],
            explanation_json={},policy_version='test-verified-support',
        ))
        assert reconcile_rewards(db,student.id)['inserted']==1
        support.status='escalated'
        assert reconcile_rewards(db,student.id)['inserted']==0
        assert rewards_projection(db,student.id,release.id)['total_stars']==3


def test_closed_but_unmastered_support_never_awards_lesson_star_even_after_reconcile(researcher_client):
    with TestingSessionLocal() as db:
        student,release,_=_fixture(db);session=_lesson(db,student,release)
        support=SupportAssignment(
            student_id=student.id,content_release_id=release.id,lesson_session_id=session.id,
            support_id='SUP-01',focus='synthetic-gap',target_skill='S1',
            source_lesson_id='L1-01',source_level=1,support_level=1,
            mode='targeted_support',status='resolved',return_to={},policy_version='test',
        )
        db.add(support);db.flush()
        db.add(AdaptationDecision(
            lesson_session_id=session.id,student_id=student.id,content_release_id=release.id,
            support_assignment_id=support.id,decision_key='support-unmastered-test',
            decision_kind='next_lesson',
            reason_code='support_gap_unresolved_continue_without_mastery',
            evidence_ids=[],explanation_json={'skill_mastery':'not_demonstrated'},
            policy_version='test-unmastered-support',
        ))
        assert reconcile_rewards(db,student.id)['inserted']==2
        assert reconcile_rewards(db,student.id)['inserted']==0
        assert rewards_projection(db,student.id,release.id)['total_stars']==2
        assert not db.query(V2RewardGrant).filter(
            V2RewardGrant.milestone=='lesson_complete',
        ).first()


def test_support_with_verified_and_unverified_foci_stays_unrewarded(researcher_client):
    with TestingSessionLocal() as db:
        student,release,_=_fixture(db);session=_lesson(db,student,release)
        for index in (1,2):
            support=SupportAssignment(
                student_id=student.id,content_release_id=release.id,lesson_session_id=session.id,
                support_id='SUP-01',focus=f'skill-{index}',target_skill='S1',
                source_lesson_id='L1-01',source_level=1,support_level=1,
                mode='targeted_support',status='resolved',return_to={},policy_version='test',
            )
            db.add(support);db.flush()
            if index==1:
                db.add(AdaptationDecision(
                    lesson_session_id=session.id,student_id=student.id,
                    content_release_id=release.id,support_assignment_id=support.id,
                    decision_key='first-skill-proven',decision_kind='next_lesson',
                    reason_code='support_check_resolved_gap',
                    evidence_ids=[],explanation_json={},policy_version='test',
                ))
        assert reconcile_rewards(db,student.id)['inserted']==2
        assert rewards_projection(db,student.id,release.id)['total_stars']==2


def test_duplicate_sessions_and_repeated_submissions_do_not_multiply_rewards(researcher_client):
    with TestingSessionLocal() as db:
        student,release,_=_fixture(db)
        _lesson(db,student,release);_lesson(db,student,release)
        reconcile_rewards(db,student.id)
        assert db.query(V2RewardGrant).count()==3


def test_level_badge_requires_every_actual_completed_lesson_and_skips_are_not_awards(researcher_client):
    with TestingSessionLocal() as db:
        student,release,journey=_fixture(db,level=3)
        # _fixture provides the matching completed official pretest.
        for lesson in get_release()['lessons']:
            _lesson(db,student,release,lesson['id'])
        result=reconcile_rewards(db,student.id)
        projection=rewards_projection(db,student.id,release.id)
        assert result['inserted']==22 and projection['total_stars']==21
        assert [badge['asset_id'] for badge in projection['badges']]==['BDG-06']
        assert all(row['lesson_id'].startswith('L3') for row in projection['lessons'])


def test_all_three_levels_use_canonical_badges_from_one_v2_ledger(researcher_client):
    with TestingSessionLocal() as db:
        student,release,_=_fixture(db)
        for lesson in get_release()['lessons']:
            _lesson(db,student,release,lesson['id'])
        assert reconcile_rewards(db,student.id)['inserted']==60
        projection=rewards_projection(db,student.id,release.id)
        assert projection['total_stars']==57
        assert [badge['asset_id'] for badge in projection['badges']]==['BDG-04','BDG-05','BDG-06']
        assert reconcile_rewards(db,student.id)['inserted']==0


def test_missing_bank_or_metadata_does_not_fabricate_rewards_or_switch_to_current_bank(researcher_client):
    with TestingSessionLocal() as db:
        student,release,_=_fixture(db)
        _lesson(db,student,release,video=False,gp=False,completed=False)
        assert reconcile_rewards(db,student.id)['inserted']==0
        snapshot=db.get(PrivateContentBankSnapshot,release.id);snapshot.checksum='f'*64
        assert reconcile_rewards(db,student.id)=={'state':'bank_unavailable','inserted':0}
        assert db.query(V2RewardGrant).count()==0


def test_rewards_and_audit_rollback_with_the_learning_transaction(researcher_client):
    with TestingSessionLocal() as db:
        student,release,_=_fixture(db);_lesson(db,student,release);db.commit()
        assert reconcile_rewards(db,student.id)['inserted']==3
        db.rollback()
        assert db.query(V2RewardGrant).count()==0
        assert db.query(AuditLog).filter(AuditLog.action=='v2.reward.granted').count()==0
        assert reconcile_rewards(db,student.id)['inserted']==3


def test_admin_reconciliation_is_explicit_replay_safe_and_forbidden_to_student(researcher_client,student_client):
    # Separate logins use the same browser cookie jar; authenticate staff last.
    with TestingSessionLocal() as db:
        student,release,_=_fixture(db);_lesson(db,student,release);db.commit()
    assert student_client.post(f'/v2/rewards/admin/students/{STUDENT_ID}/reconcile').status_code==403
    researcher_client.post('/auth/login',json={'username':'researcher1','password':'test-only-researcher-password'})
    assert researcher_client.post(f'/v2/rewards/admin/students/{STUDENT_ID}/reconcile').json()['inserted']==3
    assert researcher_client.post(f'/v2/rewards/admin/students/{STUDENT_ID}/reconcile').json()['inserted']==0


def test_actual_video_transition_awards_one_star_in_its_own_transaction(student_client):
    with TestingSessionLocal() as db:
        _fixture(db);db.commit()
    _place_fixture()
    started_response=student_client.post('/v2/lessons/L1-01/start')
    assert started_response.status_code==200,started_response.text
    started=started_response.json()
    session=started['session']['session_id']
    assert student_client.post(f'/v2/lessons/sessions/{session}/events',json={'event_key':'intro-synthetic','event_type':'intro_complete'}).status_code==200
    event={'event_key':'video-synthetic','event_type':'video_ended','position_seconds':6,'duration_seconds':6}
    for _ in range(2):
        assert student_client.post(f'/v2/lessons/sessions/{session}/events',json=event).status_code==200
    assert student_client.get('/v2/student/home').json()['rewards']['total_stars']==1
    with TestingSessionLocal() as db:
        assert db.query(V2RewardGrant).count()==1
        assert db.query(LessonProgressEvent).count()==2


def test_real_guided_and_independent_transitions_each_award_their_milestone_once(student_client):
    from v2_content.repository import get_question
    with TestingSessionLocal() as db:
        _fixture(db);db.commit()
    _place_fixture()
    started=student_client.post('/v2/lessons/L1-01/start')
    assert started.status_code==200,started.text
    session=started.json()['session']['session_id']
    for event in [{'event_key':'intro-full-test','event_type':'intro_complete'},
                  {'event_key':'video-full-test','event_type':'video_ended','position_seconds':6,'duration_seconds':6}]:
        assert student_client.post(f'/v2/lessons/sessions/{session}/events',json=event).status_code==200
    assert student_client.get('/v2/student/home').json()['rewards']['total_stars']==1
    for index in range(8):
        current=student_client.get(f'/v2/lessons/sessions/{session}/interaction').json()['interaction']['question']
        question=get_question(current['question_id'])
        answer={'submit_key':str(uuid4()),'selected_option_ids':question['private_answer']['correct_option_ids']}
        submitted=student_client.post(f'/v2/lessons/sessions/{session}/answers',json=answer)
        assert submitted.status_code==200,submitted.text
        assert student_client.post(f'/v2/lessons/sessions/{session}/answers',json=answer).json()['status']=='replayed'
        expected=1 if index<3 else 2 if index<7 else 3
        assert student_client.get('/v2/student/home').json()['rewards']['total_stars']==expected
    with TestingSessionLocal() as db:
        assert db.query(V2RewardGrant).count()==3
        assert db.get(LessonSession,session).status=='completed'


def test_reward_totals_do_not_cross_student_or_release_and_policy_update_cannot_duplicate_key(researcher_client):
    import pytest
    from sqlalchemy.exc import IntegrityError
    with TestingSessionLocal() as db:
        student,release,_=_fixture(db);_lesson(db,student,release);reconcile_rewards(db,student.id);db.commit()
        assert rewards_projection(db,student.id+999,release.id)['total_stars']==0
        assert rewards_projection(db,student.id,release.id+999)['total_stars']==0
        original=db.query(V2RewardGrant).first()
        db.add(V2RewardGrant(student_id=original.student_id,content_release_id=original.content_release_id,
            scope_kind=original.scope_kind,scope_id=original.scope_id,milestone=original.milestone,
            stars=original.stars,policy_version='future-display-version',evidence_json={}))
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()
        assert db.query(V2RewardGrant).count()==3
