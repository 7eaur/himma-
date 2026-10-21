"""Explicit allow-list projections from the private release to learner DTOs."""

from __future__ import annotations

from typing import Any

from .contracts import AuthoringQuestion, PRIVATE_KEYS, StudentQuestion


def _all_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_keys(child)


def student_question(question: dict[str, Any]) -> dict[str, Any]:
    authoring = AuthoringQuestion.model_validate(question)
    hint = None
    if authoring.role == "guided_practice":
        hint = getattr(authoring, "hint", None)
    payload = StudentQuestion(
        question_id=authoring.id,
        owner_id=authoring.owner_id,
        role=authoring.role,
        interaction=authoring.interaction,
        prompt=authoring.prompt,
        stimulus=authoring.stimulus.model_dump(mode="json"),
        options=[option.model_dump(mode="json") for option in authoring.options],
        skill_group=authoring.skill_group,
        evidence_type=authoring.evidence_type,
        presentation=dict(authoring.student_presentation),
        hint=hint,
    ).model_dump(mode="json")
    if PRIVATE_KEYS.intersection(_all_keys(payload)):
        raise ValueError("private authoring key leaked into student DTO")
    return payload


def student_manifest(release: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "himma-v2-student-manifest/1",
        "release_version": release["version"],
        "release_checksum": release["checksum"],
        "state": release["state"],
        "counts": dict(release["counts"]),
        "levels": {
            "L1": [row["id"] for row in release["lessons"] if row["level"] == "L1"],
            "L2": [row["id"] for row in release["lessons"] if row["level"] == "L2"],
            "L3": [row["id"] for row in release["lessons"] if row["level"] == "L3"],
        },
        "supports": [row["id"] for row in release["supports"]],
        "assessment": {
            "pretest": [row["id"] for row in release["questions"] if row["role"] == "pretest"],
            "posttest": [row["id"] for row in release["questions"] if row["role"] == "posttest"],
        },
    }


def student_lesson(lesson: dict[str, Any], media: dict[str, Any]) -> dict[str, Any]:
    """Project only the reviewed fields needed by the P03 lesson shell."""
    return {
        "lesson_id": lesson["id"],
        "title": lesson["title"],
        "level": lesson["level"],
        "skill_group": lesson["skill_group"],
        "objective": lesson.get("objective"),
        "intro": {
            "title": lesson["intro"].get("title") or lesson["title"],
            "text": lesson["intro"].get("text") or "",
            "button": lesson["intro"].get("button") or "ابدأ الشرح",
        },
        "video": media,
        "practice": {
            "count": len(lesson["practice_question_ids"]),
            "first_question_id": lesson["practice_question_ids"][0],
        },
        "independent_check": {"count": len(lesson["check_question_ids"])},
    }
