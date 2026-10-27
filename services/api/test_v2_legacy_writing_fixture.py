"""Synthetic immutable historical writing release for P08 regression tests.
Current 300-question candidate bank has no free-writing items.
"""
from copy import deepcopy
from hashlib import sha256
import json

from v2_content.repository import get_release


def legacy_writing_release(*question_ids: str) -> dict:
    if not question_ids:
        raise ValueError("historical question IDs required")
    release = deepcopy(get_release())
    requested = set(question_ids)
    found = set()
    for question in release["questions"]:
        if question["id"] not in requested:
            continue
        found.add(question["id"])
        question["interaction"] = "write_text"
        question["prompt"] = "اكتب الكلمة في الحقل."
        question["options"] = []
        question["private_answer"] = {
            "correct_option_ids": [],
            "rubric": {"authority": "human_supervisor", "criteria": ["وضوح الكتابة"]},
        }
        question["evidence_type"] = "word_writing"
    if found != requested:
        raise ValueError(f"missing archived questions: {requested - found}")
    encoded = json.dumps(
        [(q["id"], q["interaction"], q["private_answer"]) for q in release["questions"]],
        sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")
    checksum = sha256(encoded).hexdigest()
    release["checksum"] = checksum
    release["version"] = f"himma-v2-test-legacy-writing+{checksum[:16]}"
    return release
