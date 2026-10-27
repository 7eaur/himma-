"""V2 effort/1 policy. Persistence is transactional; every GET is read-only."""
from collections import defaultdict
from datetime import datetime, timezone
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from db.learning_models import AdaptationDecision, LessonQuestionResponse, LessonSession, PlacementDecisionV2, PrivateContentBankSnapshot, StudentJourney, SupportAssignment
from db.models import AuditLog, ContentRelease, Student, User
from db.v2_reward_models import V2RewardGrant
from dependencies import get_current_user, get_db
from reward_catalog import badge_entry_for_level, REWARD_CATALOG_VERSION

POLICY = 'himma-v2-effort/1'
LABELS = {'intro_video':'أكملت التمهيد والفيديو','guided_practice':'أكملت التدريب','lesson_complete':'أكملت الدرس'}
router = APIRouter(prefix='/v2/rewards', tags=['v2-rewards'])


def _grant(db, *, student_id, release_id, scope_kind, scope_id, milestone, session_id, evidence, actor_role, actor_id):
    values = dict(student_id=student_id,content_release_id=release_id,scope_kind=scope_kind,scope_id=scope_id,
                  milestone=milestone,stars=1 if scope_kind=='lesson' else 0,lesson_session_id=session_id,
                  policy_version=POLICY,evidence_json=evidence,created_at=datetime.now(timezone.utc))
    insert = pg_insert if db.bind.dialect.name == 'postgresql' else sqlite_insert
    inserted = db.execute(insert(V2RewardGrant).values(**values).on_conflict_do_nothing(
        index_elements=['student_id','content_release_id','scope_kind','scope_id','milestone']).returning(V2RewardGrant.id)).scalar_one_or_none()
    if inserted is not None:
        db.add(AuditLog(actor_role=actor_role,actor_id=actor_id,action='v2.reward.granted',entity_type='v2_reward_grant',entity_id=str(inserted),
            details=json.dumps({'policy':POLICY,'release_id':release_id,'scope':scope_id,'milestone':milestone})))
    return int(inserted is not None)


