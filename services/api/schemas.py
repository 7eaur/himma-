from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Literal, Optional
from datetime import datetime
from decimal import Decimal


class ResearcherLogin(BaseModel):
    username: str
    password: str


class StudentLogin(BaseModel):
    access_code: str


class UserResponse(BaseModel):
    id: int
    username: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class StudentResponse(BaseModel):
    id: int
    name: str
    access_code: str
    current_level: int

    model_config = ConfigDict(from_attributes=True)


class MeResponse(BaseModel):
    """Returned by /auth/me — works for both roles."""
    id: int
    role: str
    display_name: str

class AssessmentStartRequest(BaseModel):
    session_type: Literal["pretest", "posttest", "core"]

class AssessmentSessionResponse(BaseModel):
    id: int
    session_type: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class AssessmentProgressResponse(BaseModel):
    completed_items: int
    total_items: int
    has_pending_item: bool

class ContentOptionResponse(BaseModel):
    id: int
    text: str
    order_index: int

    model_config = ConfigDict(from_attributes=True)

class ContentStepResponse(BaseModel):
    id: int
    order_index: int
    prompt_text: str
    expected_reading_text: Optional[str] = None
    options: list[ContentOptionResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class ContentItemResponse(BaseModel):
    id: int
    stable_key: str
    kind: str
    interaction_type: str
    steps: list[ContentStepResponse] = Field(default_factory=list)
    template_data: Optional[dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class AttemptResponseSubmit(BaseModel):
    step_id: int
    selected_option_id: Optional[int] = None
    audio_storage_key: Optional[str] = None
    audio_file_size: Optional[int] = Field(default=None, gt=0)
    audio_mime_type: Optional[str] = None
    audio_duration_seconds: Optional[Decimal] = None

class AudioSubmissionReviewResponse(BaseModel):
    id: int
    storage_key: str
    status: str
    submitted_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class GradeAudioRequest(BaseModel):
    is_valid: bool # if false, turns into rerecord_required
    target_units: Optional[int] = Field(default=None, gt=0)
    deletions: int = Field(default=0, ge=0)
    substitutions: int = Field(default=0, ge=0)
    insertions: int = Field(default=0, ge=0)
    pronunciation_notes: Optional[str] = None
    fluency_notes: Optional[str] = None
    time_notes: Optional[str] = None

class SessionFinishResponse(BaseModel):
    id: int
    final_score: Decimal
    assigned_level: int
