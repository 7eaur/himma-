from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
import enum
from datetime import datetime, timezone

Base = declarative_base()


class User(Base):
    """Researcher accounts (password-based login)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String(50), default="researcher", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Student(Base):
    """Student accounts (access-code-based login)."""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    access_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)  # Pseudonym only
    current_level = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    """Immutable audit trail for security-sensitive actions."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_role = Column(String(50), nullable=False)  # "researcher" | "student"
    actor_id = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=False)
    details = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ContentKind(str, enum.Enum):
    pretest_question = "pretest_question"
    posttest_question = "posttest_question"
    core_activity = "core_activity"
    reinforcement_activity = "reinforcement_activity"

class Skill(Base):
    """Educational skills and levels."""
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    skill_key = Column(String(100), unique=True, index=True, nullable=False) # UUIDv5
    name = Column(String(100), nullable=False)
    description = Column(String)
    level_id = Column(Integer, nullable=False)
    canonical_skill_id = Column(String(100), nullable=True) # Awaiting academic taxonomy

class ContentRelease(Base):
    """Release tracking to prevent changing published content."""
    __tablename__ = "content_releases"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), unique=True, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    released_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ContentItem(Base):
    """Unified content model for pre/post tests and activities."""
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    stable_key = Column(String(100), unique=True, index=True, nullable=False)
    kind = Column(String(50), nullable=False)
    level_id = Column(Integer, nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    interaction_type = Column(String(50), nullable=False) # e.g., 'multiple_choice', 'audio_record'
    order_index = Column(Integer, nullable=False)
    version = Column(String(50), nullable=False)
    status = Column(String(50), default="draft", nullable=False)
    checksum = Column(String(64), nullable=False)
    template_data = Column(JSON().with_variant(JSONB, 'postgresql'), nullable=True) 
    
    skill = relationship("Skill")
    steps = relationship("ContentStep", back_populates="item", cascade="all, delete", order_by="ContentStep.order_index")
    assets = relationship("ContentAssetLink", back_populates="item", cascade="all, delete")

class ContentStep(Base):
    """Individual rounds within a content item."""
    __tablename__ = "content_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False)
    order_index = Column(Integer, nullable=False)
    prompt_text = Column(String, nullable=False)
    expected_reading_text = Column(String, nullable=True)
    
    item = relationship("ContentItem", back_populates="steps")
    options = relationship("ContentOption", back_populates="step", cascade="all, delete", order_by="ContentOption.order_index")
    assets = relationship("ContentAssetLink", back_populates="step", cascade="all, delete")

class ContentOption(Base):
    """Options for multiple choice or similar templates."""
    __tablename__ = "content_options"
    
    id = Column(Integer, primary_key=True, index=True)
    step_id = Column(Integer, ForeignKey("content_steps.id", ondelete="CASCADE"), nullable=False)
    text = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False, default=False)
    order_index = Column(Integer, nullable=False)
    
    step = relationship("ContentStep", back_populates="options")

class ContentAssetLink(Base):
    """Links content items or steps to manifest assets."""
    __tablename__ = "content_asset_links"
    
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("content_items.id", ondelete="CASCADE"), nullable=True)
    step_id = Column(Integer, ForeignKey("content_steps.id", ondelete="CASCADE"), nullable=True)
    manifest_asset_id = Column(String(200), nullable=False)
    asset_type = Column(String(50), nullable=False)
    usage_context = Column(String(50), nullable=True)
    
    item = relationship("ContentItem", back_populates="assets")
    step = relationship("ContentStep", back_populates="assets")

class ScoringPolicy(Base):
    """Academic scoring policies ensuring immutability when locked."""
    __tablename__ = "scoring_policies"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), unique=True, nullable=False)
    status = Column(String(50), default="draft", nullable=False) # draft, approved, locked
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    checksum = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ScoringRule(Base):
    """Specific scoring rules and rubrics tied to a policy and an item."""
    __tablename__ = "scoring_rules"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("scoring_policies.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    max_raw_score = Column(Numeric(precision=10, scale=2), nullable=False, default=1.0)
    rubric = Column(String, nullable=True)
    
    policy = relationship("ScoringPolicy")
    item = relationship("ContentItem")

class AssessmentSession(Base):
    """A single session (e.g. Pretest) for a student."""
    __tablename__ = "assessment_sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    session_type = Column(String(50), nullable=False) # pretest, posttest, core
    status = Column(String(50), nullable=False, default="in_progress")
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    final_score = Column(Numeric(precision=10, scale=4), nullable=True)
    assigned_level = Column(Integer, nullable=True)

class Attempt(Base):
    """An attempt of a ContentItem within a session."""
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("assessment_sessions.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    status = Column(String(50), nullable=False, default="in_progress")
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

class AttemptResponse(Base):
    """An answer given to a ContentStep."""
    __tablename__ = "attempt_responses"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("attempts.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("content_steps.id"), nullable=False)
    selected_option_id = Column(Integer, ForeignKey("content_options.id"), nullable=True)
    is_correct = Column(Boolean, nullable=True) # Null until graded
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class AudioSubmission(Base):
    """Audio recordings submitted for AttemptResponses."""
    __tablename__ = "audio_submissions"

    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("attempt_responses.id"), nullable=False)
    storage_key = Column(String(255), nullable=False) # MinIO key
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    duration_seconds = Column(Numeric(precision=10, scale=2), nullable=True)
    status = Column(String(50), nullable=False, default="uploaded") # uploaded, graded, rerecord_required
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class AudioReview(Base):
    """Manual grading of an audio submission."""
    __tablename__ = "audio_reviews"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("audio_submissions.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_units = Column(Integer, nullable=False)
    deletions = Column(Integer, default=0, nullable=False)
    substitutions = Column(Integer, default=0, nullable=False)
    insertions = Column(Integer, default=0, nullable=False)
    rubric_score = Column(Numeric(precision=10, scale=4), nullable=False)
    supersedes_review_id = Column(Integer, ForeignKey("audio_reviews.id"), nullable=True)
    pronunciation_notes = Column(String, nullable=True)
    fluency_notes = Column(String, nullable=True)
    time_notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
