"""Compile all approved Himma sources into ONE canonical release contract.

This module is deliberately DB-free.  Historical source files are migration
inputs only.  The output is a complete current contract validated before a
publisher may touch PostgreSQL.  No runtime request imports this module.
"""
from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from content_approval_contract_2026_09_08 import (
    CONTEXT_INTROS,
    CRITERIA,
    INTERACTION_OVERRIDES,
    ITEM_MEDIA,
    LAYOUT_HINTS,
    LEARNING_QUESTIONS,
    LEARNING_ROUND_QUESTIONS,
    LEARNING_ROUND_STIMULI,
    OPTION_CONTRACTS,
    POSTTEST_QUESTIONS,
    POSTTEST_STIMULUS_OVERRIDES,
    PRETEST_QUESTIONS,
    PRETEST_STIMULUS_OVERRIDES,
    READING_TEXTS,
    STEP_MEDIA,
    SUPPRESS_ITEM_MEDIA,
    TIMED_WORD_SELECTIONS,
    VERSION,
)
from content_option_lifecycle import visible_key

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "packages" / "content" / "src"
BASE = CONTENT / "catalog.json"
PRETEST = CONTENT / "pretest_experience_2026_09_01.json"
STUDENT_V2 = CONTENT / "student_experience_v2.json"
REIN_V1 = CONTENT / "reinforcement_additions_v1.json"
REIN_V2 = CONTENT / "reinforcement_additions_v2.json"

READ = {"read_aloud", "timed_read_aloud"}
ORDER = {"sequence", "memory_sequence", "path_sequence", "build_word"}

V1_SKILLS = {
    "L1-REIN-06":"sound_symbol_mapping", "L1-REIN-07":"letter_form_recognition",
    "L1-REIN-08":"final_sound_isolation", "L1-REIN-09":"print_concepts",
    "L1-REIN-10":"visual_memory", "L1-REIN-11":"visual_motor_direction",
    "L1-REIN-12":"logical_sequence", "L2-REIN-06":"short_vowels",
    "L2-REIN-07":"syllable_reading", "L2-REIN-08":"long_vowels",
    "L2-REIN-09":"shadda_word_reading", "L2-REIN-10":"tanween",
    "L2-REIN-11":"sentence_reading", "L3-REIN-06":"word_accuracy",
    "L3-REIN-07":"timed_word_fluency", "L3-REIN-08":"timed_passage_fluency",
    "L3-REIN-09":"vocabulary", "L3-REIN-10":"event_sequence",
}
V2_SKILLS = {"L3-REIN-11":"literal_comprehension", "L3-REIN-12":"sentence_building"}


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _clean_parts(value: str) -> list[str]:
    return [part.strip(" .") for part in re.split(r"[،/]", value) if part.strip(" .")]


def _legacy_options(interaction: str, skill_name: str, source_text: str) -> list[str]:
    """Migration-only extraction for unchanged legacy rounds.

    Known ambiguous/changed rounds are replaced later by structured approval
    contracts.  The compiled output never exposes this source string.
    """
    for label in ("الخيارات:", "الصور:"):
        if label in source_text:
            return _clean_parts(source_text.split(label, 1)[1].strip())
    if source_text.startswith("العناصر:"):
        values = source_text.split("التعليمات:", 1)[0].split(":", 1)[1]
        return _clean_parts(values)
    for label in ("المقاطع:", "الحروف:"):
        if label in source_text:
            suffix = source_text.split(label, 1)[1]
            suffix = re.split(r"\.\s*(?:كوّن|كون)", suffix, maxsplit=1)[0]
            return _clean_parts(suffix)
    if interaction in ORDER:
        if ":" in source_text:
            prefix, suffix = source_text.split(":", 1)
            if "=" in prefix or interaction == "build_word":
                return _clean_parts(suffix)
        if "؛" in source_text:
            return [part.strip(" .") for part in source_text.split("؛") if part.strip(" .")]
        if "+" in source_text:
            return [part.strip() for part in source_text.split("=", 1)[0].split("+") if part.strip()]
        return _clean_parts(source_text)
    if "؛" in source_text:
        return _clean_parts(source_text.split("؛", 1)[1])
    if "؟" in source_text:
        return _clean_parts(source_text.split("؟", 1)[1])
    if ". " in source_text and interaction.startswith("listen_"):
        return _clean_parts(source_text.split(". ", 1)[1])
    if ":" in source_text:
        prefix, suffix = source_text.split(":", 1)
        if "/" in suffix or "،" in suffix:
            return _clean_parts(suffix)
        if "/" in prefix:
            return ["نفسه", "مختلفان"]
        if suffix.strip():
            if skill_name == "مفاهيم المادة المطبوعة":
                return ["حرف", "كلمة", "جملة"]
            return [suffix.strip(" .")]
    if "=" in source_text:
        return [source_text.split("=", 1)[1].strip(" .")]
    return [source_text.strip(" .")]


