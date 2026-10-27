"""Structured human V2 audio observation isolated from historical V1 grading.

The numeric observation never becomes an automatic pass/fail threshold.
V2 shares the original secure audio storage, not the old V1 audio grade table.
"""
from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException
from pydantic import BaseModel, Field, StringConstraints, model_validator
from sqlalchemy.orm import Session
from typing import Annotated

from db.learning_models import V2AudioRubric
from db.models import AudioSubmission


class ReadingRubricV2(BaseModel):
    target_units: int = Field(gt=0, le=1000)
    deletions: int = Field(default=0, ge=0, le=1000)
    substitutions: int = Field(default=0, ge=0, le=1000)
    insertions: int = Field(default=0, ge=0, le=1000)
    pronunciation_notes: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] = ""
    fluency_notes: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] = ""

    @model_validator(mode="after")
    def validate_counts(self):
        if self.deletions + self.substitutions > self.target_units:
            raise ValueError("الحذف والاستبدال لا يمكن أن يتجاوزا الوحدات المستهدفة")
        return self

    def observed_score(self) -> Decimal:
        """A descriptive 0..1 observation, NOT a calibrated mastery result."""
        total_errors = self.deletions + self.substitutions + self.insertions
        return max(Decimal("0"), Decimal("1") -
                   Decimal(total_errors) / Decimal(self.target_units))


def save_v2_reading_rubric(
    db: Session, *, audio: AudioSubmission, reviewer_id: int,
    is_correct: bool, rubric: ReadingRubricV2 | None,
) -> None:
    """Append a rubric for this exact reviewed audio, inside the outer grade txn.

    Old clients may omit it during the UI rollout. New reviewer screens collect
    it explicitly; no uncalibrated threshold decides the child's score.
    """
    if rubric is None:
        return
    if audio.id is None or (
        audio.lesson_response_id is None and audio.assessment_response_id is None
    ):
        raise HTTPException(status_code=409, detail="معيار القراءة مخصص لتسجيلات V2 فقط")
    previous = db.query(V2AudioRubric.id).filter(
        V2AudioRubric.audio_submission_id == audio.id,
    ).first()
    if previous:
        raise HTTPException(status_code=409, detail="التسجيل مقيم سابقًا؛ لا يُكرر التقييم")
    db.add(V2AudioRubric(
        audio_submission_id=audio.id,
        reviewer_id=reviewer_id,
        is_correct=is_correct,
        target_units=rubric.target_units,
        deletions=rubric.deletions,
        substitutions=rubric.substitutions,
        insertions=rubric.insertions,
        rubric_score=rubric.observed_score(),
        pronunciation_notes=rubric.pronunciation_notes or None,
        fluency_notes=rubric.fluency_notes or None,
        policy_version="himma-v2-reading-rubric/1-observation",
        # Explicit is_correct is supplied by the human, NEVER derived from score.
    ))
