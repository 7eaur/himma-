"""Pure learner-presentation policy carried forward from the approved Sep-01 R2 projection.

The Sep-08 content review changed questions/options/media selectively and explicitly
kept the current instruction separate from the question.  The historical R2 DB
overlay is therefore a migration reference only: this module freezes its approved
instruction, hint, and encouragement behavior as pure data/functions so the
canonical release can reproduce it without running any repair/projection seeder.

Questions, stimuli, options, correctness and media are intentionally NOT owned here.
Those come from the newer canonical approval contract and compiler.
"""
from __future__ import annotations

from typing import Any

READ = {"read_aloud", "timed_read_aloud"}
LISTEN = {"listen_choose_one", "listen_choose_image", "listen_choose_many"}

# Sep-01 item-level presentation fields. Question/skill values from the old
# projection are deliberately omitted: Sep-08 owns current questions and the
# canonical skill rows own current academic skill identity.
BASE_OVERRIDES: dict[str, dict[str, str]] = {
    "L1-CORE-01": {"instruction": "انظر إلى الحرف المطلوب، ثم اختره من الحروف المعروضة.", "hint": "ركّز على شكل الحرف وعدد النقاط ومكانها."},
    "L1-CORE-02": {"instruction": "اضغط زر الاستماع، ثم اختر الحرف المطابق للصوت.", "hint": "استمع مرة أخرى، وركّز في الصوت من بدايته."},
    "L1-CORE-03": {"instruction": "لاحظ الحرف المعروض، ثم اختر الشكل المناسب له من الخيارات.", "hint": "قارن بين الحرف المعروض والخيارات، وركّز في شكل الحرف."},
    "L1-CORE-04": {"instruction": "اضغط زر الاستماع، ثم انظر إلى الصور واختر الصورة المناسبة.", "hint": "قل أسماء الصور في ذهنك، ثم ركّز على أول صوت."},
    "L1-CORE-05": {"instruction": "اضغط زر الاستماع، ثم ركّز في نهاية الكلمة واختر آخر صوت.", "hint": "استمع إلى نهاية الكلمة جيدًا قبل أن تختار."},
    "L1-CORE-07": {"instruction": "انظر إلى العنصر، ثم اختر التصنيف المناسب.", "hint": "الحرف رمز واحد، والكلمة لفظ واحد، والجملة تعطي معنى كاملًا."},
    "L1-CORE-08": {"instruction": "شاهد الصور جيدًا، ثم اضغط «التالي» عندما تكون مستعدًا لإعادة ترتيبها.", "hint": "تذكّر الصورة الأولى، ثم التي بعدها."},
    "L1-CORE-10": {"instruction": "اضغط على ما حدث أولًا، ثم ما حدث بعده، ثم الحدث الأخير.", "hint": "ابدأ بالحدث الأول، ثم أكمل التسلسل خطوة خطوة."},
    "L1-REIN-10": {"instruction": "شاهد الصور جيدًا، ثم اضغط «التالي» عندما تكون مستعدًا لإعادة ترتيبها.", "hint": "تذكّر الصورة الأولى ثم الثانية."},
    "L2-CORE-01": {"instruction": "اضغط زر الاستماع، ثم اختر المقطع المطابق للصوت.", "hint": "ركّز على الحركة المسموعة في المقطع."},
    "L2-CORE-02": {"instruction": "اضغط زر التسجيل، اقرأ المقطع المعروض، ثم أرسل التسجيل.", "hint": "اقرأ الحرف مع حركته دون إضافة صوت آخر."},
    "L2-CORE-09": {"instruction": "اضغط الحروف بالترتيب الصحيح حتى تكتمل الكلمة.", "hint": "قل الكلمة في ذهنك، ثم ابدأ بالحرف الأول وأكمل بالترتيب."},
    "L2-CORE-10": {"instruction": "اضغط زر التسجيل، اقرأ الجملة المعروضة، ثم أرسل التسجيل.", "hint": "اقرأ الكلمات بالترتيب وبوضوح."},
    "L2-REIN-10": {"instruction": "اضغط زر الاستماع، ثم اختر الكتابة المطابقة.", "hint": "ركّز على صوت نهاية الكلمة."},
    "L2-REIN-11": {"instruction": "اضغط زر التسجيل، اقرأ الجملة، ثم أرسل التسجيل.", "hint": "اقرأ الكلمات ببطء ووضوح ثم صِلها في جملة واحدة."},
    "L3-CORE-01": {"instruction": "اضغط زر التسجيل، اقرأ الكلمة المعروضة، ثم أرسل التسجيل.", "hint": "اقرأ الحروف والحركات بهدوء دون استعجال."},
    "L3-CORE-02": {"instruction": "اضغط زر التسجيل، اقرأ العبارة المعروضة، ثم أرسل التسجيل.", "hint": "اقرأ الكلمات معًا بهدوء، ولا تفصل بينها كثيرًا."},
    "L3-CORE-03": {"instruction": "اضغط زر التسجيل، اقرأ الجملة كاملة، ثم أرسل التسجيل.", "hint": "اقرأ الكلمات بالترتيب وحافظ على معنى الجملة."},
    "L3-CORE-10": {"instruction": "اضغط على الحدث الأول، ثم الذي بعده، ثم الحدث الأخير.", "hint": "فكّر: ماذا حدث أولًا؟ ثم أكمل الأحداث بالترتيب."},
    "L3-REIN-11": {"instruction": "اقرأ الجملة أولًا، ثم السؤال، واختر الإجابة الصحيحة.", "hint": "ابحث داخل الجملة عن الكلمة التي تجيب عن السؤال."},
    "L3-REIN-12": {"instruction": "اضغط الكلمات بحسب ترتيبها الصحيح حتى تكتمل الجملة.", "hint": "ابدأ بالفعل، ثم أكمل من قام به وما يتعلق به."},
}

