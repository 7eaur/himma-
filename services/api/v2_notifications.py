"""Read-only V2 attention projection with durable, idempotent acknowledgements.

Domain rows are authoritative (including work predating this feature). Reading
never writes notifications or academic state. Existing notification storage keeps
acknowledgements in an isolated v2: namespace; V1 history remains untouched.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.learning_models import AssessmentQuestionResponse, LessonQuestionResponse, LessonSession, SupportAssignment
from db.models import AssessmentSession, Student, User
from db.notification_models import ResearcherNotification
from dependencies import get_current_user, get_db
from notification_events import _insert_notification

router = APIRouter(prefix='/v2/notifications', tags=['v2-notifications'])


def attention_items(db: Session) -> list[dict]:
    items = []
    def add(key, kind, title, message, href, student_id, created):
        items.append({'id': key, 'type': kind, 'title': title, 'message': message, 'href': href,
                      'student_id': student_id, 'created_at': created, 'is_read': False})
    for response, session, student in db.query(AssessmentQuestionResponse, AssessmentSession, Student).join(
            AssessmentSession, AssessmentSession.id == AssessmentQuestionResponse.assessment_session_id).join(
            Student, Student.id == AssessmentSession.student_id).filter(
            AssessmentQuestionResponse.status == 'pending_review', AssessmentSession.v2_state.is_not(None), Student.is_active.is_(True)).all():
        add(f'assessment:{response.id}', 'assessment_review', 'قراءة اختبار تحتاج مراجعة',
            f'قراءة اختبار للطالب {student.name} بانتظار قرار المشرف.',
            '/admin/v2-assessments', student.id, response.created_at)
    for response, session, student in db.query(LessonQuestionResponse, LessonSession, Student).join(
            LessonSession, LessonSession.id == LessonQuestionResponse.lesson_session_id).join(
            Student, Student.id == LessonSession.student_id).filter(
            LessonQuestionResponse.status == 'pending_review', Student.is_active.is_(True)).all():
        add(f'lesson:{response.id}', 'lesson_review', 'قراءة درس تحتاج مراجعة',
            f'قراءة درس للطالب {student.name} بانتظار قرار المشرف.',
            '/admin/v2-lesson-review', student.id, response.created_at)
    for session, student in db.query(AssessmentSession, Student).join(Student, Student.id == AssessmentSession.student_id).filter(
            AssessmentSession.session_type == 'pretest', AssessmentSession.v2_state == 'placement_pending_review', Student.is_active.is_(True)).all():
        add(f'placement:{session.id}', 'placement_review', 'قرار تسكين مطلوب',
            f'اكتمل تقييم الطالب {student.name} وينتظر قرار التسكين.',
            '/admin/v2-assessments', student.id, session.completed_at or session.started_at)
    for assignment, student in db.query(SupportAssignment, Student).join(Student, Student.id == SupportAssignment.student_id).filter(
            SupportAssignment.status == 'escalated', Student.is_active.is_(True)).all():
        add(f'support:{assignment.id}', 'support_escalation', 'مسار دعم يحتاج قرارًا',
            f'مسار دعم للطالب {student.name} ينتظر قرار المشرف.',
            f'/admin/students/{student.id}', student.id, assignment.updated_at)
    acknowledged = {row.dedupe_key for row in db.query(ResearcherNotification).filter(
        ResearcherNotification.dedupe_key.startswith('v2:'), ResearcherNotification.is_read.is_(True)).all()}
    for item in items:
        item['is_read'] = f"v2:{item['id']}" in acknowledged
    def timestamp(item):
        created = item['created_at']
        return created.replace(tzinfo=timezone.utc).timestamp() if created else 0
    return sorted(items, key=lambda item: (item['is_read'], -timestamp(item), item['id']))


@router.get('')
def inbox(limit: int = Query(default=24, ge=1, le=100), _user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = attention_items(db)
    return {'source': 'himma_v2_attention', 'unread_count': sum(not item['is_read'] for item in items),
            'total_count': len(items), 'items': items[:limit]}


def acknowledge(db: Session, item: dict):
    _insert_notification(db.connection(), {'dedupe_key': f"v2:{item['id']}", 'notification_type': 'v2_acknowledgement',
        'title': item['title'], 'message': '', 'href': item['href'], 'entity_type': 'v2_attention', 'entity_id': item['id'],
        'is_read': True, 'read_at': datetime.now(timezone.utc)})


@router.post('/read-all')
def read_all(_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = [item for item in attention_items(db) if not item['is_read']]
    for item in items:
        acknowledge(db, item)
    db.commit()
    return {'updated': len(items)}


@router.post('/{notification_id}/read')
def read_one(notification_id: str, _user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = next((item for item in attention_items(db) if item['id'] == notification_id), None)
    if item is None:
        # Resolved work can disappear between opening the popover and clicking.
        # No arbitrary key is inserted; the UI refreshes the authoritative inbox.
        raise HTTPException(status_code=404, detail='الإشعار لم يعد ضمن الأعمال المعلقة؛ حدّث القائمة.')
    acknowledge(db, item)
    db.commit()
    return {**item, 'is_read': True}
