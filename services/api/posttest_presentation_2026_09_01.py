"""Pure structured posttest presentation source approved on 2026-09-01.

This is a migration/compiler input only. It contains no database access and is
never parsed by student requests. The 2026-09-08 approval contract is applied
after this source and therefore remains authoritative for changed question copy,
options, media and POST-Q11 semantics.
"""
from __future__ import annotations

POSTTEST_PRESENTATION = {
    "POST-Q01": {
        "skill": "تمييز الحرف بصريًا",
        "instruction_text": "انظر إلى الحروف المعروضة، ثم اختر الحرف المطلوب.",
        "encouragement": "ممتاز، ابدأ بثقة!",
        "stimulus": {"kind": "text", "text": "ت"},
    },
    "POST-Q02": {
        "skill": "التمييز بين الحروف المتشابهة بصريًا",
        "instruction_text": "انظر إلى الحروف جيدًا، ثم اختر الحرف المطلوب.",
        "encouragement": "رائع، أنت قادر عليها!",
        "stimulus": {"kind": "text", "text": "خ"},
    },
    "POST-Q03": {
        "skill": "التعرف إلى أشكال الحرف",
        "instruction_text": "لاحظ الحرف المعروض، ثم اختر شكله المناسب من الخيارات.",
        "encouragement": "أحسنت، واصل تقدمك!",
        "stimulus": {"kind": "text", "text": "س"},
    },
    "POST-Q04": {
        "skill": "ربط الصوت بالحرف",
        "instruction_text": "اضغط زر الاستماع، ثم اختر الحرف المطابق للصوت.",
        "encouragement": "ممتاز، ركّز في الصوت!",
        "stimulus": {"kind": "audio", "audio_target": "ق"},
    },
    "POST-Q05": {
        "skill": "تحديد الصوت الأول في الكلمة",
        "instruction_text": "اضغط زر الاستماع، ثم انظر إلى الصور واختر الصورة المناسبة.",
        "encouragement": "رائع، واصل!",
        "stimulus": {"kind": "audio", "audio_target": "ب"},
    },
    "POST-Q06": {
        "skill": "تحديد الصوت الأول في الكلمة المسموعة",
        "instruction_text": "اضغط زر الاستماع، ثم ركّز في أول صوت تسمعه واختر الحرف المناسب.",
        "encouragement": "أحسنت، أنت تتقدم!",
        "stimulus": {"kind": "audio", "audio_target": "نَخْلَة"},
    },
    "POST-Q07": {
        "skill": "تحديد الصوت الأخير في الكلمة المسموعة",
        "instruction_text": "اضغط زر الاستماع، ثم ركّز في آخر صوت تسمعه واختر الحرف المناسب.",
        "encouragement": "ممتاز، استمر!",
        "stimulus": {"kind": "audio", "audio_target": "قَمَر"},
    },
    "POST-Q08": {
        "skill": "مفاهيم المادة المطبوعة — تمييز الحرف",
        "instruction_text": "اختر العنصر الذي يمثل حرفًا واحدًا، وليس كلمة أو جملة كاملة.",
        "encouragement": "رائع، اختر بهدوء!",
        "stimulus": {"kind": "none"},
    },
    "POST-Q09": {
        "skill": "مفاهيم المادة المطبوعة — تمييز الكلمة",
        "instruction_text": "اختر العنصر الذي يمثل كلمة، وليس حرفًا منفردًا أو جملة كاملة.",
        "encouragement": "أحسنت، واصل!",
        "stimulus": {"kind": "none"},
    },
    "POST-Q10": {
        "skill": "فهم التسلسل وترتيب الأحداث",
        "instruction_text": "اضغط على الصورة التي حدثت أولًا، ثم الصورة التي بعدها، ثم الصورة الأخيرة.",
        "encouragement": "رائع، أنت جاهز لهذه الجولة!",
        "stimulus": {"kind": "none"},
    },
    "POST-Q11": {
        "skill": "تمييز الحركات القصيرة",
        "instruction_text": "اضغط زر الاستماع، ثم اختر المقطع المطابق للصوت.",
        "encouragement": "ممتاز، واصل تقدمك!",
        # Historical Sep-01 value. Sep-08 contract must override this to مَ.
        "stimulus": {"kind": "audio", "audio_target": "مِ"},
    },
    "POST-Q12": {
        "skill": "التمييز بين الصوت القصير والصوت الطويل",
        "instruction_text": "اضغط زر الاستماع، ثم اختر المقطع المطابق للصوت.",
        "encouragement": "رائع، استمر بنفس الثقة!",
        "stimulus": {"kind": "audio", "audio_target": "نُو"},
    },
    "POST-Q13": {
        "skill": "دمج المقاطع لتكوين كلمة",
        "instruction_text": "اضغط على المقطع الأول، ثم اضغط على المقطع الثاني لإكمال الكلمة.",
        "encouragement": "أحسنت، أنت تتقدم خطوة خطوة!",
        "stimulus": {"kind": "text", "text": "مَكْتَب"},
    },
    "POST-Q14": {
        "skill": "بناء كلمة من حروف",
        "instruction_text": "ابدأ بالحرف الأول من كلمة «نَخْلَة»، ثم أكمل الحروف بالترتيب.",
        "encouragement": "ممتاز، ركّز في اسم الصورة!",
        "stimulus": {"kind": "image", "text": "نَخْلَة"},
    },
    "POST-Q15": {
        "skill": "ترتيب الحروف لتكوين كلمة",
        "instruction_text": "اضغط على الحروف بالترتيب الصحيح حتى تكتمل الكلمة.",
        "encouragement": "رائع، رتّبها بهدوء!",
        "stimulus": {"kind": "text", "text": "فِيل"},
    },
    "POST-Q16": {
        "skill": "إكمال الكلمة بحرف ناقص",
        "instruction_text": "اقرأ ما قبل الفراغ وما بعده، ثم اختر الحرف المناسب.",
        "encouragement": "أحسنت، ركّز في شكل الكلمة!",
        "stimulus": {"kind": "text", "text": "بَـ _ ـر"},
    },
    "POST-Q17": {
        "skill": "ربط الكلمة المكتوبة بالصورة",
        "instruction_text": "انظر إلى الكلمة جيدًا، ثم اختر الصورة التي تدل عليها.",
        "encouragement": "ممتاز، واصل!",
        "stimulus": {"kind": "text", "text": "قَمَر"},
    },
    "POST-Q18": {
        "skill": "مطابقة الكلمة المسموعة بالكلمة المكتوبة",
        "instruction_text": "اضغط زر الاستماع، ثم اختر الكلمة المطابقة للصوت.",
        "encouragement": "رائع، أنت تقوم بعمل جميل!",
        "stimulus": {"kind": "audio", "audio_target": "سُوق"},
    },
    "POST-Q19": {
        "skill": "قراءة كلمة",
        "instruction_text": "اضغط زر التسجيل، اقرأ الكلمة المعروضة، ثم أرسل التسجيل.",
        "encouragement": "ممتاز، اقرأ بثقة!",
        "stimulus": {"kind": "reading", "text": "رَسَمَ"},
        "expected_reading_text": "رَسَمَ",
    },
    "POST-Q20": {
        "skill": "قراءة كلمة تحتوي على سكون",
        "instruction_text": "اضغط زر التسجيل، اقرأ الكلمة المعروضة، ثم أرسل التسجيل.",
        "encouragement": "رائع، واصل تقدمك!",
        "stimulus": {"kind": "reading", "text": "نَجْم"},
        "expected_reading_text": "نَجْم",
    },
    "POST-Q21": {
        "skill": "قراءة كلمة تحتوي على مد",
        "instruction_text": "اضغط زر التسجيل، اقرأ الكلمة المعروضة، ثم أرسل التسجيل.",
        "encouragement": "أحسنت، أنت تتقدم!",
        "stimulus": {"kind": "reading", "text": "نُور"},
        "expected_reading_text": "نُور",
    },
    "POST-Q22": {
        "skill": "قراءة كلمة تحتوي على شدة",
        "instruction_text": "اضغط زر التسجيل، اقرأ الكلمة المعروضة، ثم أرسل التسجيل.",
        "encouragement": "ممتاز، اقرأ كما تراها!",
        "stimulus": {"kind": "reading", "text": "سُلَّم"},
        "expected_reading_text": "سُلَّم",
    },
    "POST-Q23": {
        "skill": "قراءة جملة قصيرة",
        "instruction_text": "اضغط زر التسجيل، اقرأ الجملة كاملة، ثم أرسل التسجيل.",
        "encouragement": "رائع، اقرأ الكلمات بالترتيب!",
        "stimulus": {"kind": "reading", "text": "تَلْعَبُ مَرْيَمُ بِالْكُرَةِ."},
        "expected_reading_text": "تَلْعَبُ مَرْيَمُ بِالْكُرَةِ.",
    },
    "POST-Q24": {
        "skill": "قراءة نص قصير وقياس الطلاقة",
        "instruction_text": "اضغط زر التسجيل، اقرأ النص كاملًا، ثم أرسل التسجيل.",
        "encouragement": "اقرأ بهدوء، وحاول أن تكون قراءتك واضحة.",
        "stimulus": {
            "kind": "reading",
            "text": "فِي صَبَاحٍ مُشْمِسٍ، ذَهَبَ مَاجِدٌ مَعَ وَالِدِهِ إِلَى الشَّاطِئِ. أَخَذَ دَلْوًا صَغِيرًا، وَحَمَلَ وَالِدُهُ مَاءً وَمِظَلَّةً. بَنَى مَاجِدٌ بَيْتًا مِنَ الرَّمْلِ، ثُمَّ جَمَعَ أَصْدَافًا مُلَوَّنَةً. قَبْلَ الْعَوْدَةِ، نَظَّفَا مَكَانَهُمَا.",
        },
        "expected_reading_text": "فِي صَبَاحٍ مُشْمِسٍ، ذَهَبَ مَاجِدٌ مَعَ وَالِدِهِ إِلَى الشَّاطِئِ. أَخَذَ دَلْوًا صَغِيرًا، وَحَمَلَ وَالِدُهُ مَاءً وَمِظَلَّةً. بَنَى مَاجِدٌ بَيْتًا مِنَ الرَّمْلِ، ثُمَّ جَمَعَ أَصْدَافًا مُلَوَّنَةً. قَبْلَ الْعَوْدَةِ، نَظَّفَا مَكَانَهُمَا.",
    },
    "POST-Q25": {
        "skill": "فهم معلومة مباشرة من النص",
        "instruction_text": "اقرأ السؤال، ثم اختر الإجابة الصحيحة من الخيارات.",
        "encouragement": "ممتاز، ابحث في بداية النص!",
        "stimulus": {"kind": "reference"},
    },
    "POST-Q26": {
        "skill": "فهم معلومة مباشرة من النص",
        "instruction_text": "اقرأ السؤال، ثم اختر الإجابة الصحيحة من الخيارات.",
        "encouragement": "رائع، واصل تقدمك!",
        "stimulus": {"kind": "reference"},
    },
    "POST-Q27": {
        "skill": "فهم معلومة مباشرة من النص",
        "instruction_text": "اقرأ السؤال، ثم اختر الإجابة الصحيحة من الخيارات.",
        "encouragement": "أحسنت، أنت قريب من النهاية!",
        "stimulus": {"kind": "reference"},
    },
    "POST-Q28": {
        "skill": "فهم استنتاجي من النص",
        "instruction_text": "فكّر في سبب هذا التصرف، ثم اختر الإجابة الأنسب.",
        "encouragement": "ممتاز، فكّر بثقة!",
        "stimulus": {"kind": "reference"},
    },
    "POST-Q29": {
        "skill": "ترتيب أحداث من نص مقروء",
        "instruction_text": "اضغط على الحدث الذي حدث أولًا، ثم الذي بعده، ثم الحدث الأخير.",
        "encouragement": "رائع، تذكّر تسلسل القصة!",
        "stimulus": {"kind": "reference"},
    },
    "POST-Q30": {
        "skill": "فهم معنى كلمة من السياق",
        "instruction_text": "اقرأ العبارة، ثم اختر معنى الكلمة من الخيارات.",
        "encouragement": "أحسنت، أكمل السؤال الأخير بثقة!",
        "stimulus": {"kind": "text", "text": "أَصْدَافًا مُلَوَّنَةً"},
    },
}

if set(POSTTEST_PRESENTATION) != {f"POST-Q{number:02d}" for number in range(1, 31)}:
    raise RuntimeError("Structured posttest presentation must cover POST-Q01..POST-Q30 exactly")
