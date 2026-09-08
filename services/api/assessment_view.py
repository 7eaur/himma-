"""Clean DB-only read contract for pretest/posttest student screens.

The assessment engine remains responsible for attempts, scoring and idempotency.
This router only transforms the engine's next-item selection into the canonical
student-facing payload. Legacy prompt/source text is never exposed or parsed.

The serializer itself lives in ``content_student_view`` and is reused by the
researcher content preview so preview and learner screens cannot drift.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import assessment
import schemas
from content_student_view import assessment_student_payload
from db.models import Student
from dependencies import get_current_student, get_db

router = APIRouter(prefix="/assessment-view", tags=["Assessment Student View"])


@router.get("/session/{session_id}/next", response_model=schemas.AssessmentStudentViewResponse | None)
def next_student_view(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    raw = assessment.get_next_item(session_id=session_id, db=db, student=student)
    if raw is None:
        return None
    item_id = int(raw["id"])
    step_id = int(raw["steps"][0]["id"])
    item = assessment._load_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=409, detail="تعذر تحميل محتوى السؤال")
    step = next((value for value in item.steps if value.id == step_id), None)
    if step is None:
        raise HTTPException(status_code=409, detail="تعذر تحميل جولة السؤال")
    return assessment_student_payload(item, step)
