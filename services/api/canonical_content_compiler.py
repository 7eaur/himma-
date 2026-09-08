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
        return [source_text.split("=", 1)[1].strip(" .")]
    return [source_text.strip(" .")]


def _question_answer(item: dict[str, Any]) -> str | None:
    criterion = item.get("criterion")
    if not criterion or str(criterion).startswith("مطابقة") or "الترتيب" in str(criterion):
        return None
    if criterion in {
        "الدقة والاسترسال",
        "تحليل الكلمات والوقت",
        "الكلمات الصحيحة والحذف والإضافة والاستبدال والوقت",
    }:
        return None
    return str(criterion)


def _round_answer(item: dict[str, Any], source_text: str, options: list[str]) -> str | None:
    answer = _question_answer(item)
    if answer:
        return answer
    if not options:
        return None
    if str(item.get("interaction_type")) in ORDER:
        return options[0]
    if ":" in source_text:
        prefix, suffix = source_text.split(":", 1)
        if "/" in prefix:
            return suffix.strip(" .")
        if len(options) > 1:
            return prefix.strip(" .")
        return suffix.strip(" .")
    if "=" in source_text:
        return source_text.split("=", 1)[1].strip(" .")
    return options[0]


def _correct_index(answer: str | None, options: list[str]) -> int:
    """Replicate the reviewed legacy importer only while compiling the baseline.

    The result becomes explicit ``is_correct`` data in the canonical release;
    no runtime path is allowed to perform this inference.
    """
    if not options:
        return -1
    if not answer:
        return 0
    answer_key = _semantic_key(answer)
    option_keys = [_semantic_key(option) for option in options]
    for index, key in enumerate(option_keys):
        if key == answer_key or key in answer_key or answer_key in key:
            return index
    return max(range(len(options)), key=lambda index: SequenceMatcher(None, answer_key, option_keys[index]).ratio())


def _generic_instruction(interaction: str) -> str:
    if interaction in LISTEN:
        return "اضغط زر الاستماع، ثم اختر الإجابة المطابقة."
    if interaction in READ:
        return "اضغط زر التسجيل، اقرأ النص المعروض، ثم أرسل التسجيل."
    if interaction == "memory_sequence":
        return "شاهد العناصر جيدًا، ثم أعد ترتيبها كما ظهرت."
    if interaction in ORDER:
        return "اضغط العناصر بحسب ترتيبها الصحيح."
    if interaction in {"choose_image", "choose_many"}:
        return "انظر إلى العناصر المعروضة، ثم اختر المطلوب."
    return "اقرأ المطلوب، ثم اختر الإجابة المناسبة."


def _generic_hint(interaction: str) -> str:
    if interaction == "memory_sequence":
        return "تذكّر العنصر الأول، ثم الذي بعده."
    if interaction in ORDER:
        return "ابدأ بالعنصر الأول، ثم أكمل الترتيب خطوة خطوة."
    if interaction in READ:
        return "اقرأ ببطء ووضوح، وركّز في الحروف والحركات."
    if interaction in LISTEN:
        return "استمع مرة أخرى، وركّز في الصوت المطلوب."
    if interaction in {"choose_image", "choose_many"}:
        return "انظر إلى كل عنصر بهدوء قبل أن تختار."
    return "اقرأ المطلوب بهدوء، ثم اختر الإجابة الأنسب."


def _encouragement(round_number: int) -> str:
    values = (
        "أحسنت، واصل بثقة!", "رائع، أنت تتقدم خطوة خطوة!", "ممتاز، استمر!",
        "عمل جميل، ركّز وأكمل!", "أنت قادر عليها!",
    )
    return values[(max(1, round_number) - 1) % len(values)]


