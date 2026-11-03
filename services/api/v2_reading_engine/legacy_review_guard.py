"""Prevent historical human review from racing native V2 speech evidence.

This is a data-scoped transition guard. Historical responses without native
jobs remain readable/recoverable until their consumers have been retired;
a response bound to *any* native job may NEVER receive a second staff decision.
The guard runs before review-claim, retry, rubric, or academic mutations.
"""
from __future__ import annotations

from typing import Literal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.v2_reading_models import V2ReadingJob


def reject_legacy_review_for_native(
    db: Session, *, kind: Literal["lesson", "assessment"], response_id: int,
) -> None:
    owner = (V2ReadingJob.lesson_response_id if kind == "lesson"
             else V2ReadingJob.assessment_response_id)
    native_job_id = db.scalar(
        select(V2ReadingJob.id).where(owner == response_id).limit(1)
    )
    if native_job_id is not None:
        # Do not reveal a transcript, provider, or score to staff manual routes.
        raise HTTPException(
            status_code=409,
            detail="هذه القراءة تُقيَّم تلقائيًا. تابع نتيجتها في متابعة القراءة الصوتية.",
        )