def _base_round(item: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    source = str(raw.get("source_text") or "")
    interaction = str(item.get("interaction_type") or "choose_one")
    if interaction in READ:
        expected = re.sub(r"^اقرأ(?:\s+النص\s+الآتي)?\s*:\s*", "", source).strip()
        return {"order_index":int(raw["order_index"]), "question_text":"اقرأ النص الظاهر بصوت واضح.", "instruction_text":"", "stimulus":{}, "expected_reading_text":expected, "options":[], "media":deepcopy(raw.get("media") or []), "media_gaps":deepcopy(raw.get("media_gaps") or [])}
    options = _legacy_options(interaction, str(item.get("skill_name") or ""), source)
    return {"order_index":int(raw["order_index"]), "question_text":source, "instruction_text":"", "stimulus":{}, "expected_reading_text":None, "options":[{"text":value,"is_correct":False} for value in options], "media":deepcopy(raw.get("media") or []), "media_gaps":deepcopy(raw.get("media_gaps") or [])}


def _base_items() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    payload = _json(BASE)
    items: list[dict[str, Any]] = []
    for item in payload["items"]:
        spec = {
            "canonical_id":str(item["canonical_id"]), "stable_key":str(item["stable_key"]),
            "kind":str(item["kind"]), "level_id":int(item["level_id"]),
            "skill_key":str(item["skill_id"]), "interaction_type":str(item["interaction_type"]),
            "order_index":int(item["order_index"]), "title":str(item.get("title") or item["canonical_id"]),
            "criterion":item.get("criterion"), "rounds":[_base_round(item, raw) for raw in item.get("rounds", [])],
            "item_assets":deepcopy(item.get("item_assets") or []), "source_release":"client_catalog_105",
        }
        items.append(spec)
    return items, deepcopy(payload["skills"])


def _addition_round(item: dict[str, Any], raw: dict[str, Any], order: int) -> dict[str, Any]:
    interaction = str(item["interaction"])
    expected = raw.get("expected_reading")
    if isinstance(expected, list): expected = " ".join(str(v) for v in expected)
    values: list[str] = []
    if isinstance(raw.get("options"), list): values = [str(v) for v in raw["options"]]
    elif isinstance(raw.get("sequence"), list): values = [str(v) for v in raw["sequence"]]
    elif isinstance(raw.get("path"), str):
        count = int(str(raw["path"]).split("_", 1)[0]); values = [str(v) for v in range(1, count + 1)]
    answer = str(raw.get("answer") or "")
    options = [{"text":v,"is_correct":bool(answer and v == answer)} for v in values]
    prompt = str(raw.get("prompt") or raw.get("text") or "")
    if not prompt:
        prompt = "اقرأ النص بصوت واضح." if interaction in READ else ("رتّب العناصر بالترتيب الصحيح." if interaction in ORDER else "اختر الإجابة المناسبة.")
    return {"order_index":order,"question_text":prompt,"instruction_text":"","stimulus":{},"expected_reading_text":str(expected) if expected is not None else None,"options":options,"media":[],"media_gaps":[]}


def _addition_items(path: Path, skills: dict[str, str], stable_prefix: str) -> list[dict[str, Any]]:
    payload = _json(path)
    result = []
    for item in payload["items"]:
        canonical = str(item["canonical_id"])
        result.append({
            "canonical_id":canonical, "stable_key":f"{stable_prefix}:{canonical.lower()}",
            "kind":"reinforcement_activity", "level_id":int(item["level"]),
            "canonical_skill_code":skills[canonical], "interaction_type":str(item["interaction"]),
            "order_index":int(canonical.rsplit("-", 1)[1]), "title":str(item["title"]),
            "criterion":None, "rounds":[_addition_round(item, raw, i) for i, raw in enumerate(item["rounds"], 1)],
            "item_assets":[], "source_release":str(payload["catalog_version"]),
        })
    return result


def _apply_pretest(items: dict[str, dict[str, Any]]) -> None:
    payload = _json(PRETEST)
    for current in payload["items"]:
        canonical = str(current["canonical_id"])
        item = items[canonical]
        step = item["rounds"][0]
        step["question_text"] = str(current["question_text"])
        step["instruction_text"] = str(current["instruction_text"])
        step["stimulus"] = deepcopy(current.get("stimulus") or {})
        if current.get("options") is not None:
            answer = current.get("correct_answer")
            answers = {str(v) for v in answer} if isinstance(answer, list) else {str(answer)}
            step["options"] = [{"text":str(v),"is_correct":str(v) in answers} for v in current.get("options", [])]
        item["presentation"] = {"skill":current.get("skill"),"encouragement":current.get("encouragement"),"question_text":current.get("question_text"),"instruction_text":current.get("instruction_text"),"stimulus":deepcopy(current.get("stimulus") or {})}


def _apply_student_v2(items: dict[str, dict[str, Any]]) -> None:
    payload = _json(STUDENT_V2)
    for canonical, rounds in (payload.get("replacement_rounds") or {}).items():
        if canonical not in items: continue
        item = items[canonical]
        rebuilt = []
        for index, raw in enumerate(rounds, 1):
            options = [str(v) for v in raw.get("options", [])]
            answer = str(raw.get("answer") or "")
            rebuilt.append({"order_index":index,"question_text":str(raw.get("prompt") or "اختر الإجابة المناسبة."),"instruction_text":"","stimulus":{},"expected_reading_text":None,"options":[{"text":v,"is_correct":v == answer} for v in options],"media":[],"media_gaps":[]})
        item["rounds"] = rebuilt
    for canonical, correction in (payload.get("explicit_corrections") or {}).items():
        if canonical in items and correction.get("interaction"):
            items[canonical]["interaction_type"] = str(correction["interaction"])


def _semantic_asset(spec: tuple[str, str, str, str], option_order: int | None = None) -> dict[str, Any]:
    asset_id, asset_type, usage, semantic = spec
    result = {"asset_id":asset_id,"asset_type":asset_type,"usage":usage,"semantic_text":semantic}
    if option_order is not None: result["option_order_index"] = option_order
    return result


def _apply_approval(items: dict[str, dict[str, Any]]) -> None:
    for canonical, question in {**PRETEST_QUESTIONS, **LEARNING_QUESTIONS, **POSTTEST_QUESTIONS}.items():
        item = items.get(canonical)
        if not item: raise RuntimeError(f"Approval references missing item {canonical}")
        if len(item["rounds"]) == 1: item["rounds"][0]["question_text"] = question
        item.setdefault("presentation", {})["question_text"] = question
    for canonical, questions in LEARNING_ROUND_QUESTIONS.items():
        item = items[canonical]
        if len(item["rounds"]) != len(questions): raise RuntimeError(f"{canonical}: question round count mismatch")
        for step, question in zip(item["rounds"], questions, strict=True): step["question_text"] = question
    for canonical, stimuli in LEARNING_ROUND_STIMULI.items():
        item = items[canonical]
        if len(item["rounds"]) != len(stimuli): raise RuntimeError(f"{canonical}: stimulus round count mismatch")
        for step, text in zip(item["rounds"], stimuli, strict=True): step["stimulus"] = {"kind":"text","text":text}
    for canonical, rounds in OPTION_CONTRACTS.items():
        item = items[canonical]
        if len(item["rounds"]) != len(rounds): raise RuntimeError(f"{canonical}: option round count mismatch")
        for step, desired in zip(item["rounds"], rounds, strict=True): step["options"] = [{"text":text,"is_correct":correct} for text, correct in desired]
    for canonical, value in INTERACTION_OVERRIDES.items(): items[canonical]["interaction_type"] = value
    for canonical, values in READING_TEXTS.items():
        item = items[canonical]
        if len(item["rounds"]) != len(values): raise RuntimeError(f"{canonical}: reading round count mismatch")
        for step, value in zip(item["rounds"], values, strict=True): step["expected_reading_text"] = value; step["options"] = []
    for canonical, values in TIMED_WORD_SELECTIONS.items():
        item = items[canonical]
        if len(item["rounds"]) != len(values): raise RuntimeError(f"{canonical}: timed-word round count mismatch")
        for step, value in zip(item["rounds"], values, strict=True): step["expected_reading_text"] = value; step["options"] = []
    for canonical, value in CRITERIA.items(): items[canonical]["criterion"] = value
    for canonical, value in PRETEST_STIMULUS_OVERRIDES.items(): items[canonical]["rounds"][0]["stimulus"] = deepcopy(value)
    for canonical, value in POSTTEST_STIMULUS_OVERRIDES.items(): items[canonical]["rounds"][0]["stimulus"] = deepcopy(value)
    for canonical, intro in CONTEXT_INTROS.items(): items[canonical]["context_intro"] = deepcopy(intro)
    for canonical, hint in LAYOUT_HINTS.items(): items[canonical]["layout_hint"] = hint
    for canonical, by_round in STEP_MEDIA.items():
        item = items[canonical]
        steps = {int(step["order_index"]):step for step in item["rounds"]}
        for round_number, specs in by_round.items():
            step = steps[round_number]
            option_index = {visible_key(str(o["text"])):i for i, o in enumerate(step["options"], 1)}
            media = []
            for spec in specs:
                semantic = spec[3]
                order = option_index.get(visible_key(semantic)) if spec[2] == "choice" else None
                if spec[2] == "choice" and order is None: raise RuntimeError(f"{canonical} r{round_number}: media semantic {semantic!r} has no current option")
                media.append(_semantic_asset(spec, order))
            step["media"] = media
            step["media_gaps"] = []
    for canonical, specs in ITEM_MEDIA.items(): items[canonical]["item_assets"] = [_semantic_asset(spec) for spec in specs]
    for canonical in SUPPRESS_ITEM_MEDIA:
        if canonical in items: items[canonical]["item_assets"] = []
    for item in items.values(): item["release_version"] = VERSION


def _validate(items: list[dict[str, Any]]) -> None:
    if len(items) != 125: raise RuntimeError(f"Canonical release must contain 125 items, got {len(items)}")
    ids = [item["canonical_id"] for item in items]
    if len(ids) != len(set(ids)): raise RuntimeError("Duplicate canonical IDs")
    counts = {"pretest_question":0,"posttest_question":0,"core_activity":0,"reinforcement_activity":0}
    for item in items: counts[item["kind"]] = counts.get(item["kind"], 0) + 1
    if counts != {"pretest_question":30,"posttest_question":30,"core_activity":30,"reinforcement_activity":35}: raise RuntimeError(f"Canonical count mismatch: {counts}")
    ordered = ORDER
    for item in items:
        interaction = item["interaction_type"]
        if not item["rounds"]: raise RuntimeError(f"{item['canonical_id']} has no rounds")
        for step in item["rounds"]:
            texts = [str(o["text"]) for o in step["options"]]
            keys = [visible_key(v) for v in texts]
            if interaction not in ordered and len(keys) != len(set(keys)): raise RuntimeError(f"Duplicate visible options: {item['canonical_id']} r{step['order_index']}")
            for text in texts:
                if any(marker in text for marker in ("الخيارات:", "التعليمات:", "اختر المقطعين اللذين", "كوّن كلمة")):
                    raise RuntimeError(f"Composite/raw option leaked: {item['canonical_id']} -> {text}")
            mapped = [m for m in step.get("media", []) if m.get("asset_type") == "image" and m.get("usage") == "choice"]
            if mapped:
                orders = [m.get("option_order_index") for m in mapped]
                if any(v is None for v in orders) or len(orders) != len(set(orders)): raise RuntimeError(f"Invalid semantic image mapping: {item['canonical_id']} r{step['order_index']}")
    post11 = next(i for i in items if i["canonical_id"] == "POST-Q11")
    if post11["criterion"] != "مَ": raise RuntimeError("POST-Q11 criterion is not مَ")


def compile_release() -> dict[str, Any]:
    base, skills = _base_items()
    all_items = base + _addition_items(REIN_V1, V1_SKILLS, "himma:reinforcement-addition") + _addition_items(REIN_V2, V2_SKILLS, "himma:reinforcement-addition-v2")
    by_id = {item["canonical_id"]:item for item in all_items}
    _apply_pretest(by_id)
    _apply_student_v2(by_id)
    _apply_approval(by_id)
    ordered_items = sorted(by_id.values(), key=lambda i:(0 if i["kind"] == "pretest_question" else 1 if i["kind"] == "core_activity" else 2 if i["kind"] == "reinforcement_activity" else 3, i["level_id"], i["order_index"], i["canonical_id"]))
    _validate(ordered_items)
    canonical = {"schema_version":2,"release_version":VERSION,"skills":skills,"items":ordered_items}
    raw = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    canonical["sha256"] = hashlib.sha256(raw).hexdigest()
    return canonical


if __name__ == "__main__":
    release = compile_release()
    print(json.dumps({"release_version":release["release_version"],"items":len(release["items"]),"sha256":release["sha256"]}, ensure_ascii=False, indent=2))