def _base_round(item: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    source = str(raw.get("source_text") or "")
    interaction = str(item.get("interaction_type") or "choose_one")
    order = int(raw["order_index"])
    if interaction in READ:
        expected = re.sub(r"^اقرأ(?:\s+النص\s+الآتي)?\s*:\s*", "", source).strip()
        return {
            "order_index":order, "question_text":"اقرأ النص الظاهر بصوت واضح.",
            "instruction_text":_generic_instruction(interaction), "hint":_generic_hint(interaction),
            "encouragement":_encouragement(order), "stimulus":{},
            "expected_reading_text":expected, "options":[],
            "media":deepcopy(raw.get("media") or []), "media_gaps":deepcopy(raw.get("media_gaps") or []),
        }
    options = _legacy_options(interaction, str(item.get("skill_name") or ""), source)
    answer = _round_answer(item, source, options)
    correct_index = _correct_index(answer, options)
    return {
        "order_index":order, "question_text":source,
        "instruction_text":_generic_instruction(interaction), "hint":_generic_hint(interaction),
        "encouragement":_encouragement(order), "stimulus":{}, "expected_reading_text":None,
        "options":[{"text":value,"is_correct":index == correct_index} for index, value in enumerate(options)],
        "media":deepcopy(raw.get("media") or []), "media_gaps":deepcopy(raw.get("media_gaps") or []),
    }


def _base_items() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    payload = _json(BASE)
    skill_by_id = {str(value["skill_id"]):value for value in payload["skills"]}
    items: list[dict[str, Any]] = []
    for item in payload["items"]:
        skill = skill_by_id[str(item["skill_id"])]
        items.append({
            "canonical_id":str(item["canonical_id"]), "stable_key":str(item["stable_key"]),
            "kind":str(item["kind"]), "level_id":int(item["level_id"]),
            "skill_key":str(item["skill_id"]), "canonical_skill_code":str(skill["skill_code"]),
            "interaction_type":str(item["interaction_type"]), "order_index":int(item["order_index"]),
            "title":str(item.get("title") or item["canonical_id"]), "criterion":item.get("criterion"),
            "rounds":[_base_round(item, raw) for raw in item.get("rounds", [])],
            "item_assets":deepcopy(item.get("item_assets") or []), "source_release":"client_catalog_105",
        })
    return items, deepcopy(payload["skills"])


def _addition_round(item: dict[str, Any], raw: dict[str, Any], order: int) -> dict[str, Any]:
    interaction = str(item["interaction"])
    expected = raw.get("expected_reading")
    if isinstance(expected, list):
        expected = " ".join(str(v) for v in expected)
    values: list[str] = []
    if isinstance(raw.get("options"), list):
        values = [str(v) for v in raw["options"]]
    elif isinstance(raw.get("sequence"), list):
        values = [str(v) for v in raw["sequence"]]
    elif isinstance(raw.get("path"), str):
        count = int(str(raw["path"]).split("_", 1)[0])
        values = [str(v) for v in range(1, count + 1)]
    answer = str(raw.get("answer") or "")
    if interaction in ORDER:
        options = [{"text":v,"is_correct":False} for v in values]
    else:
        options = [{"text":v,"is_correct":bool(answer and v == answer)} for v in values]
    prompt = str(raw.get("prompt") or raw.get("text") or "")
    if not prompt:
        prompt = "اقرأ النص بصوت واضح." if interaction in READ else ("رتّب العناصر بالترتيب الصحيح." if interaction in ORDER else "اختر الإجابة المناسبة.")
    return {
        "order_index":order, "question_text":prompt, "instruction_text":_generic_instruction(interaction),
        "hint":_generic_hint(interaction), "encouragement":_encouragement(order), "stimulus":{},
        "expected_reading_text":str(expected) if expected is not None else None,
        "options":options, "media":[], "media_gaps":[],
    }


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
        step["hint"] = str(current.get("hint") or _generic_hint(str(current["interaction_type"])))
        step["encouragement"] = str(current.get("encouragement") or _encouragement(1))
        step["stimulus"] = deepcopy(current.get("stimulus") or {})
        if current.get("options") is not None:
            answer = current.get("correct_answer")
            answers = {str(v) for v in answer} if isinstance(answer, list) else {str(answer)}
            step["options"] = [{"text":str(v),"is_correct":str(v) in answers} for v in current.get("options", [])]
        item["interaction_type"] = str(current["interaction_type"])


def _apply_student_v2(items: dict[str, dict[str, Any]]) -> None:
    payload = _json(STUDENT_V2)
    for canonical, rounds in (payload.get("replacement_rounds") or {}).items():
        if canonical not in items:
            continue
        item = items[canonical]
        rebuilt = []
        for index, raw in enumerate(rounds, 1):
            values = [str(v) for v in raw.get("options", [])]
            answer = str(raw.get("answer") or "")
            rebuilt.append({
                "order_index":index, "question_text":str(raw.get("prompt") or "اختر الإجابة المناسبة."),
                "instruction_text":_generic_instruction(str(item["interaction_type"])),
                "hint":_generic_hint(str(item["interaction_type"])), "encouragement":_encouragement(index),
                "stimulus":{}, "expected_reading_text":None,
                "options":[{"text":v,"is_correct":v == answer} for v in values], "media":[], "media_gaps":[],
            })
        item["rounds"] = rebuilt
    for canonical, correction in (payload.get("explicit_corrections") or {}).items():
        if canonical in items and correction.get("interaction"):
            items[canonical]["interaction_type"] = str(correction["interaction"])


def _apply_auditory_story_source(items: dict[str, dict[str, Any]]) -> None:
    """Fold the approved L1 story replacement into the canonical release.

    The durable old visual-motor skill row is deliberately re-used by the
    publisher and renamed/re-keyed; no 45th academic skill is created.
    """
    payload = _json(AUDITORY_STORIES)
    for source_item in payload.get("items", []):
        canonical = str(source_item["canonical_id"])
        item = items[canonical]
        item["canonical_skill_code"] = "auditory_literal_comprehension"
        item["interaction_type"] = str(source_item["interaction_type"])
        source_rounds = list(source_item.get("rounds") or [])
        if len(source_rounds) != len(item["rounds"]):
            raise RuntimeError(f"{canonical}: auditory story round count mismatch")
        for step, raw in zip(item["rounds"], source_rounds, strict=True):
            step["question_text"] = str(raw.get("prompt") or step["question_text"])
            step["instruction_text"] = "اختر الإجابة الصحيحة اعتمادًا على ما فهمته من القصة."
            step["hint"] = str(raw.get("hint") or "تذكّر أحداث القصة التي استمعت إليها.")
            step["encouragement"] = _encouragement(int(step["order_index"]))


def _current_correct_text(step: dict[str, Any]) -> str:
    correct = [str(value["text"]) for value in step.get("options", []) if bool(value.get("is_correct"))]
    if len(correct) != 1:
        raise RuntimeError(f"Migration contract requires one current correct option, got {correct}")
    return correct[0]


def _apply_pool(step: dict[str, Any], pool: list[str], total: int) -> None:
    correct = _current_correct_text(step)
    correct_plain = _plain(correct)
    distractors = [value for value in pool if _plain(value) != correct_plain]
    if len(distractors) < total - 1:
        raise RuntimeError("Legacy approved pool has too few distractors")
    offset = max(0, int(step["order_index"]) - 1) % len(distractors)
    rotated = distractors[offset:] + distractors[:offset]
    desired = [correct]
    for value in rotated:
        if len(desired) >= total:
            break
        if _plain(value) not in {_plain(existing) for existing in desired}:
            desired.append(value)
    step["options"] = [{"text":value,"is_correct":index == 0} for index, value in enumerate(desired)]


def _word_image_asset(value: str) -> str | None:
    direct = WORD_IMAGE_ASSETS.get(value)
    if direct:
        return direct
    plain = _plain(value)
    return next((asset for label, asset in WORD_IMAGE_ASSETS.items() if _plain(label) == plain), None)


def _apply_legacy_maintenance(items: dict[str, dict[str, Any]]) -> None:
    for canonical, (pool, total) in LEGACY_POOLS.items():
        item = items.get(canonical)
        if not item:
            continue
        for step in item["rounds"]:
            _apply_pool(step, pool, total)

    for canonical, rounds in LEGACY_EXACT_CHOICES.items():
        item = items[canonical]
        if len(item["rounds"]) != len(rounds):
            raise RuntimeError(f"{canonical}: legacy maintenance round count mismatch")
        for step, desired in zip(item["rounds"], rounds, strict=True):
            step["options"] = [{"text":value,"is_correct":index == 0} for index, value in enumerate(desired)]

    segmentation = items["L3-REIN-01"]
    if len(segmentation["rounds"]) != len(LEGACY_SEGMENTATION):
        raise RuntimeError("L3-REIN-01: segmentation round count mismatch")
    for step, desired in zip(segmentation["rounds"], LEGACY_SEGMENTATION, strict=True):
        step["options"] = [{"text":value,"is_correct":index == 0} for index, value in enumerate(desired)]

    # The prior approved L1 word-image reinforcement already had an explicit
    # image bank. Keep that mapping in the compiled release instead of relying on
    # the retired maintenance seed.
    image_item = items.get("L1-REIN-03")
    if image_item:
        for step in image_item["rounds"]:
            media = []
            for index, option in enumerate(step["options"], 1):
                asset = _word_image_asset(str(option["text"]))
                if not asset:
                    raise RuntimeError(f"L1-REIN-03: no approved image for {option['text']!r}")
                media.append({
                    "asset_id":asset, "asset_type":"image", "usage":"choice",
                    "semantic_text":str(option["text"]), "option_order_index":index,
                })
            step["media"] = media


def _semantic_asset(spec: tuple[str, str, str, str], option_order: int | None = None) -> dict[str, Any]:
    asset_id, asset_type, usage, semantic = spec
    result = {"asset_id":asset_id,"asset_type":asset_type,"usage":usage,"semantic_text":semantic}
    if option_order is not None:
        result["option_order_index"] = option_order
    return result


def _apply_approval(items: dict[str, dict[str, Any]]) -> None:
    for canonical, question in {**PRETEST_QUESTIONS, **LEARNING_QUESTIONS, **POSTTEST_QUESTIONS}.items():
        item = items.get(canonical)
        if not item:
            raise RuntimeError(f"Approval references missing item {canonical}")
        for step in item["rounds"]:
            step["question_text"] = question
    for canonical, questions in LEARNING_ROUND_QUESTIONS.items():
        item = items[canonical]
        if len(item["rounds"]) != len(questions):
            raise RuntimeError(f"{canonical}: question round count mismatch")
        for step, question in zip(item["rounds"], questions, strict=True):
            step["question_text"] = question
    for canonical, stimuli in LEARNING_ROUND_STIMULI.items():
        item = items[canonical]
        if len(item["rounds"]) != len(stimuli):
            raise RuntimeError(f"{canonical}: stimulus round count mismatch")
        for step, text in zip(item["rounds"], stimuli, strict=True):
            step["stimulus"] = {"kind":"text","text":text}
    for canonical, rounds in OPTION_CONTRACTS.items():
        item = items[canonical]
        if len(item["rounds"]) != len(rounds):
            raise RuntimeError(f"{canonical}: option round count mismatch")
        for step, desired in zip(item["rounds"], rounds, strict=True):
            step["options"] = [{"text":text,"is_correct":correct} for text, correct in desired]
    for canonical, value in INTERACTION_OVERRIDES.items():
        items[canonical]["interaction_type"] = value
    for canonical, values in READING_TEXTS.items():
        item = items[canonical]
        if len(item["rounds"]) != len(values):
            raise RuntimeError(f"{canonical}: reading round count mismatch")
        for step, value in zip(item["rounds"], values, strict=True):
            step["expected_reading_text"] = value
            step["options"] = []
    for canonical, values in TIMED_WORD_SELECTIONS.items():
        item = items[canonical]
        if len(item["rounds"]) != len(values):
            raise RuntimeError(f"{canonical}: timed-word round count mismatch")
        for step, value in zip(item["rounds"], values, strict=True):
            step["expected_reading_text"] = value
            step["options"] = []
    for canonical, value in CRITERIA.items():
        items[canonical]["criterion"] = value
    for canonical, value in PRETEST_STIMULUS_OVERRIDES.items():
        items[canonical]["rounds"][0]["stimulus"] = deepcopy(value)
    for canonical, value in POSTTEST_STIMULUS_OVERRIDES.items():
        items[canonical]["rounds"][0]["stimulus"] = deepcopy(value)
    for canonical, intro in CONTEXT_INTROS.items():
        items[canonical]["context_intro"] = deepcopy(intro)
    for canonical, hint in LAYOUT_HINTS.items():
        items[canonical]["layout_hint"] = hint

    for canonical, by_round in STEP_MEDIA.items():
        item = items[canonical]
        steps = {int(step["order_index"]):step for step in item["rounds"]}
        for round_number, specs in by_round.items():
            step = steps[round_number]
            option_index = {visible_key(str(option["text"])):index for index, option in enumerate(step["options"], 1)}
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
    if interaction in {"choose_image", "listen_choose_image"} and not step.get("media_gaps"):
        if len(choice_images) != len(options):
            raise RuntimeError(f"{prefix}: image-choice is not 1:1 ({len(choice_images)}/{len(options)})")


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
