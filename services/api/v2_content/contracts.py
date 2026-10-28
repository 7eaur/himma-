"""Typed authoring and learner-safe contracts for the Himma V2 bank."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


Interaction = Literal[
    "choose_one",
    "listen_choose_one",
    "choose_image",
    "sequence",
    "build_word",
    "read_aloud",
]
QuestionRole = Literal[
    "guided_practice",
    "independent_check",
    "support_check",
    "pretest",
    "posttest",
]
MediaKind = Literal["audio", "image", "video"]


class AuthoringModel(BaseModel):
    """Preserve reviewed authoring metadata without exposing it by default."""

    model_config = ConfigDict(extra="allow")


class MediaReference(AuthoringModel):
    media_id: str = Field(min_length=1, max_length=160)
    kind: MediaKind


class Stimulus(AuthoringModel):
    text: str | None = None
    media: list[MediaReference] = Field(default_factory=list)


class QuestionOption(AuthoringModel):
    id: str = Field(min_length=1, max_length=40)
    text: str | None = None
    media: list[MediaReference] = Field(default_factory=list)


class PrivateAnswer(AuthoringModel):
    correct_option_ids: list[str] = Field(default_factory=list)
    accepted_option_orders: list[list[str]] = Field(default_factory=list)
    rubric: dict[str, Any] | None = None


class AuthoringQuestion(AuthoringModel):
    id: str = Field(min_length=1, max_length=160)
    owner_id: str | None = None
    role: QuestionRole
    interaction: Interaction
    prompt: str = Field(min_length=1)
    stimulus: Stimulus
    options: list[QuestionOption]
    private_answer: PrivateAnswer
    skill_group: str = Field(pattern=r"^S(?:[1-9]|1[0-3])$")
    evidence_type: str = Field(min_length=1)
    student_presentation: dict[str, Any]

    @model_validator(mode="after")
    def validate_interaction_contract(self):
        option_ids = [option.id for option in self.options]
        if len(option_ids) != len(set(option_ids)):
            raise ValueError("question option ids must be unique")

        choice_types = {
            "choose_one",
            "listen_choose_one",
            "choose_image",
            "sequence",
            "build_word",
        }
        if self.interaction in choice_types:
            if not self.options:
                raise ValueError("choice/order interactions require options")
            answer_ids = self.private_answer.correct_option_ids
            if not answer_ids or any(value not in option_ids for value in answer_ids):
                raise ValueError("private answer must reference existing options")
            if self.interaction in {"sequence", "build_word"}:
                expected = set(option_ids)
                for ordering in [answer_ids, *self.private_answer.accepted_option_orders]:
                    if (len(ordering) != len(option_ids) or len(set(ordering)) != len(ordering)
                            or set(ordering) != expected):
                        raise ValueError("ordered answer must use every tile exactly once")
        else:
            if self.options or self.private_answer.correct_option_ids:
                raise ValueError("reading interactions cannot expose choice answers")
            if not self.private_answer.rubric:
                raise ValueError("reading interactions require a private review rubric")
        return self


class AuthoringLesson(AuthoringModel):
    id: str = Field(pattern=r"^L[1-3]-\d{2}$")
    title: str = Field(min_length=1)
    level: str = Field(pattern=r"^L[1-3]$")
    skill_group: str = Field(pattern=r"^S(?:[1-9]|1[0-3])$")
    intro: dict[str, Any]
    video_media_id: str
    practice_question_ids: list[str] = Field(min_length=3, max_length=4)
    check_question_ids: list[str] = Field(min_length=3, max_length=4)
    linked_support: str | None = None


class AuthoringSupport(AuthoringModel):
    id: str = Field(pattern=r"^SUP-\d{2}$")
    title: str = Field(min_length=1)
    target_skill: str = Field(pattern=r"^S(?:[1-9]|1[0-3])$")
    linked_lessons: list[str] = Field(min_length=1)
    focus: list[str] = Field(min_length=1)
    practice_ids: list[str] = Field(min_length=1)
    check_ids: list[str] = Field(min_length=1)
    focus_item_map: dict[str, dict[str, Any]]
    video_media_id: str | None = None


class AuthoringMedia(AuthoringModel):
    id: str = Field(min_length=1, max_length=160)
    kind: MediaKind | None = None
    type: MediaKind | None = None
    status: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_kind(self):
        resolved = self.kind or self.type
        if resolved not in {"audio", "image", "video"}:
            raise ValueError("media kind/type is required")
        if self.kind and self.type and self.kind != self.type:
            raise ValueError("media kind and type disagree")
        self.kind = resolved
        self.type = resolved
        return self


class StudentMediaReference(BaseModel):
    media_id: str
    kind: MediaKind


class StudentStimulus(BaseModel):
    text: str | None
    media: list[StudentMediaReference]


class StudentOption(BaseModel):
    id: str
    text: str | None
    media: list[StudentMediaReference]


class StudentQuestion(BaseModel):
    question_id: str
    owner_id: str | None
    role: QuestionRole
    interaction: Interaction
    prompt: str
    stimulus: StudentStimulus
    options: list[StudentOption]
    skill_group: str
    evidence_type: str
    presentation: dict[str, Any]
    hint: str | None = None


PRIVATE_KEYS = {
    "private_answer",
    "correct_option_ids",
    "rubric",
    "reading_reference",
    "origin_v1",
    "source_v1_id",
    "error_focus",
    "writing_scoring_policy",
    "display_scoring_policy",
    "notes",
    "technical_gaps",
    "media_qa",
    "content_qa_note",
}
