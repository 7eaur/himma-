"""Staff account operations shared with V2, without V1 academic projections."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from db.learning_models import StudentJourney, SupportAssignment, LessonSession, LessonQuestionResponse, AssessmentQuestionResponse
from db.models import AssessmentSession, Student, User
from dependencies import get_current_user, get_db
from protected import _audit, _ensure_unique_access_code, _generate_access_code, _student_payload, create_student
from schemas import StudentCreateRequest, StudentUpdateRequest, StudentAccessCodeUpdateRequest, StudentPosttestAccessRequest
from v2_student_readmodel import build_student_v2_home

router = APIRouter(prefix='/v2/student/admin/students', tags=['v2-student-accounts'])


@router.post('', status_code=status.HTTP_201_CREATED)
def create_account(body: StudentCreateRequest, response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Admissions, unique codes, and the Student identity are shared across versions.
    # No historical assessment or V1 learning session is created by this operation.
    student = create_student(body, user, db)
    response.headers['Cache-Control'] = 'private, no-store'
    return {'source': 'himma_v2_account', 'id': student['id'], 'access_code': student['access_code']}


def _student(db, student_id, *, lock=False):
    query = db.query(Student).filter(Student.id == student_id)
    row = (query.with_for_update() if lock else query).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail='الطالب غير موجود')
    return row


def account_payload(student):
    return {'source': 'himma_v2_account', 'id': student.id, 'full_name': student.name,
            'grade_level': student.grade_level, 'status': 'active' if student.is_active else 'inactive',
            'created_at': student.created_at, 'posttest_enabled': bool(student.posttest_enabled)}


@router.get('/{student_id}/account')
def account(student_id: int, response: Response, _user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    response.headers['Cache-Control'] = 'private, no-store'
    return account_payload(_student(db, student_id))


@router.patch('/{student_id}/account')
def update_account(student_id: int, body: StudentUpdateRequest, response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    student = _student(db, student_id, lock=True)
    changes = []
    if body.full_name is not None and student.name != body.full_name:
        student.name = body.full_name; changes.append('full_name')
    if body.is_active is not None and student.is_active != body.is_active:
        student.is_active = body.is_active; changes.append('is_active')
    if changes:
        _audit(db, actor_id=user.id, action='v2.student.account.updated', entity_type='student', entity_id=str(student.id), details={'fields': changes})
        db.commit(); db.refresh(student)
    response.headers['Cache-Control'] = 'private, no-store'
    return account_payload(student)


@router.post('/{student_id}/access-code/reveal')
def reveal_code(student_id: int, response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    student = _student(db, student_id)
    _audit(db, actor_id=user.id, action='v2.student.access_code.revealed', entity_type='student', entity_id=str(student.id), details={})
    db.commit()
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return {'student_id': student.id, 'access_code': student.access_code}


@router.post('/{student_id}/access-code')
def change_code(student_id: int, body: StudentAccessCodeUpdateRequest, response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    student = _student(db, student_id, lock=True)
    code = body.access_code or _generate_access_code(db)
    _ensure_unique_access_code(db, code, excluding_student_id=student.id)
    changed = code != student.access_code
    student.access_code = code
    _audit(db, actor_id=user.id, action='v2.student.access_code.updated', entity_type='student', entity_id=str(student.id),
           details={'mode':'manual' if body.access_code else 'generated','changed':changed})
    db.commit(); db.refresh(student)
    response.headers['Cache-Control'] = 'private, no-store'
    # A new secret is only fetched by an explicit reveal/copy, never in a profile.
    return account_payload(student)


@router.post('/{student_id}/posttest-access')
def posttest_access(student_id: int, body: StudentPosttestAccessRequest, response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    student = _student(db, student_id, lock=True)
    journey = db.query(StudentJourney).filter(StudentJourney.student_id == student.id).with_for_update().one_or_none()
    if not journey:
        raise HTTPException(status_code=409, detail='لم تبدأ رحلة V2 لهذا الطالب.')
    sessions = db.query(AssessmentSession).filter(AssessmentSession.student_id == student.id, AssessmentSession.v2_state.is_not(None)).all()
    if any(row.session_type == 'posttest' and row.status in {'completed','in_progress'} for row in sessions):
        raise HTTPException(status_code=409, detail='الاختبار البعدي V2 مكتمل أو قيد التنفيذ؛ لا يمكن تغيير إتاحته.')
    if body.enabled:
        home = build_student_v2_home(db, student)
        progress = home['progress']
        pre = home['assessments']['pretest']
        pending_support = db.query(SupportAssignment.id).filter(SupportAssignment.student_id == student.id,
            SupportAssignment.content_release_id == journey.content_release_id, SupportAssignment.status != 'resolved').first()
        pending_lesson = db.query(LessonQuestionResponse.id).join(LessonSession, LessonSession.id == LessonQuestionResponse.lesson_session_id).filter(
            LessonSession.student_id == student.id, LessonSession.content_release_id == journey.content_release_id, LessonQuestionResponse.status == 'pending_review').first()
        pending_assessment = db.query(AssessmentQuestionResponse.id).join(AssessmentSession, AssessmentSession.id == AssessmentQuestionResponse.assessment_session_id).filter(
            AssessmentSession.student_id == student.id, AssessmentSession.content_release_id == journey.content_release_id, AssessmentSession.v2_state.is_not(None), AssessmentQuestionResponse.status == 'pending_review').first()
        if (not student.is_active or journey.placement_state != 'posttest_ready' or home['data_status'] != 'ready'
            or not pre or not pre['official'] or pre['score_percent'] is None
            or not any(row.id == pre['session_id'] and row.content_release_id == journey.content_release_id for row in sessions)
            or not progress['assigned_lessons'] or progress['completed_lessons'] != progress['assigned_lessons']
            or progress['pending_review'] or pending_support or pending_lesson or pending_assessment):
            raise HTTPException(status_code=409, detail='يجب اعتماد القبلي وإكمال دروس V2 والدعم والمراجعات قبل فتح البعدي.')
    if bool(student.posttest_enabled) != body.enabled:
        student.posttest_enabled = body.enabled
        student.posttest_enabled_at = datetime.now(timezone.utc) if body.enabled else None
        student.posttest_enabled_by = user.id if body.enabled else None
        _audit(db, actor_id=user.id, action='v2.student.posttest_access.updated', entity_type='student', entity_id=str(student.id), details={'enabled':body.enabled,'release_id':journey.content_release_id})
        db.commit(); db.refresh(student)
    response.headers['Cache-Control'] = 'private, no-store'
    return account_payload(student)


@router.get('/{student_id}/historical-account')
def historical_account(student_id: int, response: Response, _user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payload = _student_payload(db, _student(db, student_id))
    response.headers['Cache-Control'] = 'private, no-store'
    fields = ('current_level','posttest_eligible','core_completed_items','core_total_items','core_completed')
    return {'source': 'himma_v1_archived_account', 'student_id': student_id, **{key: payload[key] for key in fields}}
