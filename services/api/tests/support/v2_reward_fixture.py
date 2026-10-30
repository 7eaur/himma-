"""Local CI-only synthetic completed lesson, with no rewards pre-awarded."""
from datetime import datetime, timezone
import json
from pathlib import Path
import secrets
import sys
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from sqlalchemy.engine import make_url
from db.database import SessionLocal, SQLALCHEMY_DATABASE_URL
from db.learning_models import LessonSession, LessonQuestionResponse, PlacementDecisionV2, StudentJourney
from db.models import AssessmentSession, Student
from db.v2_reward_models import V2RewardGrant
from v2_content.importer import register_candidate_release
from v2_content.repository import get_release


def main():
    url=make_url(SQLALCHEMY_DATABASE_URL)
    if url.host not in {'localhost','127.0.0.1'} and not (url.drivername.startswith('sqlite') and str(url.database).startswith('/tmp/')):
        raise RuntimeError('Synthetic rewards fixture is restricted to a local test database')
    with SessionLocal() as db:
        release=register_candidate_release(db)
        code=None
        for _ in range(100):
            candidate=f'{secrets.randbelow(1000000):06d}'
            if not db.query(Student.id).filter(Student.access_code==candidate).first():
                code=candidate;break
        if code is None:raise RuntimeError('No unused synthetic code')
        student=Student(name=f'طالب مكافآت V2 اصطناعي {uuid4().hex[:8]}',access_code=code,grade_level=3,current_level=1)
        db.add(student);db.flush()
        db.add(StudentJourney(student_id=student.id,content_release_id=release.id,current_level=1,current_lesson_id='L1-02',placement_state='placed'))
        # A genuine V2 reward requires a matching completed, official
        # pretest and system-owned placement. Synthetic session flags alone
        # must never bypass the production academic evidence predicate.
        assessment=AssessmentSession(
            student_id=student.id,content_release_id=release.id,
            session_type='pretest',status='completed',v2_state='completed',
            official_for_reporting=True,assigned_level=1,final_score=80,
            assessment_attempt_no=1,
        )
        db.add(assessment);db.flush()
        db.add(PlacementDecisionV2(
            student_id=student.id,assessment_session_id=assessment.id,
            content_release_id=release.id,assigned_level=1,
            reason='Synthetic official pretest placement for rewards E2E',
            policy_version='test-only-verified-placement',decided_by=None,
        ))
        now=datetime.now(timezone.utc)
        lesson=LessonSession(student_id=student.id,content_release_id=release.id,lesson_id='L1-01',stage='complete',status='completed',
            intro_seen=True,video_seen=True,video_completed_at=now,completed_at=now)
        db.add(lesson);db.flush()
        for question in get_release()['questions']:
            if question.get('owner_id')=='L1-01' and question['role'] in {'guided_practice','independent_check'}:
                db.add(LessonQuestionResponse(lesson_session_id=lesson.id,question_id=question['id'],role=question['role'],
                    submit_key=str(uuid4()),answer_json={},status='graded',is_correct=True))
        db.commit()
        assert db.query(V2RewardGrant).filter(V2RewardGrant.student_id==student.id).count()==0
        print(json.dumps({'student_id':student.id,'name':student.name,'access_code':code},ensure_ascii=False))

if __name__=='__main__':main()
