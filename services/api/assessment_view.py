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
from db.models import ContentItem, Student
from dependencies import get_current_student, get_db

router = APIRouter(prefix="/assessment-view", tags=["Assessment Student View"])


def _reference_stimulus_text(db: Session, item: ContentItem) -> str:
    """Resolve a reference-only comprehension item to its approved passage.

    The canonical assessment source intentionally stores Q25-Q29 as references
    to the reading passage that immediately precedes them.  The student payload
    must nevertheless be self-contained so a refresh or direct navigation does
    not make that passage disappear.
    """
    experience_key = (
        "pretest_experience"
        if item.kind == "pretest_question"
        else "posttest_experience"
    )
    candidates = (
        db.query(ContentItem)
        .filter(
            ContentItem.kind == item.kind,
            ContentItem.level_id == item.level_id,
            ContentItem.status == "approved",
            ContentItem.order_index < item.order_index,
        )
        .order_by(ContentItem.order_index.desc())
        .all()
    )
    for candidate in candidates:
        presentation = (candidate.template_data or {}).get(experience_key) or {}
        stimulus = presentation.get("stimulus") or {}
        text = str(stimulus.get("text") or "").strip()
        if stimulus.get("kind") == "reading" and text:
            return text
    raise HTTPException(status_code=409, detail="تعذر تحميل النص المرجعي المعتمد للسؤال")


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
    payload = assessment_student_payload(item, step)
    stimulus = payload["presentation"].get("stimulus") or {}
    if stimulus.get("kind") == "reference":
        payload["presentation"]["stimulus"] = {
            **stimulus,
            "text": _reference_stimulus_text(db, item),
        }
    return payload