# The R2 structured projection superseded the corresponding Sep-01 base fields.
PROJECTION_OVERRIDES: dict[str, dict[str, str]] = {
    "L1-REIN-07": {
        "instruction": "انظر إلى الحرف، ثم اختر الشكل الصحيح له من الخيارات.",
        "hint": "ركّز في شكل الحرف نفسه، ولا تعتمد على موقعه فقط.",
    },
    "L1-REIN-09": {
        "instruction": "انظر إلى العنصر، ثم اختر التصنيف المناسب.",
        "hint": "لاحظ هل هو رمز واحد، كلمة واحدة، أم جملة كاملة.",
    },
    "L2-REIN-01": {
        "instruction": "انظر إلى الكلمة الناقصة، ثم اختر الحرف الذي يكملها.",
        "hint": "اقرأ ما يظهر من الكلمة، ثم جرّب الحرف الذي يجعلها كلمة صحيحة.",
    },
    "L2-REIN-09": {
        "instruction": "قارن بين الكلمتين، ثم اختر الكتابة الصحيحة للشدة.",
        "hint": "ركّز على موضع علامة الشدة فوق الحرف.",
    },
    "L3-CORE-07": {
        "instruction": "ارجع إلى النص، ثم اختر الإجابة الموجودة فيه.",
        "hint": "ابحث في النص عن المعلومة التي يطلبها السؤال.",
    },
    "L3-CORE-08": {
        "instruction": "اقرأ السؤال، ثم اختر الإجابة الأنسب اعتمادًا على النص.",
        "hint": "فكّر في معنى الحدث وما يدل عليه داخل النص.",
    },
    "L3-CORE-09": {
        "instruction": "انظر إلى الكلمة، ثم اختر معناها الصحيح.",
        "hint": "فكّر في معنى الكلمة داخل الجملة أو السياق الذي تعلمته.",
    },
    "L3-REIN-01": {
        "instruction": "انظر إلى الخيارات، ثم اختر التقسيم الذي يحافظ على وحدات المعنى.",
        "hint": "اجمع الكلمات التي تكوّن معنى واحدًا قبل الانتقال إلى الجزء التالي.",
    },
    "L3-REIN-02": {
        "instruction": "اقرأ المطلوب، ثم اختر الجملة التي تقدّم الدليل المناسب.",
        "hint": "ابحث عن الجملة التي تثبت المعنى المطلوب مباشرة.",
    },
    "L3-REIN-05": {
        "instruction": "اقرأ النص أو شاهده، ثم اختر العنوان الذي يلخص فكرته.",
        "hint": "اختر العنوان الذي يجمع الفكرة الأهم في النص.",
    },
    "L3-REIN-09": {
        "instruction": "اقرأ الجملة والسؤال، ثم اختر المعنى المناسب من الخيارات.",
        "hint": "استخدم معنى الجملة لتعرف المقصود من الكلمة.",
    },
}

# Student Experience v2 replaced the old sound-vs-word L1-CORE-06 semantics
# before the Sep-08 wording review. Preserve that corrected instruction/hint,
# not the stale Sep-01 item override.
SPECIAL_OVERRIDES: dict[str, dict[str, str]] = {
    "L1-CORE-06": {
        "instruction": "استمع إلى الكلمتين كاملتين، ثم قارن أول صوت في كل كلمة.",
        "hint": "ركّز على بداية الكلمة الأولى ثم بداية الكلمة الثانية.",
    },
}

# The R2 projection explicitly replaced an answer-revealing classification hint.
SAFE_HINT_OVERRIDES = {
    "L1-CORE-07": "لاحظ حجم العنصر وعدد الرموز والمسافات بين أجزائه، ثم اختر التصنيف المناسب.",
}

