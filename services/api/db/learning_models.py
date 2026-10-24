"""V2 journey/session state pinned to an immutable content release."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB

from db.models import Base


def _now():
    return datetime.now(timezone.utc)


class StudentJourney(Base):
    __tablename__ = "student_journeys"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, unique=True)
    content_release_id = Column(Integer, ForeignKey("content_releases.id", ondelete="RESTRICT"), nullable=False)
    current_level = Column(Integer, nullable=False, default=1, server_default="1")
    current_lesson_id = Column(String(20), nullable=True)
    placement_state = Column(String(32), nullable=False, default="not_started", server_default="not_started")
    status = Column(String(32), nullable=False, default="active", server_default="active")
    version = Column(Integer, nullable=False, default=1, server_default="1")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("current_level BETWEEN 1 AND 3", name="ck_student_journeys_level"),
        CheckConstraint("placement_state IN ('not_started','in_progress','placed','posttest_ready','completed')", name="ck_student_journeys_placement"),
        CheckConstraint("status IN ('active','paused','completed')", name="ck_student_journeys_status"),
        CheckConstraint("version >= 1", name="ck_student_journeys_version"),
    )


class LessonSession(Base):
    __tablename__ = "lesson_sessions"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    content_release_id = Column(Integer, ForeignKey("content_releases.id", ondelete="RESTRICT"), nullable=False)
    lesson_id = Column(String(20), nullable=False)
    stage = Column(String(32), nullable=False, default="intro", server_default="intro")
    step_index = Column(Integer, nullable=False, default=0, server_default="0")
    status = Column(String(32), nullable=False, default="in_progress", server_default="in_progress")
    video_seen = Column(Boolean, nullable=False, default=False, server_default="false")
    intro_seen = Column(Boolean, nullable=False, default=False, server_default="false")
    video_position_seconds = Column(Float, nullable=False, default=0, server_default="0")
    video_duration_seconds = Column(Float, nullable=True)
    video_completed_at = Column(DateTime(timezone=True), nullable=True)
    return_to = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "stage IN ('intro','video','guided_practice','independent_check','additional_check','support_practice','support_check','waiting_review','supervisor_hold','complete')",
            name="ck_lesson_sessions_stage",
        ),
        CheckConstraint("status IN ('in_progress','waiting_review','completed','abandoned')", name="ck_lesson_sessions_status"),
        CheckConstraint("step_index >= 0", name="ck_lesson_sessions_step"),
        CheckConstraint("version >= 1", name="ck_lesson_sessions_version"),
        Index("uq_lesson_sessions_active_student", "student_id", unique=True, postgresql_where=text("status IN ('in_progress','waiting_review')"), sqlite_where=text("status IN ('in_progress','waiting_review')")),
    )


class LessonProgressEvent(Base):
    """Small idempotent event log for resumable P03 lesson transitions."""

    __tablename__ = "lesson_progress_events"

    id = Column(Integer, primary_key=True)
    lesson_session_id = Column(Integer, ForeignKey("lesson_sessions.id", ondelete="CASCADE"), nullable=False)
    event_key = Column(String(100), nullable=False)
    event_type = Column(String(40), nullable=False)
    payload_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('intro_complete','video_progress','video_ended')",
            name="ck_lesson_progress_events_type",
        ),
        UniqueConstraint("lesson_session_id", "event_key", name="uq_lesson_progress_event_key"),
        Index("ix_lesson_progress_events_session_created", "lesson_session_id", "created_at"),
    )


class LessonQuestionResponse(Base):
    __tablename__ = "lesson_question_responses"

    id = Column(Integer, primary_key=True)
    lesson_session_id = Column(Integer, ForeignKey("lesson_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(160), nullable=False)
    role = Column(String(32), nullable=False)
    answer_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    submit_key = Column(String(100), nullable=False)
    attempt_no = Column(Integer, nullable=False, default=1, server_default="1")
    status = Column(String(32), nullable=False, default="submitted", server_default="submitted")
    is_correct = Column(Boolean, nullable=True)
    hint_used = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    support_assignment_id = Column(Integer, ForeignKey("support_assignments.id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        CheckConstraint("role IN ('guided_practice','independent_check','support_check')", name="ck_lesson_responses_role"),
        CheckConstraint("status IN ('submitted','pending_review','graded')", name="ck_lesson_responses_status"),
        CheckConstraint("attempt_no >= 1", name="ck_lesson_responses_attempt"),
        UniqueConstraint("lesson_session_id", "question_id", "attempt_no", name="uq_lesson_response_question_attempt"),
        UniqueConstraint("lesson_session_id", "submit_key", name="uq_lesson_response_submit_key"),
    )


class LessonQuestionDraft(Base):
    """One server-side open-response draft per lesson question.

    Drafts are deliberately separate from attempts: autosave must never create
    evidence, consume an attempt, or move the lesson state machine.
    """

    __tablename__ = "lesson_question_drafts"

    id = Column(Integer, primary_key=True)
    lesson_session_id = Column(Integer, ForeignKey("lesson_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(160), nullable=False)
    draft_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("version >= 1", name="ck_lesson_question_drafts_version"),
        UniqueConstraint("lesson_session_id", "question_id", name="uq_lesson_question_draft"),
    )


class SupportAssignment(Base):
    """A bounded support/check detour that returns to one lesson session."""

    __tablename__ = "support_assignments"

    id = Column(Integer, primary_key=True)
    lesson_session_id = Column(Integer, ForeignKey("lesson_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    content_release_id = Column(Integer, ForeignKey("content_releases.id", ondelete="RESTRICT"), nullable=False)
    support_id = Column(String(20), nullable=False)
    focus = Column(String(80), nullable=False)
    target_skill = Column(String(10), nullable=False)
    source_lesson_id = Column(String(20), nullable=False)
    source_level = Column(Integer, nullable=False)
    support_level = Column(Integer, nullable=False)
    mode = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="active", server_default="active")
    verification_round = Column(Integer, nullable=False, default=0, server_default="0")
    practice_question_ids = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list)
    check_question_ids = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list)
    return_to = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    policy_version = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("source_level BETWEEN 1 AND 3", name="ck_support_assignments_source_level"),
        CheckConstraint("support_level BETWEEN 1 AND 3", name="ck_support_assignments_support_level"),
        CheckConstraint("mode IN ('additional_check','targeted_support')", name="ck_support_assignments_mode"),
        CheckConstraint("status IN ('active','waiting_review','resolved','escalated')", name="ck_support_assignments_status"),
        CheckConstraint("verification_round BETWEEN 0 AND 1", name="ck_support_assignments_round"),
        Index(
            "uq_support_assignments_active_session",
            "lesson_session_id",
            unique=True,
            postgresql_where=text("status IN ('active','waiting_review')"),
            sqlite_where=text("status IN ('active','waiting_review')"),
        ),
        Index("ix_support_assignments_student_status", "student_id", "status"),
    )


class SkillEvidence(Base):
    """Immutable projection of one response for policy and reporting."""

    __tablename__ = "skill_evidence"

    id = Column(Integer, primary_key=True)
    response_id = Column(Integer, ForeignKey("lesson_question_responses.id", ondelete="CASCADE"), nullable=False, unique=True)
    lesson_session_id = Column(Integer, ForeignKey("lesson_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    content_release_id = Column(Integer, ForeignKey("content_releases.id", ondelete="RESTRICT"), nullable=False)
    support_assignment_id = Column(Integer, ForeignKey("support_assignments.id", ondelete="SET NULL"), nullable=True)
    question_id = Column(String(160), nullable=False)
    source_kind = Column(String(20), nullable=False)
    role = Column(String(32), nullable=False)
    skill_group = Column(String(10), nullable=False)
    evidence_type = Column(String(80), nullable=False)
    error_focus = Column(String(80), nullable=True)
    support_focus = Column(String(80), nullable=True)
    review_status = Column(String(32), nullable=False)
    is_correct = Column(Boolean, nullable=True)
    hint_used = Column(Boolean, nullable=False, default=False, server_default="false")
    counts_for_mastery = Column(Boolean, nullable=False, default=False, server_default="false")
    policy_version = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("source_kind IN ('lesson','support')", name="ck_skill_evidence_source"),
        CheckConstraint("role IN ('guided_practice','independent_check','support_check')", name="ck_skill_evidence_role"),
        CheckConstraint("review_status IN ('pending_review','graded')", name="ck_skill_evidence_review"),
        Index("ix_skill_evidence_student_skill", "student_id", "skill_group", "created_at"),
        Index("ix_skill_evidence_session_role", "lesson_session_id", "role"),
    )


class AdaptationDecision(Base):
    """Durable and explainable result of a policy boundary evaluation."""

    __tablename__ = "adaptation_decisions_v2"

    id = Column(Integer, primary_key=True)
    lesson_session_id = Column(Integer, ForeignKey("lesson_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    content_release_id = Column(Integer, ForeignKey("content_releases.id", ondelete="RESTRICT"), nullable=False)
    support_assignment_id = Column(Integer, ForeignKey("support_assignments.id", ondelete="SET NULL"), nullable=True)
    decision_key = Column(String(120), nullable=False)
    decision_kind = Column(String(40), nullable=False)
    reason_code = Column(String(100), nullable=False)
    evidence_ids = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list)
    explanation_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    policy_version = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint(
            "decision_kind IN ('next_lesson','additional_check','targeted_support','waiting_review','supervisor_hold')",
            name="ck_adaptation_decisions_v2_kind",
        ),
        UniqueConstraint("lesson_session_id", "decision_key", name="uq_adaptation_decisions_v2_key"),
        Index("ix_adaptation_decisions_v2_student_created", "student_id", "created_at"),
    )


class AssessmentQuestionResponse(Base):
    """One immutable V2 pre/post response; open evidence stays neutral."""

    __tablename__ = "assessment_question_responses"

    id = Column(Integer, primary_key=True)
    assessment_session_id = Column(Integer, ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(160), nullable=False)
    role = Column(String(20), nullable=False)
    answer_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    submit_key = Column(String(100), nullable=False)
    status = Column(String(32), nullable=False)
    is_correct = Column(Boolean, nullable=True)
    skill_group = Column(String(10), nullable=False)
    evidence_type = Column(String(80), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_note = Column(String, nullable=True)

    __table_args__ = (
        CheckConstraint("role IN ('pretest','posttest')", name="ck_assessment_responses_role"),
        CheckConstraint("status IN ('pending_review','graded')", name="ck_assessment_responses_status"),
        UniqueConstraint("assessment_session_id", "question_id", name="uq_assessment_response_question"),
        UniqueConstraint("assessment_session_id", "submit_key", name="uq_assessment_response_submit"),
        Index("ix_assessment_responses_review", "status", "role", "created_at"),
    )


class AssessmentQuestionDraft(Base):
    __tablename__ = "assessment_question_drafts"

    id = Column(Integer, primary_key=True)
    assessment_session_id = Column(Integer, ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(160), nullable=False)
    draft_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        UniqueConstraint("assessment_session_id", "question_id", name="uq_assessment_question_draft"),
        CheckConstraint("version >= 1", name="ck_assessment_question_draft_version"),
    )


class PlacementDecisionV2(Base):
    """Audited human placement; no unapproved score threshold is encoded."""

    __tablename__ = "placement_decisions_v2"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    assessment_session_id = Column(Integer, ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    content_release_id = Column(Integer, ForeignKey("content_releases.id", ondelete="RESTRICT"), nullable=False)
    assigned_level = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    policy_version = Column(String(100), nullable=False)
    decided_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint("assigned_level BETWEEN 1 AND 3", name="ck_placement_v2_level"),
        Index("ix_placement_v2_student_created", "student_id", "created_at"),
    )


class V2LessonReviewAction(Base):
    """Append-only human decisions for V2 lesson reading and writing evidence."""
    __tablename__ = "v2_lesson_review_actions"

    id = Column(Integer, primary_key=True)
    lesson_response_id = Column(Integer, ForeignKey("lesson_question_responses.id", ondelete="CASCADE"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    action = Column(String(32), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    note = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint("action IN ('graded')", name="ck_v2_lesson_review_action_kind"),
        Index("ix_v2_lesson_review_actions_response", "lesson_response_id", "created_at"),
    )


class PrivateContentBankSnapshot(Base):
    """Internal immutable assessment bank with private answer keys; never public metadata."""
    __tablename__ = "private_content_bank_snapshots"

    content_release_id = Column(Integer, ForeignKey("content_releases.id", ondelete="RESTRICT"), primary_key=True)
    checksum = Column(String(64), nullable=False)
    payload_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
