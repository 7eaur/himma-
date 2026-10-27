"""Compile the four reviewed authoring banks into one immutable private release."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .contracts import (
    AuthoringLesson,
    AuthoringMedia,
    AuthoringQuestion,
    AuthoringSupport,
)
from .adaptation_mapping import EXPLICIT_HOLD_QUESTION_IDS, resolve_question_focus


REPO_ROOT = Path(__file__).resolve().parents[3]
BANK_ROOT = REPO_ROOT / "docs" / "v2" / "content-bank"
BANK_FILES = (
    "L1_AUTHORING_BANK_DRAFT.json",
    "L2_AUTHORING_BANK_DRAFT.json",
    "L3_AUTHORING_BANK_DRAFT.json",
    "ASSESSMENT_PRE_POST_DRAFT.json",
)
RELEASE_SCHEMA = "himma-v2-private-release/1"
EXPECTED_INTERACTIONS = {
    "choose_one": 107,
    "listen_choose_one": 52,
    "sequence": 57,
    "build_word": 18,
    "choose_image": 4,
    "read_aloud": 62,
}
EXPECTED_ROLES = {
    "guided_practice": 119,
    "independent_check": 75,
    "support_check": 46,
    "pretest": 30,
    "posttest": 30,
}
ALLOWED_MEDIA_CONFLICTS = {"label", "review"}
EXPECTED_LEVELS = {"L1": 6, "L2": 6, "L3": 7}
EXPECTED_MEDIA_KINDS = {"audio": 47, "image": 23, "video": 19}
EXPECTED_SKILLS = {f"S{number}" for number in range(1, 14)}
EXPECTED_SOURCE_METADATA = {
    "L1_AUTHORING_BANK_DRAFT.json": ("himma-v2-authoring/0.3-draft", "content_draft_not_published"),
    "L2_AUTHORING_BANK_DRAFT.json": ("himma-v2-authoring/0.3-draft", "draft_no_runtime_no_publish"),
    "L3_AUTHORING_BANK_DRAFT.json": ("himma-v2-authoring/0.3-draft", "draft_no_publish"),
    "ASSESSMENT_PRE_POST_DRAFT.json": ("himma-v2-assessment-authoring/0.1-draft", "draft_not_approved_not_published"),
}


class ContentBankError(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _load_documents(bank_root: Path) -> list[dict[str, Any]]:
    documents = []
    for name in BANK_FILES:
        path = bank_root / name
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ContentBankError(f"cannot read authoring bank {name}") from exc
        document["_source_file"] = name
        documents.append(document)
    return documents


def _merge_media(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for raw in rows:
        media = AuthoringMedia.model_validate(raw).model_dump(mode="json", exclude_none=True)
        current = merged.setdefault(media["id"], {"id": media["id"]})
        for key, value in media.items():
            if key == "id" or value in (None, "", [], {}):
                continue
            previous = current.get(key)
            if previous not in (None, "", [], {}) and previous != value and key not in ALLOWED_MEDIA_CONFLICTS:
                raise ContentBankError(f"conflicting media definition {media['id']} field={key}")
            if previous in (None, "", [], {}) or key == "label":
                current[key] = value
    return [merged[key] for key in sorted(merged)]


def _assert_unique(rows: list[dict[str, Any]], label: str) -> None:
    ids = [str(row.get("id") or "") for row in rows]
    if not all(ids) or len(ids) != len(set(ids)):
        raise ContentBankError(f"{label} ids must be present and unique")


def _media_references(question: AuthoringQuestion) -> list[str]:
    refs = [item.media_id for item in question.stimulus.media]
    for option in question.options:
        refs.extend(item.media_id for item in option.media)
    extra = getattr(question, "media_ids", None) or []
    refs.extend(str(value) for value in extra)
    return refs


def compile_release(bank_root: Path = BANK_ROOT) -> dict[str, Any]:
    documents = _load_documents(bank_root)
    lessons_raw: list[dict[str, Any]] = []
    supports_raw: list[dict[str, Any]] = []
    questions_raw: list[dict[str, Any]] = []
    media_raw: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []

    for document in documents:
        source_file = document.pop("_source_file")
        expected_schema, expected_status = EXPECTED_SOURCE_METADATA[source_file]
        if (document.get("schema_version"), document.get("status")) != (expected_schema, expected_status):
            raise ContentBankError(f"unexpected source metadata for {source_file}")
        sources.append({
            "file": source_file,
            "schema_version": document.get("schema_version"),
            "status": document.get("status"),
            "sha256": sha256(_canonical(document)).hexdigest(),
        })
        lessons_raw.extend(document.get("lessons") or [])
        supports_raw.extend(document.get("supports") or [])
        questions_raw.extend(document.get("questions") or [])
        questions_raw.extend(document.get("pretest") or [])
        questions_raw.extend(document.get("posttest") or [])
        media_raw.extend(document.get("media") or [])

    _assert_unique(lessons_raw, "lesson")
    _assert_unique(supports_raw, "support")
    _assert_unique(questions_raw, "question")

    lessons = [AuthoringLesson.model_validate(row) for row in lessons_raw]
    supports = [AuthoringSupport.model_validate(row) for row in supports_raw]
    questions = [AuthoringQuestion.model_validate(row) for row in questions_raw]
    media = _merge_media(media_raw)

    if (len(lessons), len(supports), len(questions), len(media)) != (19, 12, 300, 89):
        raise ContentBankError("expected 19 lessons, 12 supports, 300 questions and 89 media assets")

    level_counts = {level: sum(lesson.level == level for lesson in lessons) for level in EXPECTED_LEVELS}
    media_kind_counts = {kind: sum(item["kind"] == kind for item in media) for kind in EXPECTED_MEDIA_KINDS}
    skills = {question.skill_group for question in questions} | {lesson.skill_group for lesson in lessons} | {support.target_skill for support in supports}
    if level_counts != EXPECTED_LEVELS or media_kind_counts != EXPECTED_MEDIA_KINDS or skills != EXPECTED_SKILLS:
        raise ContentBankError("level, skill or media-kind totals do not match the approved baseline")

    interactions: dict[str, int] = {}
    roles: dict[str, int] = {}
    for question in questions:
        interactions[question.interaction] = interactions.get(question.interaction, 0) + 1
        roles[question.role] = roles.get(question.role, 0) + 1
    if interactions != EXPECTED_INTERACTIONS or roles != EXPECTED_ROLES:
        raise ContentBankError("question interaction/role totals do not match the approved baseline")

    question_ids = {question.id for question in questions}
    questions_by_id = {question.id: question for question in questions}
    lesson_ids = {lesson.id for lesson in lessons}
    support_ids = {support.id for support in supports}
    media_ids = {item["id"] for item in media}
    referenced_learning_questions: set[str] = set()

    for lesson in lessons:
        referenced = lesson.practice_question_ids + lesson.check_question_ids
        if any(value not in question_ids for value in referenced):
            raise ContentBankError(f"lesson {lesson.id} references an unknown question")
        if lesson.video_media_id not in media_ids:
            raise ContentBankError(f"lesson {lesson.id} references an unknown video")
        if lesson.linked_support and lesson.linked_support not in support_ids:
            raise ContentBankError(f"lesson {lesson.id} references an unknown support")
        for question_id in lesson.practice_question_ids:
            question = questions_by_id[question_id]
            if question.owner_id != lesson.id or question.role != "guided_practice":
                raise ContentBankError(f"lesson {lesson.id} has an invalid practice question contract")
        for question_id in lesson.check_question_ids:
            question = questions_by_id[question_id]
            if question.owner_id != lesson.id or question.role != "independent_check":
                raise ContentBankError(f"lesson {lesson.id} has an invalid check question contract")
        referenced_learning_questions.update(referenced)

    for support in supports:
        if any(value not in lesson_ids for value in support.linked_lessons):
            raise ContentBankError(f"support {support.id} references an unknown lesson")
        if any(value not in question_ids for value in support.practice_ids + support.check_ids):
            raise ContentBankError(f"support {support.id} references an unknown question")
        if set(support.focus_item_map) != set(support.focus):
            raise ContentBankError(f"support {support.id} focus map is incomplete")
        for focus, mapping in support.focus_item_map.items():
            mapped = list(mapping.get("practice_ids") or []) + list(mapping.get("check_ids") or [])
            if any(value not in question_ids for value in mapped):
                raise ContentBankError(f"support {support.id} focus {focus} references unknown questions")
        for question_id in support.practice_ids:
            question = questions_by_id[question_id]
            if question.owner_id != support.id or question.role != "guided_practice":
                raise ContentBankError(f"support {support.id} has an invalid practice question contract")
        for question_id in support.check_ids:
            question = questions_by_id[question_id]
            if question.owner_id != support.id or question.role != "support_check":
                raise ContentBankError(f"support {support.id} has an invalid check question contract")
        referenced_learning_questions.update(support.practice_ids + support.check_ids)

    for question in questions:
        if any(value not in media_ids for value in _media_references(question)):
            raise ContentBankError(f"question {question.id} references unknown media")
        if question.owner_id and question.owner_id not in lesson_ids | support_ids:
            raise ContentBankError(f"question {question.id} has an unknown owner")

    support_by_lesson = {
        lesson_id: support.model_dump(mode="json")
        for support in supports
        for lesson_id in support.linked_lessons
    }
    mapping_holds = set()
    for question in questions:
        if question.role != "independent_check":
            continue
        support = support_by_lesson.get(question.owner_id or "")
        if not support or resolve_question_focus(question.model_dump(mode="json"), support) is None:
            mapping_holds.add(question.id)
    if mapping_holds != EXPLICIT_HOLD_QUESTION_IDS:
        raise ContentBankError(
            f"adaptation mapping must be total or explicitly held: {sorted(mapping_holds)}"
        )

    authored_learning_questions = {question.id for question in questions if question.role not in {"pretest", "posttest"}}
    if referenced_learning_questions != authored_learning_questions:
        raise ContentBankError("every learning question must be referenced exactly by its lesson/support contract")
    if any(question.owner_id for question in questions if question.role in {"pretest", "posttest"}):
        raise ContentBankError("assessment questions cannot be owned by a lesson/support")

    payload = {
        "schema_version": RELEASE_SCHEMA,
        "state": "candidate_not_approved",
        "sources": sorted(sources, key=lambda row: row["file"]),
        "counts": {
            "lessons": len(lessons),
            "supports": len(supports),
            "questions": len(questions),
            "media": len(media),
            "levels": level_counts,
            "media_kinds": media_kind_counts,
            "skills": len(skills),
            "interactions": interactions,
            "roles": roles,
        },
        "lessons": [row.model_dump(mode="json") for row in lessons],
        "supports": [row.model_dump(mode="json") for row in supports],
        "questions": [row.model_dump(mode="json") for row in questions],
        "media": media,
    }
    checksum = sha256(_canonical(payload)).hexdigest()
    release = deepcopy(payload)
    release["checksum"] = checksum
    release["version"] = f"himma-v2-authoring-0.3-draft+{checksum[:12]}"
    return release


def main() -> None:
    release = compile_release()
    print(json.dumps({
        "version": release["version"],
        "checksum": release["checksum"],
        "state": release["state"],
        "counts": release["counts"],
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