# These items were later replaced by approved auditory-story sources. Their
# per-round story hints/instructions already live in the canonical compiler and
# must not be overwritten by the superseded direction-reading Sep-01 metadata.
PRESERVE_STORY_ROUNDS = {"L1-CORE-09", "L1-REIN-11"}


def encouragement(index: int, total: int) -> str:
    """Freeze the current R2 motivational copy exactly, independent of DB state."""
    if total >= 8:
        if index == 1:
            return "ممتاز، ابدأ بثقة!"
        if index == 2:
            return "رائع، واصل!"
        if index == 3:
            return "أحسنت، تقدم جميل!"
        if index == total:
            return "رائع، أكملها بقوة!"
        if index == total - 1:
            return "ممتاز، أنت قريب جدًا!"
        if index >= total - 2:
            return "رائع، بقي القليل!"
        return "ممتاز، واصل بنفس الثقة!"
    phrases = [
        "ممتاز، أنت جاهز لهذه الجولة!",
        "رائع، واصل تقدمك!",
        "أحسنت، أنت تتقدم بشكل جميل!",
        "ممتاز، بقي القليل!",
        "رائع، أكمل الجولة الأخيرة بثقة!",
    ]
    if total <= 1:
        return "ممتاز، أنت قادر عليها!"
    pos = round((index - 1) * 4 / max(1, total - 1))
    return phrases[max(0, min(4, pos))]


def generic_instruction(interaction: str) -> str:
    if interaction in LISTEN:
        return "اضغط زر الاستماع، ثم اختر الإجابة المطابقة."
    if interaction in READ:
        return "اضغط زر التسجيل، اقرأ النص المعروض، ثم أرسل التسجيل."
    if interaction == "memory_sequence":
        return "شاهد الصور جيدًا، ثم اضغط «التالي» عندما تكون مستعدًا لإعادة ترتيبها."
    if interaction == "sequence":
        return "اضغط العناصر بحسب ترتيبها الصحيح."
    if interaction == "build_word":
        return "اضغط الحروف أو المقاطع بالترتيب حتى تكتمل الكلمة."
    if interaction in {"choose_image", "choose_many"}:
        return "انظر إلى العناصر المعروضة، ثم اختر المطلوب."
    return "اقرأ المطلوب، ثم اختر الإجابة المناسبة."


def generic_hint(interaction: str) -> str:
    if interaction == "memory_sequence":
        return "تذكّر الصورة الأولى، ثم التي بعدها."
    if interaction == "sequence":
        return "ابدأ بما حدث أولًا، ثم أكمل الترتيب خطوة خطوة."
    if interaction == "build_word":
        return "ابدأ بالحرف أو المقطع الذي تبدأ به الكلمة."
    if interaction in READ:
        return "اقرأ ببطء ووضوح، وركّز في الحروف والحركات."
    if interaction in LISTEN:
        return "استمع مرة أخرى، وركّز في الصوت المطلوب."
    if interaction in {"choose_image", "choose_many"}:
        return "انظر إلى كل عنصر بهدوء قبل أن تختار."
    return "اقرأ المطلوب بهدوء، ثم اختر الإجابة الأنسب."


def apply_learning_presentation(release: dict[str, Any]) -> None:
    """Apply only preserved Sep-01/R2 instruction, hint and encouragement fields.

    This runs after the Sep-08 academic compiler. It never changes a question,
    stimulus, option, correct answer, interaction, reading target, or media link.
    """
    learning = [
        item
        for item in release.get("items") or []
        if str(item.get("kind") or "") in {"core_activity", "reinforcement_activity"}
    ]
    if len(learning) != 65:
        raise RuntimeError(f"Expected 65 learning items for presentation projection, got {len(learning)}")

    for item in learning:
        canonical = str(item.get("canonical_id") or "")
        interaction = str(item.get("interaction_type") or "")
        rounds = list(item.get("rounds") or [])
        if not rounds:
            raise RuntimeError(f"{canonical}: no rounds for learning presentation")

        for step in rounds:
            round_number = int(step.get("order_index") or 0)
            step["encouragement"] = encouragement(round_number, len(rounds))

            # Story replacements own their per-round guidance and must remain
            # untouched apart from the common approved encouragement sequence.
            if canonical in PRESERVE_STORY_ROUNDS:
                continue

            override = dict(BASE_OVERRIDES.get(canonical, {}))
            override.update(PROJECTION_OVERRIDES.get(canonical, {}))
            override.update(SPECIAL_OVERRIDES.get(canonical, {}))

            step["instruction_text"] = str(
                override.get("instruction") or generic_instruction(interaction)
            )
            step["hint"] = str(
                SAFE_HINT_OVERRIDES.get(canonical)
                or override.get("hint")
                or generic_hint(interaction)
            )