def reconcile_rewards(db: Session, student_id: int, *, actor_role='student', actor_id=None, lesson_session_id=None) -> dict:
    """Insert only independently proven milestones; caller owns transaction/lock.

    The bank snapshot pinned to this journey owns its lesson/question identities.
    Missing history never becomes a current-bank assumption or a fabricated star.
    """
    db.flush()
    journey = db.query(StudentJourney).filter(StudentJourney.student_id==student_id).one_or_none()
    if not journey or journey.placement_state not in {'placed','posttest_ready','completed'}:
        return {'state':'no_placed_journey','inserted':0}
    release = db.get(ContentRelease,journey.content_release_id)
    snapshot = db.get(PrivateContentBankSnapshot,journey.content_release_id)
    bank = snapshot.payload_json if snapshot else None
    if (not release or not snapshot or snapshot.checksum!=release.checksum or not isinstance(bank,dict)
        or bank.get('checksum')!=release.checksum or bank.get('version')!=release.version
        or not isinstance(bank.get('lessons'),list) or not isinstance(bank.get('questions'),list)):
        return {'state':'bank_unavailable','inserted':0}
    lessons = {row['id']:row for row in bank['lessons']}
    sessions = db.query(LessonSession).filter(LessonSession.student_id==student_id,LessonSession.content_release_id==release.id).order_by(LessonSession.id).all()
    placement = db.query(PlacementDecisionV2).filter(PlacementDecisionV2.student_id==student_id,PlacementDecisionV2.content_release_id==release.id).order_by(PlacementDecisionV2.id.desc()).first()
    starting_level = placement.assigned_level if placement else min([journey.current_level]+[
        int(lessons[row.lesson_id]['level'][1]) for row in sessions if row.status=='completed' and row.lesson_id in lessons])
    rows = defaultdict(list)
    for row in db.query(LessonQuestionResponse).join(LessonSession,LessonSession.id==LessonQuestionResponse.lesson_session_id).filter(
            LessonSession.student_id==student_id,LessonSession.content_release_id==release.id).all():
        rows[row.lesson_session_id].append(row)
    unresolved = {session_id for session_id, in db.query(SupportAssignment.lesson_session_id).filter(
        SupportAssignment.student_id==student_id,SupportAssignment.content_release_id==release.id,SupportAssignment.status!='resolved').all()}
    unresolved_mastery_sessions = {session_id for session_id, in db.query(AdaptationDecision.lesson_session_id).filter(
        AdaptationDecision.student_id == student_id,
        AdaptationDecision.content_release_id == release.id,
        AdaptationDecision.reason_code == 'support_gap_unresolved_continue_without_mastery',
    ).distinct().all()}
    questions = defaultdict(lambda: defaultdict(set))
    for question in bank['questions']:
        questions[question.get('owner_id')][question['role']].add(question['id'])
    inserted = 0
    for session in sessions:
        if lesson_session_id is not None and session.id != lesson_session_id:
            continue
        lesson = lessons.get(session.lesson_id)
        if not lesson or int(lesson['level'][1])<starting_level:
            continue
        evidence = rows[session.id]
        milestones = []
        if session.intro_seen and session.video_seen and session.video_completed_at:
            milestones.append(('intro_video',{'session_id':session.id,'video_completed_at':session.video_completed_at.isoformat()}))
        gp = questions[session.lesson_id]['guided_practice']
        gp_saved = {row.question_id for row in evidence if row.role=='guided_practice'}
        if gp and gp<=gp_saved and session.stage not in {'intro','video','guided_practice'}:
            milestones.append(('guided_practice',{'session_id':session.id,'question_count':len(gp)}))
        ic = questions[session.lesson_id]['independent_check']
        ic_graded = {row.question_id for row in evidence if row.role=='independent_check' and row.status=='graded' and row.is_correct is not None}
        pending_ic = any(row.role=='independent_check' and row.status=='pending_review' for row in evidence)
        if (session.status=='completed' and session.stage=='complete' and session.completed_at and ic and ic<=ic_graded
            and not pending_ic and session.id not in unresolved
            and session.id not in unresolved_mastery_sessions):
            milestones.append(('lesson_complete',{'session_id':session.id,'question_count':len(ic),'completed_at':session.completed_at.isoformat()}))
        for milestone, proof in milestones:
            inserted += _grant(db,student_id=student_id,release_id=release.id,scope_kind='lesson',scope_id=session.lesson_id,
                milestone=milestone,session_id=session.id,evidence={**proof,'lesson_title':lesson['title']},actor_role=actor_role,actor_id=actor_id or student_id)
    completed_ids = {scope for scope, in db.query(V2RewardGrant.scope_id).filter(V2RewardGrant.student_id==student_id,
        V2RewardGrant.content_release_id==release.id,V2RewardGrant.milestone=='lesson_complete').all()}
    for level in (1,2,3):
        required = {lesson['id'] for lesson in lessons.values() if lesson['level']==f'L{level}'}
        if level>=starting_level and required and required<=completed_ids:
            inserted += _grant(db,student_id=student_id,release_id=release.id,scope_kind='level',scope_id=f'L{level}',
                milestone='level_complete',session_id=None,evidence={'lesson_ids':sorted(required)},actor_role=actor_role,actor_id=actor_id or student_id)
    return {'state':'ready','inserted':inserted}


def rewards_projection(db: Session, student_id: int, release_id: int | None) -> dict:
    rows = db.query(V2RewardGrant).filter(V2RewardGrant.student_id==student_id,V2RewardGrant.content_release_id==release_id).order_by(V2RewardGrant.id).all() if release_id else []
    badges = []
    lessons = defaultdict(lambda: {'stars':0,'milestones':[],'title':'درسي'})
    for row in rows:
        if row.scope_kind=='lesson':
            lessons[row.scope_id]['stars']+=row.stars
            lessons[row.scope_id]['title']=row.evidence_json.get('lesson_title') or 'درسي'
            lessons[row.scope_id]['milestones'].append({'key':row.milestone,'label':LABELS[row.milestone]})
        else:
            badge=badge_entry_for_level(int(row.scope_id[1]))
            badges.append({'id':row.id,'key':f'v2:{row.scope_id}:learned','label':badge.label,'asset_id':badge.asset_id,
                'asset_path':badge.asset_path,'catalog_version':REWARD_CATALOG_VERSION})
    return {'state':'ready','source':'himma_v2_reward_ledger','policy_version':POLICY,'release_id':release_id,
            'total_stars':sum(row.stars for row in rows),'badges':badges,
            'lessons':[{'lesson_id':lesson_id,**value} for lesson_id,value in sorted(lessons.items())]}


@router.post('/admin/students/{student_id}/reconcile')
def reconcile_student(student_id: int, user: User=Depends(get_current_user),db: Session=Depends(get_db)):
    student=db.query(Student).filter(Student.id==student_id).with_for_update().one_or_none()
    if not student:
        raise HTTPException(status_code=404,detail='الطالب غير موجود')
    result=reconcile_rewards(db,student_id,actor_role='researcher',actor_id=user.id)
    if result['state']=='bank_unavailable':
        raise HTTPException(status_code=409,detail='البنك الأصلي غير متاح؛ لم تُمنح نجوم من افتراضات.')
    db.commit()
    return result
