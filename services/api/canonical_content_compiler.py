"""Compile every approved Himma source into one canonical current release.

This module is deliberately DB-free. Historical catalogs are import/migration
inputs only. The compiled release is the *only* object that a publisher may use
to update PostgreSQL. Runtime requests never import or parse those source files.

The order is intentional:
1. import the immutable client baseline + approved reinforcement additions;
2. reproduce the already-approved maintenance semantics needed to migrate that
   legacy material (correctness, exact choice pools, image mappings, stories);
3. apply the owner-approved 2026-09-08 contract last;
4. validate the complete 125-item release strictly before returning it.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from copy import deepcopy
from difflib import SequenceMatcher
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
AUDITORY_STORIES = CONTENT / "l1_auditory_comprehension_v1.json"
REIN_V1 = CONTENT / "reinforcement_additions_v1.json"
REIN_V2 = CONTENT / "reinforcement_additions_v2.json"

READ = {"read_aloud", "timed_read_aloud"}
SINGLE = {"choose_one", "listen_choose_one", "choose_image", "listen_choose_image"}
MULTI = {"choose_many", "listen_choose_many"}
ORDER = {"sequence", "memory_sequence", "path_sequence", "build_word"}
LISTEN = {"listen_choose_one", "listen_choose_image", "listen_choose_many"}

# Additional reinforcement items reuse the canonical skill rows already created
# by the approved 105-item catalog. No new academic skills are invented here.
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

# These were approved maintenance contracts before the 2026-09-08 copy review.
# They are migration inputs only and are folded into the final release so the old
# seed_student_choice_corrections runtime patch is no longer required.
LEGACY_POOLS: dict[str, tuple[list[str], int]] = {
    "L1-CORE-03": (["بـ", "مـ", "سـ", "كـ", "لـ"], 4),
    "L1-REIN-03": (["باب", "قلم", "شمس", "سمكة", "كرة"], 3),
    "L2-REIN-04": (["بَاب", "قَلَم", "شَمْس", "قِطَّة", "كِتَاب"], 3),
    "POST-Q08": (["ل", "كِتَاب", "قَرَأَ خَالِدٌ الْكِتَابَ."], 3),
    "POST-Q09": (["ك", "نَخْلَة", "ذَهَبَ مَاجِدٌ إِلَى الْبَحْرِ"], 3),
}
LEGACY_EXACT_CHOICES: dict[str, list[list[str]]] = {
    "L3-CORE-07": [
        ["المكتبة", "الحديقة", "الساحة"],
        ["وقت الفسحة", "في الليل", "بعد العودة إلى البيت"],
        ["الحيوانات", "السيارات", "الطعام"],
        ["أمين المكتبة", "صديقه", "والده"],
        ["أعاده إلى مكانه", "تركه على الأرض", "أخذه إلى البيت"],
    ],
    "L3-CORE-08": [
        ["لأنهم سيقضون وقتًا في الرحلة", "ليغسل السيارة", "ليرويه على الأرض"],
        ["لوضع حاجاتهم فيها", "لتركها في الوادي", "للعب بها"],
        ["المحافظة على النظافة", "الرغبة في العودة سريعًا", "الخوف من الطيور"],
        ["تنظيف المكان قبل المغادرة", "ترك الطعام على الأرض", "قطع الأشجار"],
        ["رحلة عائلية مع المحافظة على المكان", "يوم دراسي داخل الفصل", "التسوق من السوق"],
    ],
    "L3-CORE-09": [
        ["قليل الضوضاء", "سريع الحركة", "شديد الحرارة"],
        ["أرجع", "أخذ", "كسر"],
        ["أشياء متروكة بعد الاستخدام", "أدوات الدراسة", "أنواع النباتات"],
        ["نظيفة وواضحة", "مظلمة", "بعيدة"],
        ["بجانب", "فوق", "بعيدًا عن"],
    ],
    "L3-REIN-02": [
        ["حمل سالم مظلته وخرج من المنزل", "لعب سالم بالكرة", "قرأ سالم كتابًا"],
        ["كانت تسقيها كل صباح", "كانت تنظر إلى السماء", "كانت تلعب في الساحة"],
        ["أعاد الكتاب إلى مكانه", "دخل المكتبة", "جلس على الكرسي"],
    ],
    "L3-REIN-05": [
        ["في المكتبة", "في الملعب", "رحلة إلى البحر"],
        ["شاطئ نظيف", "يوم في المدرسة", "زيارة الطبيب"],
        ["النبتة الصغيرة", "السيارة الجديدة", "الطائر السريع"],
    ],
}
LEGACY_SEGMENTATION = [
    [
        "ذَهَبَ سَالِمٌ / إِلَى الْمَدْرَسَةِ / فِي الصَّبَاحِ",
        "ذَهَبَ / سَالِمٌ إِلَى الْمَدْرَسَةِ / فِي الصَّبَاحِ",
        "ذَهَبَ سَالِمٌ إِلَى / الْمَدْرَسَةِ فِي / الصَّبَاحِ",
    ],
    [
        "جَلَسَتْ مَرْيَمُ / تَحْتَ الشَّجَرَةِ / وَقَرَأَتْ كِتَابًا",
        "جَلَسَتْ / مَرْيَمُ تَحْتَ الشَّجَرَةِ / وَقَرَأَتْ كِتَابًا",
        "جَلَسَتْ مَرْيَمُ تَحْتَ / الشَّجَرَةِ وَقَرَأَتْ / كِتَابًا",
    ],
    [
        "لَعِبَ الْأَطْفَالُ / فِي السَّاحَةِ / بَعْدَ الدَّرْسِ",
        "لَعِبَ / الْأَطْفَالُ فِي السَّاحَةِ / بَعْدَ الدَّرْسِ",
        "لَعِبَ الْأَطْفَالُ فِي / السَّاحَةِ بَعْدَ / الدَّرْسِ",
    ],
    [
        "وَقَفَ الْعُصْفُورُ / فَوْقَ النَّخْلَةِ / ثُمَّ طَارَ",
        "وَقَفَ / الْعُصْفُورُ فَوْقَ النَّخْلَةِ / ثُمَّ طَارَ",
        "وَقَفَ الْعُصْفُورُ فَوْقَ / النَّخْلَةِ ثُمَّ / طَارَ",
    ],
    [
        "عَادَ مَاجِدٌ / إِلَى الْبَيْتِ / مَعَ وَالِدِهِ",
        "عَادَ / مَاجِدٌ إِلَى الْبَيْتِ / مَعَ وَالِدِهِ",
        "عَادَ مَاجِدٌ إِلَى / الْبَيْتِ مَعَ / وَالِدِهِ",
    ],
]
WORD_IMAGE_ASSETS = {
    "باب":"VOC-03", "بَاب":"VOC-03", "قلم":"VOC-04", "قَلَم":"VOC-04",
    "شمس":"VOC-06", "شَمْس":"VOC-06", "سمكة":"VOC-05", "كرة":"VOC-10",
    "قِطَّة":"VOC-16", "كتاب":"VOC-02", "كِتَاب":"VOC-02",
}

RAW_MARKERS = (
    "الخيارات:", "التعليمات:", "الإجابة الصحيحة:", "كوّن كلمة", "كون كلمة",
)


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _plain(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").replace("ـ", "")
    return re.sub(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]", "", value)


def _semantic_key(value: str) -> str:
    value = _plain(value)
    value = re.sub(r"[^\w\u0600-\u06ff]+", "", value, flags=re.UNICODE)
    if value.startswith("ال"):
        value = value[2:]
    return value.casefold()


def _clean_parts(value: str) -> list[str]:
    return [part.strip(" .") for part in re.split(r"[،/]", value) if part.strip(" .")]


def _legacy_options(interaction: str, skill_name: str, source_text: str) -> list[str]:
    """Migration-only extraction for baseline rounds that predate structured data."""
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
        return [part.strip(" .") for part in source_text.split("=", 1)[0].split("+") if part.strip(" .")]
    return []


def _infer_correct_index(options: list[str], answer: str, criterion: str) -> int | None:
    if not options:
        return None
    targets = [_semantic_key(answer), _semantic_key(criterion)]
    for target in targets:
        if not target:
            continue
        exact = [index for index, option in enumerate(options) if _semantic_key(option) == target]
        if len(exact) == 1:
            return exact[0]
    # Migration fallback only: choose the unique strongest semantic match. The
    # compiled result is still validated as structured data before publication.
    target = next((value for value in targets if value), "")
    if target:
        scores = [(SequenceMatcher(None, _semantic_key(option), target).ratio(), index) for index, option in enumerate(options)]
        scores.sort(reverse=True)
        if scores and scores[0][0] >= 0.72 and (len(scores) == 1 or scores[0][0] > scores[1][0]):
            return scores[0][1]
    return None


def _base_round(item: dict[str, Any], task: dict[str, Any], round_number: int) -> dict[str, Any]:
    interaction = str(task.get("interaction_type") or item.get("interaction_type") or "choose_one")
    source = str(task.get("source_text") or "").strip()
    expected = str(task.get("expected_response") or "").strip()
    criterion = str(task.get("criterion") or expected or item.get("criterion") or "").strip()
    options = _legacy_options(interaction, str(item.get("skill_name") or ""), source)
    correct_index = _infer_correct_index(options, expected, criterion)
    if interaction in SINGLE | MULTI and options and correct_index is None:
        raise RuntimeError(f"{item['stable_key']} r{round_number}: cannot migrate legacy correctness")
    presentation_source = _strip_embedded_source(source, interaction, options)
    return {
        "order_index":round_number,
        "prompt_text":presentation_source,
        "question_text":presentation_source or _default_question(interaction, str(item.get("skill_name") or "")),
        "instruction_text":_generic_instruction(interaction),
        "hint":_generic_hint(interaction),
        "encouragement":_encouragement(round_number),
        "stimulus_text":"",
        "stimulus":{"kind":"none"},
        "expected_reading_text":expected if interaction in READ else None,
        "options":[{"text":value,"is_correct":index == correct_index} for index, value in enumerate(options)],
        "media":[],
        "media_gaps":[],
    }


def _base_items() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    catalog = _json(BASE)
    items: list[dict[str, Any]] = []
    for raw in catalog["items"]:
        interaction = str(raw["interaction_type"])
        rounds = [_base_round(raw, task, index) for index, task in enumerate(raw["tasks"], 1)]
        items.append({
            "stable_key":str(raw["stable_key"]),
            "canonical_id":_catalog_canonical(raw),
            "kind":str(raw["kind"]),
            "level_id":int(raw["level_id"]),
            "order_index":int(raw["order_index"]),
            "interaction_type":interaction,
            "source_method":str(raw.get("source_method") or ""),
            "criterion":str(raw.get("criterion") or "").strip(),
            "canonical_skill_code":str(raw.get("skill_code") or "").strip(),
            "skill_name":str(raw.get("skill_name") or "").strip(),
            "title":str(raw.get("title") or raw.get("skill_name") or "مهمة تعليمية").strip(),
            "item_assets":[],
            "rounds":rounds,
        })
    skills = [dict(value) for value in catalog.get("skills", [])]
    return items, skills


def _addition_items(path: Path, skill_map: dict[str, str], stable_prefix: str) -> list[dict[str, Any]]:
    payload = _json(path)
    result = []
    for raw in payload.get("items", []):
        canonical = str(raw["id"])
        interaction = str(raw["interaction_type"])
        skill_code = skill_map.get(canonical)
        if not skill_code:
            raise RuntimeError(f"No canonical skill mapping for {canonical}")
        rounds = []
        for index, task in enumerate(raw.get("tasks", []), 1):
            source = str(task.get("source_text") or "").strip()
            expected = str(task.get("expected_response") or "").strip()
            criterion = str(task.get("criterion") or expected or raw.get("criterion") or "").strip()
            options = _legacy_options(interaction, str(raw.get("skill") or ""), source)
            correct_index = _infer_correct_index(options, expected, criterion)
            if interaction in SINGLE | MULTI and options and correct_index is None:
                raise RuntimeError(f"{canonical} r{index}: cannot migrate reinforcement correctness")
            presentation_source = _strip_embedded_source(source, interaction, options)
            rounds.append({
                "order_index":index,
                "prompt_text":presentation_source,
                "question_text":presentation_source or _default_question(interaction, str(raw.get("skill") or "")),
                "instruction_text":_generic_instruction(interaction),
                "hint":_generic_hint(interaction),
                "encouragement":_encouragement(index),
                "stimulus_text":"",
                "stimulus":{"kind":"none"},
                "expected_reading_text":expected if interaction in READ else None,
                "options":[{"text":value,"is_correct":option_index == correct_index} for option_index, value in enumerate(options)],
                "media":[],
                "media_gaps":[],
            })
        result.append({
            "stable_key":f"{stable_prefix}:{canonical.lower()}",
            "canonical_id":canonical,
            "kind":"reinforcement_activity",
            "level_id":int(raw["level_id"]),
            "order_index":int(raw["order_index"]),
            "interaction_type":interaction,
            "source_method":str(raw.get("source_method") or ""),
            "criterion":str(raw.get("criterion") or "").strip(),
            "canonical_skill_code":skill_code,
            "skill_name":str(raw.get("skill") or "").strip(),
            "title":str(raw.get("skill") or "تدريب تقوية").strip(),
            "item_assets":[],
            "rounds":rounds,
        })
    return result


def _replace_options(step: dict[str, Any], options: list[tuple[str, bool]]) -> None:
    step["options"] = [{"text":str(text), "is_correct":bool(correct)} for text, correct in options]


def _apply_pretest(items: dict[str, dict[str, Any]]) -> None:
    payload = _json(PRETEST)
    for q in payload.get("questions", []):
        canonical = str(q["id"])
        item = items[canonical]
        step = item["rounds"][0]
        item["interaction_type"] = str(q["interaction_type"])
        item["canonical_skill_code"] = str(q["skill_code"])
        item["skill_name"] = str(q["skill"])
        step["question_text"] = str(q["question_text"]).strip()
        step["instruction_text"] = str(q["instruction_text"]).strip()
        step["encouragement"] = str(q["encouragement"]).strip()
        step["stimulus"] = deepcopy(q.get("stimulus") or {"kind":"none"})
        step["stimulus_text"] = str((step["stimulus"] or {}).get("text") or "")
        step["expected_reading_text"] = q.get("reading_reference")
        desired = []
        for opt in q.get("options") or []:
            desired.append((str(opt["text"]), bool(opt.get("is_correct"))))
        if desired:
            _replace_options(step, desired)


def _apply_student_v2(items: dict[str, dict[str, Any]]) -> None:
    payload = _json(STUDENT_V2)
    for raw in payload.get("replacements", []):
        canonical = str(raw["id"])
        if canonical not in items:
            continue
        item = items[canonical]
        item["interaction_type"] = str(raw.get("interaction_type") or item["interaction_type"])
        rounds = []
        for index, source in enumerate(raw.get("tasks") or [], 1):
            answer = str(source.get("correct_answer") or "").strip()
            values = [str(value) for value in (source.get("options") or [])]
            if not values and item["interaction_type"] == "read_aloud":
                values = []
            rounds.append({
                "order_index":index,
                "prompt_text":str(source.get("prompt_text") or source.get("question_text") or "").strip(),
                "question_text":str(source.get("question_text") or source.get("prompt_text") or "").strip(),
                "instruction_text":str(source.get("instruction_text") or _generic_instruction(item["interaction_type"])),
                "hint":str(source.get("hint") or _generic_hint(item["interaction_type"])),
                "encouragement":str(source.get("encouragement") or _encouragement(index)),
                "stimulus_text":str(source.get("stimulus_text") or ""),
                "stimulus":deepcopy(source.get("stimulus") or {"kind":"none"}),
                "expected_reading_text":source.get("reading_reference") or source.get("expected_reading_text"),
                "options":[{"text":value, "is_correct":visible_key(value) == visible_key(answer)} for value in values],
                "media":[],
                "media_gaps":[],
            })
        if rounds:
            item["rounds"] = rounds


def _apply_auditory_story_source(items: dict[str, dict[str, Any]]) -> None:
    payload = _json(AUDITORY_STORIES)
    for raw in payload.get("replacements", []):
        canonical = str(raw.get("id") or "")
        if canonical not in items:
            continue
        item = items[canonical]
        item["interaction_type"] = str(raw.get("interaction_type") or item["interaction_type"])
        if raw.get("criterion"):
            item["criterion"] = str(raw["criterion"])


def _deterministic_pool_options(pool: list[str], size: int, correct: str, round_index: int) -> list[tuple[str,bool]]:
    correct_key = visible_key(correct)
    if correct_key not in {visible_key(value) for value in pool}:
        raise RuntimeError(f"Legacy pool has no correct value {correct!r}")
    start = (round_index - 1) % len(pool)
    ordered = [pool[(start + offset) % len(pool)] for offset in range(len(pool))]
    chosen = ordered[:size]
    if correct_key not in {visible_key(value) for value in chosen}:
        chosen[-1] = next(value for value in pool if visible_key(value) == correct_key)
    return [(value, visible_key(value) == correct_key) for value in chosen]


def _apply_legacy_maintenance(items: dict[str, dict[str, Any]]) -> None:
    for canonical, (pool, size) in LEGACY_POOLS.items():
        item = items[canonical]
        for index, step in enumerate(item["rounds"], 1):
            correct = next((str(value["text"]) for value in step["options"] if value["is_correct"]), "")
            if not correct:
                criterion = str(item.get("criterion") or "")
                correct = criterion.split("،")[index - 1].strip() if "،" in criterion else criterion
            _replace_options(step, _deterministic_pool_options(pool, size, correct, index))
            if canonical in {"L1-REIN-03", "L2-REIN-04"}:
                step["media"] = [
                    _semantic_asset((WORD_IMAGE_ASSETS[text], "image", "choice", text), order)
                    for order, (text, _) in enumerate(_deterministic_pool_options(pool, size, correct, index), 1)
                ]
    for canonical, choices in LEGACY_EXACT_CHOICES.items():
        item = items[canonical]
        for index, values in enumerate(choices, 1):
            step = item["rounds"][index - 1]
            existing_correct = next((str(value["text"]) for value in step["options"] if value["is_correct"]), "")
            correct_key = _semantic_key(existing_correct) or _semantic_key(str(item.get("criterion") or ""))
            exact = next((value for value in values if _semantic_key(value) == correct_key), values[0])
            _replace_options(step, [(value, value == exact) for value in values])
    if "L3-REIN-01" in items:
        item = items["L3-REIN-01"]
        for index, values in enumerate(LEGACY_SEGMENTATION, 1):
            _replace_options(item["rounds"][index - 1], [(value, option_index == 0) for option_index, value in enumerate(values)])


def _apply_approval(items: dict[str, dict[str, Any]]) -> None:
    for canonical, value in INTERACTION_OVERRIDES.items():
        items[canonical]["interaction_type"] = value

    for canonical, question in PRETEST_QUESTIONS.items():
        items[canonical]["rounds"][0]["question_text"] = question
    for canonical, question in POSTTEST_QUESTIONS.items():
        for step in items[canonical]["rounds"]:
            step["question_text"] = question
    for canonical, question in LEARNING_QUESTIONS.items():
        if canonical in LEARNING_ROUND_QUESTIONS:
            continue
        for step in items[canonical]["rounds"]:
            step["question_text"] = question
    for canonical, by_round in LEARNING_ROUND_QUESTIONS.items():
        for round_number, question in by_round.items():
            items[canonical]["rounds"][round_number - 1]["question_text"] = question
    for canonical, by_round in LEARNING_ROUND_STIMULI.items():
        for round_number, stimulus in by_round.items():
            step = items[canonical]["rounds"][round_number - 1]
            step["stimulus_text"] = stimulus
            step["stimulus"] = {"kind":"text", "text":stimulus}
    for canonical, stimulus in PRETEST_STIMULUS_OVERRIDES.items():
        step = items[canonical]["rounds"][0]
        step["stimulus"] = deepcopy(stimulus)
        step["stimulus_text"] = str(stimulus.get("text") or "")
    for canonical, stimulus in POSTTEST_STIMULUS_OVERRIDES.items():
        step = items[canonical]["rounds"][0]
        step["stimulus"] = deepcopy(stimulus)
        step["stimulus_text"] = str(stimulus.get("text") or "")

    for canonical, by_round in OPTION_CONTRACTS.items():
        for round_number, desired in by_round.items():
            _replace_options(items[canonical]["rounds"][round_number - 1], desired)
    for canonical, criterion in CRITERIA.items():
        items[canonical]["criterion"] = criterion
    for canonical, value in READING_TEXTS.items():
        rounds = items[canonical]["rounds"]
        if isinstance(value, list):
            for index, text in enumerate(value, 1):
                rounds[index - 1]["expected_reading_text"] = text
                rounds[index - 1]["stimulus_text"] = text
                rounds[index - 1]["stimulus"] = {"kind":"reading", "text":text}
        else:
            for step in rounds:
                step["expected_reading_text"] = value
                step["stimulus_text"] = value
                step["stimulus"] = {"kind":"reading", "text":value}
    for canonical, by_round in TIMED_WORD_SELECTIONS.items():
        for round_number, words in by_round.items():
            step = items[canonical]["rounds"][round_number - 1]
            text = " ".join(words)
            step["expected_reading_text"] = text
            step["stimulus_text"] = text
            step["stimulus"] = {"kind":"reading", "text":text}
            step["options"] = []

    # Final owner-approved interaction cleanup: reading tasks have no choice state.
    for item in items.values():
        if item["interaction_type"] in READ:
            for step in item["rounds"]:
                step["options"] = []

    for canonical, intro in CONTEXT_INTROS.items():
        items[canonical]["context_intro"] = deepcopy(intro)
    for canonical, hint in LAYOUT_HINTS.items():
        items[canonical]["layout_hint"] = hint

    for canonical, by_round in STEP_MEDIA.items():
        for round_number, specs in by_round.items():
            step = items[canonical]["rounds"][round_number - 1]
            option_index = {visible_key(value["text"]):index for index, value in enumerate(step["options"], 1)}
            media = []
            for spec in specs:
                semantic = spec[3]
                order = option_index.get(visible_key(semantic)) if spec[2] == "choice" else None
                if spec[2] == "choice" and order is None:
                    raise RuntimeError(f"{canonical} r{round_number}: media semantic {semantic!r} has no current option")
                media.append(_semantic_asset(spec, order))
            step["media"] = media
            step["media_gaps"] = []

    for canonical, specs in ITEM_MEDIA.items():
        items[canonical]["item_assets"] = [_semantic_asset(spec) for spec in specs]
    for canonical in SUPPRESS_ITEM_MEDIA:
        if canonical in items:
            items[canonical]["item_assets"] = []

    # Story audio belongs to the intro only, never to question rounds.
    for canonical in ("L1-CORE-09", "L1-REIN-11"):
        for step in items[canonical]["rounds"]:
            step["media"] = [asset for asset in step.get("media", []) if asset.get("asset_type") != "audio"]
            step["instruction_text"] = "اختر الإجابة الصحيحة اعتمادًا على ما فهمته من القصة."

    # Ensure every final student-facing round has explicit presentation fields.
    for item in items.values():
        interaction = str(item["interaction_type"])
        for step in item["rounds"]:
            step["instruction_text"] = str(step.get("instruction_text") or _generic_instruction(interaction)).strip()
            step["hint"] = str(step.get("hint") or _generic_hint(interaction)).strip()
            step["encouragement"] = str(step.get("encouragement") or _encouragement(int(step["order_index"]))).strip()
        item["release_version"] = VERSION


def _validate_round(item: dict[str, Any], step: dict[str, Any]) -> None:
    canonical = str(item["canonical_id"])
    interaction = str(item["interaction_type"])
    prefix = f"{canonical}/R{int(step['order_index']):02d}"
    options = list(step.get("options") or [])
    texts = [str(value.get("text") or "") for value in options]
    keys = [visible_key(value) for value in texts]
    correct_count = sum(1 for value in options if bool(value.get("is_correct")))

    if any(not key for key in keys):
        raise RuntimeError(f"{prefix}: empty option")
    if interaction not in ORDER and len(keys) != len(set(keys)):
        raise RuntimeError(f"{prefix}: duplicate visible options")
    if interaction in SINGLE:
        if not 2 <= len(options) <= 5:
            raise RuntimeError(f"{prefix}: single-choice count={len(options)}")
        if correct_count != 1:
            raise RuntimeError(f"{prefix}: single-choice correct_count={correct_count}")
    elif interaction in MULTI:
        if not 2 <= len(options) <= 6:
            raise RuntimeError(f"{prefix}: multi-choice count={len(options)}")
        if not 1 <= correct_count < len(options):
            raise RuntimeError(f"{prefix}: multi-choice correct_count={correct_count}/{len(options)}")
    elif interaction in ORDER:
        if not 2 <= len(options) <= 8:
            raise RuntimeError(f"{prefix}: ordered-task count={len(options)}")
    elif interaction in READ:
        if options:
            raise RuntimeError(f"{prefix}: read-aloud has options")
        if not str(step.get("expected_reading_text") or "").strip():
            raise RuntimeError(f"{prefix}: read-aloud has no expected text")

    for field in ("question_text", "instruction_text", "hint", "encouragement"):
        value = str(step.get(field) or "").strip()
        if not value:
            raise RuntimeError(f"{prefix}: empty {field}")
        if any(marker in value for marker in RAW_MARKERS):
            raise RuntimeError(f"{prefix}: raw/source marker leaked into {field}")
    for text in texts:
        if any(marker in text for marker in RAW_MARKERS):
            raise RuntimeError(f"{prefix}: composite/raw option leaked: {text!r}")
        if "اختر المقطعين اللذين" in text:
            raise RuntimeError(f"{prefix}: question leaked into option")

    choice_images = [
        value for value in step.get("media", [])
        if value.get("asset_type") == "image" and value.get("usage") == "choice"
    ]
    if choice_images:
        orders = [value.get("option_order_index") for value in choice_images]
        if any(value is None for value in orders) or len(orders) != len(set(orders)):
            raise RuntimeError(f"{prefix}: invalid semantic image mapping")
        if any(int(value) < 1 or int(value) > len(options) for value in orders):
            raise RuntimeError(f"{prefix}: image maps outside current option set")
    has_declared_gap = bool(step.get("media_gaps"))
    if interaction in {"choose_image", "listen_choose_image"} and not has_declared_gap:
        if len(choice_images) != len(options):
            raise RuntimeError(f"{prefix}: image-choice is not 1:1 ({len(choice_images)}/{len(options)})")
    if interaction == "memory_sequence" and not has_declared_gap:
        if len(choice_images) != len(options):
            raise RuntimeError(f"{prefix}: memory image mapping is not 1:1 ({len(choice_images)}/{len(options)})")
    elif interaction in ORDER and choice_images and not has_declared_gap:
        if len(choice_images) != len(options):
            raise RuntimeError(f"{prefix}: ordered image mapping is partial ({len(choice_images)}/{len(options)})")


def _validate(items: list[dict[str, Any]]) -> None:
    if len(items) != 125:
        raise RuntimeError(f"Canonical release must contain 125 items, got {len(items)}")
    ids = [str(item["canonical_id"]) for item in items]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate canonical IDs")
    counts = {"pretest_question":0,"posttest_question":0,"core_activity":0,"reinforcement_activity":0}
    for item in items:
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1
    expected = {"pretest_question":30,"posttest_question":30,"core_activity":30,"reinforcement_activity":35}
    if counts != expected:
        raise RuntimeError(f"Canonical count mismatch: {counts}")

    for item in items:
        if not item.get("rounds"):
            raise RuntimeError(f"{item['canonical_id']} has no rounds")
        if not str(item.get("canonical_skill_code") or "").strip():
            raise RuntimeError(f"{item['canonical_id']} has no canonical skill")
        for step in item["rounds"]:
            _validate_round(item, step)

    post11 = next(item for item in items if item["canonical_id"] == "POST-Q11")
    step11 = post11["rounds"][0]
    if post11["criterion"] != "مَ":
        raise RuntimeError("POST-Q11 criterion is not مَ")
    if [value["text"] for value in step11["options"] if value["is_correct"]] != ["مَ"]:
        raise RuntimeError("POST-Q11 correct option is not مَ")
    stimulus = step11.get("stimulus") or {}
    if stimulus.get("audio_target") != "مَ":
        raise RuntimeError("POST-Q11 audio target is not مَ")
    audio_ids = [value.get("asset_id") for value in step11.get("media", []) if value.get("asset_type") == "audio"]
    if audio_ids != ["LET-01"]:
        raise RuntimeError(f"POST-Q11 audio asset mismatch: {audio_ids}")

    for canonical in ("POST-Q08", "POST-Q13"):
        item = next(value for value in items if value["canonical_id"] == canonical)
        for step in item["rounds"]:
            for option in step["options"]:
                value = str(option["text"])
                if "اختر" in value or "كوّن" in value or "الخيارات" in value:
                    raise RuntimeError(f"{canonical}: raw source leakage regression")

    for canonical, asset_id in (("L1-CORE-09", "INS-01"), ("L1-REIN-11", "INS-02")):
        item = next(value for value in items if value["canonical_id"] == canonical)
        if [value.get("asset_id") for value in item.get("item_assets", [])] != [asset_id]:
            raise RuntimeError(f"{canonical}: story intro audio mismatch")
        if any(value.get("asset_type") == "audio" for step in item["rounds"] for value in step.get("media", [])):
            raise RuntimeError(f"{canonical}: story audio leaked into question round")
        if item.get("canonical_skill_code") != "auditory_literal_comprehension":
            raise RuntimeError(f"{canonical}: auditory skill was not reconciled")

    for prefix in ("PRE-Q", "POST-Q"):
        for number in range(25, 31):
            item = next(value for value in items if value["canonical_id"] == f"{prefix}{number:02d}")
            if item.get("item_assets"):
                raise RuntimeError(f"{item['canonical_id']}: story image must be suppressed")


def compile_release() -> dict[str, Any]:
    base, skills = _base_items()
    all_items = (
        base
        + _addition_items(REIN_V1, V1_SKILLS, "himma:reinforcement-addition")
        + _addition_items(REIN_V2, V2_SKILLS, "himma:reinforcement-addition-v2")
    )
    by_id = {item["canonical_id"]:item for item in all_items}
    if len(by_id) != len(all_items):
        raise RuntimeError("Duplicate canonical ID before canonical compilation")

    _apply_pretest(by_id)
    _apply_student_v2(by_id)
    _apply_auditory_story_source(by_id)
    _apply_legacy_maintenance(by_id)
    _apply_approval(by_id)

    ordered_items = sorted(
        by_id.values(),
        key=lambda item:(
            0 if item["kind"] == "pretest_question" else
            1 if item["kind"] == "core_activity" else
            2 if item["kind"] == "reinforcement_activity" else 3,
            int(item["level_id"]), int(item["order_index"]), str(item["canonical_id"]),
        ),
    )
    _validate(ordered_items)
    canonical: dict[str, Any] = {
        "schema_version":3,
        "release_version":VERSION,
        "skills":skills,
        "skill_reconciliations":[{
            "level_id":1,
            "from_code":"visual_motor_direction",
            "to_code":"auditory_literal_comprehension",
            "name":"الفهم السمعي المباشر",
            "description":"الفهم السمعي المباشر من قصة مسموعة",
        }],
        "items":ordered_items,
    }
    raw = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    canonical["sha256"] = hashlib.sha256(raw).hexdigest()
    return canonical


if __name__ == "__main__":
    release = compile_release()
    print(json.dumps({
        "release_version":release["release_version"],
        "items":len(release["items"]),
        "sha256":release["sha256"],
    }, ensure_ascii=False, indent=2))
