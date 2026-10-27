"""Behavior parity and query-budget gates for the supervisor student list."""
from __future__ import annotations

import pytest
from sqlalchemy import event

import protected
from admin_student_projection import build_student_list_payloads
from db.adaptation_models import AdaptationDecision
from db.database import SessionLocal
from db.models import AssessmentSession, Student


def _build_cohort(db, count: int) -> list[Student]:
    first = db.query(Student).filter(Student.access_code == "STU001").one()
    students = [first]
    for index in range(1, count):
        student = Student(
            access_code=f"{700000 + index:06d}",
            name=f"طالب {index + 1}",
            grade_level=3,
            current_level=1,
            is_active=True,
        )
        db.add(student)
        students.append(student)
    db.flush()

    for index, student in enumerate(students):
        db.add(AssessmentSession(
            student_id=student.id,
            session_type="pretest",
            status="completed",
            assigned_level=1,
            assessment_attempt_no=1,
            official_for_reporting=True,
        ))
        core = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="completed",
            assigned_level=1,
        )
        db.add(core)
        db.flush()
        # Force the promotion-decision batch to participate in the query budget.
        if index == 0:
            db.add(AdaptationDecision(
                student_id=student.id,
                decision_source="automatic",
                action="promote",
                mastery_score=90,
                previous_level=1,
                new_level=2,
                valid_attempt_count=6,
                consecutive_low_count=0,
                snapshot_key="perf-budget-promotion",
                explanation={
                    "previous_session_id": core.id,
                    "journey_transition": "L1->L2",
                },
            ))
    db.commit()
    return students


@pytest.mark.parametrize("cohort_size", [1, 10, 50])
def test_student_list_query_budget_is_independent_of_cohort_size(cohort_size: int):
    db = SessionLocal()
    try:
        _build_cohort(db, cohort_size)
        engine = db.get_bind()
        statements = 0

        def count_statement(*_args, **_kwargs):
            nonlocal statements
            statements += 1

        event.listen(engine, "before_cursor_execute", count_statement)
        try:
            payloads = protected.list_students(user=None, db=db)
        finally:
            event.remove(engine, "before_cursor_execute", count_statement)

        assert len(payloads) == cohort_size
        # Student rows + sessions + grouped attempt counts + promotion decisions.
        assert statements <= 4, f"student list used {statements} SQL statements for {cohort_size} students"
    finally:
        db.close()


def test_batched_projection_matches_single_student_owner_for_early_promotion():
    db = SessionLocal()
    try:
        student = _build_cohort(db, 1)[0]

        single_payload = protected._student_payload(db, student)
        batched_payload = build_student_list_payloads(db, [student])[0]

        assert single_payload == batched_payload
        assert batched_payload["core_completed"] is True
        assert batched_payload["core_completed_items"] == 0
        assert batched_payload["posttest_eligible"] is False
    finally:
        db.close()


def test_active_reopened_core_keeps_batched_posttest_eligibility_closed():
    db = SessionLocal()
    try:
        student = _build_cohort(db, 1)[0]
        student.current_level = 3
        db.add(AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=3,
        ))
        db.commit()

        single_payload = protected._student_payload(db, student)
        batched_payload = build_student_list_payloads(db, [student])[0]

        assert single_payload == batched_payload
        assert batched_payload["core_completed"] is False
        assert batched_payload["posttest_eligible"] is False
    finally:
        db.close()
