#!/usr/bin/env python3
"""
build_catalog.py — توليد كتالوج المحتوى الحقيقي لمنصة هِمّة
30 سؤال قبلي + 30 سؤال بعدي + 45 نشاط (30 أساسي + 15 تقوية)

التشغيل: python build_catalog.py
الناتج: packages/content/src/catalog.json (يستبدل الملف الحالي)
"""

import json, hashlib, os, uuid

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(ROOT, "packages", "content", "src", "catalog.json")

def stable_key(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, "himma.v1." + ".".join(str(p) for p in parts)))

def skill_key(level_id, skill_name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"himma.skill.{level_id}.{skill_name}"))

# ─── المهارات الثلاثة ─────────────────────────────────────────────────────────
LEVELS = {
    1: {"name": "الاستعداد للقراءة", "skills": [
        "تمييز الحرف بصرياً",
        "تمييز الحروف المتشابهة",
        "مطابقة شكل الحرف",
        "تسمية الحرف",
        "ترتيب الحروف",
    ]},
    2: {"name": "بناء الكلمة", "skills": [
        "تركيب المقطع",
        "تحليل الكلمة لمقاطع",
        "قراءة كلمة بسيطة",
        "مطابقة الكلمة بالصورة",
        "كتابة كلمة مسموعة",
    ]},
    3: {"name": "الطلاقة والفهم", "skills": [
        "قراءة جملة قصيرة",
        "فهم جملة مقروءة",
        "طلاقة القراءة",
        "قراءة قصة قصيرة",
        "فهم النص",
    ]},
}

# بيانات المحتوى الحقيقية — أسئلة قبلية (30)
PRETEST_QUESTIONS = [
    # المستوى 1 — الاستعداد للقراءة (10 أسئلة)
    {"level": 1, "skill": "تمييز الحرف بصرياً", "prompt": "اضغط على الحرف «ب»", "options": ["ت","ب","ث","ن"], "answer": "ب", "vocab_img": None},
    {"level": 1, "skill": "تمييز الحروف المتشابهة", "prompt": "اضغط على الحرف «ج»", "options": ["ح","خ","ج","ع"], "answer": "ج", "vocab_img": None},
    {"level": 1, "skill": "مطابقة شكل الحرف", "prompt": "أيّ شكل يمثّل حرف «م»؟", "options": ["مـ","سـ","لـ","بـ"], "answer": "مـ", "vocab_img": None},
    {"level": 1, "skill": "تسمية الحرف", "prompt": "ما اسم هذا الحرف: «ص»؟", "options": ["سين","صاد","ضاد","شين"], "answer": "صاد", "vocab_img": None},
    {"level": 1, "skill": "ترتيب الحروف", "prompt": "أيّ الحروف يأتي بعد «أ» مباشرةً؟", "options": ["ت","ج","ب","ث"], "answer": "ب", "vocab_img": None},
    {"level": 1, "skill": "تمييز الحرف بصرياً", "prompt": "اضغط على الحرف «ر»", "options": ["ز","ر","و","ن"], "answer": "ر", "vocab_img": None},
    {"level": 1, "skill": "تمييز الحروف المتشابهة", "prompt": "اضغط على الحرف «ض»", "options": ["ص","ض","ظ","ط"], "answer": "ض", "vocab_img": None},
    {"level": 1, "skill": "مطابقة شكل الحرف", "prompt": "أيّ شكل يمثّل حرف «ك» في وسط الكلمة؟", "options": ["كـ","نـ","فـ","ـكـ"], "answer": "ـكـ", "vocab_img": None},
    {"level": 1, "skill": "تسمية الحرف", "prompt": "ما اسم هذا الحرف: «ع»؟", "options": ["غين","عين","همزة","خاء"], "answer": "عين", "vocab_img": None},
    {"level": 1, "skill": "ترتيب الحروف", "prompt": "ما الحرف الثامن في الهجاء العربي؟", "options": ["د","ذ","ح","ط"], "answer": "ح", "vocab_img": None},

    # المستوى 2 — بناء الكلمة (10 أسئلة)
    {"level": 2, "skill": "تركيب المقطع", "prompt": "أيّ مقطع يصنعه الحرف «ب» مع الفتحة؟", "options": ["بِ","بُ","بَ","بْ"], "answer": "بَ", "vocab_img": None},
    {"level": 2, "skill": "تحليل الكلمة لمقاطع", "prompt": "كم مقطعاً في كلمة «كِتَاب»؟", "options": ["2","3","4","1"], "answer": "3", "vocab_img": None},
    {"level": 2, "skill": "قراءة كلمة بسيطة", "prompt": "اقرأ: كلمة م-و-ز. ما هي؟", "options": ["موج","موز","مور","موس"], "answer": "موز", "vocab_img": "hem-voc-01-banana-1024.png"},
    {"level": 2, "skill": "مطابقة الكلمة بالصورة", "prompt": "هذه صورة 📖. ما الكلمة المناسبة؟", "options": ["قلم","كتاب","باب","شجرة"], "answer": "كتاب", "vocab_img": "hem-voc-02-book-1024.png"},
    {"level": 2, "skill": "تركيب المقطع", "prompt": "أيّ مقطع يصنعه «س» مع الكسرة؟", "options": ["سَ","سِ","سُ","سْ"], "answer": "سِ", "vocab_img": None},
    {"level": 2, "skill": "قراءة كلمة بسيطة", "prompt": "اقرأ: ب-ا-ب. ما هي؟", "options": ["باب","ناب","داب","راب"], "answer": "باب", "vocab_img": "hem-voc-03-door-1024.png"},
    {"level": 2, "skill": "مطابقة الكلمة بالصورة", "prompt": "هذه صورة ✏️. ما الكلمة المناسبة؟", "options": ["مسطرة","قلم","ممحاة","كراسة"], "answer": "قلم", "vocab_img": "hem-voc-04-pencil-1024.png"},
    {"level": 2, "skill": "تحليل الكلمة لمقاطع", "prompt": "كم مقطعاً في كلمة «شَمْس»؟", "options": ["1","2","3","4"], "answer": "2", "vocab_img": None},
    {"level": 2, "skill": "قراءة كلمة بسيطة", "prompt": "اقرأ: س-م-ك. ما هي؟", "options": ["سمر","سمك","سمع","سمن"], "answer": "سمك", "vocab_img": "hem-voc-05-fish-1024.png"},
    {"level": 2, "skill": "مطابقة الكلمة بالصورة", "prompt": "هذه صورة 🌞. ما الكلمة المناسبة؟", "options": ["قمر","نجم","شمس","سحاب"], "answer": "شمس", "vocab_img": "hem-voc-06-sun-1024.png"},

    # المستوى 3 — الطلاقة والفهم (10 أسئلة)
    {"level": 3, "skill": "قراءة جملة قصيرة", "prompt": "اقرأ: «الولد يلعب». ماذا يفعل الولد؟", "options": ["يأكل","يلعب","ينام","يقرأ"], "answer": "يلعب", "vocab_img": None},
    {"level": 3, "skill": "فهم جملة مقروءة", "prompt": "«البنت تشرب الماء». ماذا تشرب البنت؟", "options": ["عصير","حليب","ماء","شاي"], "answer": "ماء", "vocab_img": None},
    {"level": 3, "skill": "طلاقة القراءة", "audio_prompt": True, "prompt": "اقرأ الجملة بصوت عالٍ: «الشمس تشرق في الصباح»", "reading_text": "الشمس تشرق في الصباح", "options": [], "answer": None, "vocab_img": None},
    {"level": 3, "skill": "قراءة قصة قصيرة", "prompt": "«ذهب علي إلى المدرسة وحمل حقيبته». ماذا حمل علي؟", "options": ["كتاباً","حقيبته","قلماً","طعاماً"], "answer": "حقيبته", "vocab_img": "hem-voc-17-school-bag-1024.png"},
    {"level": 3, "skill": "فهم النص", "prompt": "«لعب الأطفال في الحديقة». أين لعب الأطفال؟", "options": ["البيت","المدرسة","الحديقة","الشارع"], "answer": "الحديقة", "vocab_img": "hem-voc-21-garden-1024.png"},
    {"level": 3, "skill": "قراءة جملة قصيرة", "audio_prompt": True, "prompt": "اقرأ بصوت عالٍ: «القمر يضيء الليل»", "reading_text": "القمر يضيء الليل", "options": [], "answer": None, "vocab_img": "hem-voc-07-moon-1024.png"},
    {"level": 3, "skill": "فهم جملة مقروءة", "prompt": "«الطير يطير في السماء». ماذا يفعل الطير؟", "options": ["يسبح","يطير","يمشي","يأكل"], "answer": "يطير", "vocab_img": "hem-voc-20-bird-1024.png"},
    {"level": 3, "skill": "طلاقة القراءة", "audio_prompt": True, "prompt": "اقرأ بصوت عالٍ: «الشجرة كبيرة وجميلة»", "reading_text": "الشجرة كبيرة وجميلة", "options": [], "answer": None, "vocab_img": "hem-voc-08-tree-1024.png"},
    {"level": 3, "skill": "قراءة قصة قصيرة", "prompt": "«سارت سارة إلى المكتبة لتقرأ كتاباً». لماذا ذهبت سارة؟", "options": ["للعب","للقراءة","للأكل","للنوم"], "answer": "للقراءة", "vocab_img": "hem-voc-22-library-1024.png"},
    {"level": 3, "skill": "فهم النص", "prompt": "«نمت الأسرة باكراً لأنّ الغد يوم مدرسة». متى نامت الأسرة؟", "options": ["متأخراً","باكراً","في النهار","في المساء"], "answer": "باكراً", "vocab_img": None},
]

# بيانات أسئلة بعدية (30) — مختلفة بالمفردات والصور لكن موازية بالمهارة
POSTTEST_QUESTIONS = [
    # المستوى 1 (10)
    {"level": 1, "skill": "تمييز الحرف بصرياً", "prompt": "اضغط على الحرف «د»", "options": ["ذ","ز","د","ر"], "answer": "د", "vocab_img": None},
    {"level": 1, "skill": "تمييز الحروف المتشابهة", "prompt": "اضغط على الحرف «ف»", "options": ["ق","ف","و","ن"], "answer": "ف", "vocab_img": None},
    {"level": 1, "skill": "مطابقة شكل الحرف", "prompt": "أيّ شكل يمثّل حرف «ع» في البداية؟", "options": ["عـ","غـ","ضـ","صـ"], "answer": "عـ", "vocab_img": None},
    {"level": 1, "skill": "تسمية الحرف", "prompt": "ما اسم هذا الحرف: «ظ»؟", "options": ["طاء","ضاد","ظاء","ذال"], "answer": "ظاء", "vocab_img": None},
    {"level": 1, "skill": "ترتيب الحروف", "prompt": "أيّ الحروف يأتي قبل «ت» مباشرةً؟", "options": ["أ","ب","ث","ج"], "answer": "ب", "vocab_img": None},
    {"level": 1, "skill": "تمييز الحرف بصرياً", "prompt": "اضغط على الحرف «ل»", "options": ["ن","ل","ر","و"], "answer": "ل", "vocab_img": None},
    {"level": 1, "skill": "تمييز الحروف المتشابهة", "prompt": "اضغط على الحرف «ط»", "options": ["ض","ظ","ط","ص"], "answer": "ط", "vocab_img": None},
    {"level": 1, "skill": "مطابقة شكل الحرف", "prompt": "أيّ شكل يمثّل حرف «ف» في النهاية؟", "options": ["ـف","ـق","ـو","ـن"], "answer": "ـف", "vocab_img": None},
    {"level": 1, "skill": "تسمية الحرف", "prompt": "ما اسم هذا الحرف: «ق»؟", "options": ["كاف","فاء","قاف","غين"], "answer": "قاف", "vocab_img": None},
    {"level": 1, "skill": "ترتيب الحروف", "prompt": "ما الحرف الخامس عشر في الهجاء؟", "options": ["ن","م","ل","ك"], "answer": "ل", "vocab_img": None},

    # المستوى 2 (10)
    {"level": 2, "skill": "تركيب المقطع", "prompt": "أيّ مقطع يصنعه «ل» مع الضمة؟", "options": ["لَ","لِ","لُ","لْ"], "answer": "لُ", "vocab_img": None},
    {"level": 2, "skill": "تحليل الكلمة لمقاطع", "prompt": "كم مقطعاً في كلمة «مَدْرَسَة»؟", "options": ["2","3","4","5"], "answer": "4", "vocab_img": None},
    {"level": 2, "skill": "قراءة كلمة بسيطة", "prompt": "اقرأ: ق-م-ر. ما هي؟", "options": ["قمر","قمص","قمع","قمة"], "answer": "قمر", "vocab_img": "hem-voc-07-moon-1024.png"},
    {"level": 2, "skill": "مطابقة الكلمة بالصورة", "prompt": "هذه صورة 🌊. ما الكلمة المناسبة؟", "options": ["بحر","نهر","بحيرة","خليج"], "answer": "بحر", "vocab_img": "hem-voc-24-sea-1024.png"},
    {"level": 2, "skill": "تركيب المقطع", "prompt": "أيّ مقطع يصنعه «م» مع السكون؟", "options": ["مَ","مِ","مُ","مْ"], "answer": "مْ", "vocab_img": None},
    {"level": 2, "skill": "قراءة كلمة بسيطة", "prompt": "اقرأ: ن-ج-م. ما هي؟", "options": ["نجم","نجر","نجل","نجح"], "answer": "نجم", "vocab_img": "hem-voc-14-star-1024.png"},
    {"level": 2, "skill": "مطابقة الكلمة بالصورة", "prompt": "هذه صورة 🐱. ما الكلمة المناسبة؟", "options": ["كلب","قطة","بقرة","دجاجة"], "answer": "قطة", "vocab_img": "hem-voc-16-cat-1024.png"},
    {"level": 2, "skill": "تحليل الكلمة لمقاطع", "prompt": "كم مقطعاً في كلمة «بَيْت»؟", "options": ["1","2","3","4"], "answer": "2", "vocab_img": None},
    {"level": 2, "skill": "قراءة كلمة بسيطة", "prompt": "اقرأ: ط-ي-ر. ما هي؟", "options": ["طير","طيب","طيف","طير"], "answer": "طير", "vocab_img": "hem-voc-20-bird-1024.png"},
    {"level": 2, "skill": "مطابقة الكلمة بالصورة", "prompt": "هذه صورة 🏫. ما الكلمة المناسبة؟", "options": ["بيت","مدرسة","مستشفى","دكان"], "answer": "مدرسة", "vocab_img": "hem-voc-18-school-1024.png"},

    # المستوى 3 (10)
    {"level": 3, "skill": "قراءة جملة قصيرة", "prompt": "اقرأ: «البنت تقرأ الكتاب». ماذا تفعل البنت؟", "options": ["تكتب","تقرأ","تلعب","تأكل"], "answer": "تقرأ", "vocab_img": None},
    {"level": 3, "skill": "فهم جملة مقروءة", "prompt": "«الولد يأكل التفاح». ماذا يأكل الولد؟", "options": ["برتقالاً","تفاحاً","موزاً","عنباً"], "answer": "تفاحاً", "vocab_img": None},
    {"level": 3, "skill": "طلاقة القراءة", "audio_prompt": True, "prompt": "اقرأ بصوت عالٍ: «الطير يغرد في الصباح»", "reading_text": "الطير يغرد في الصباح", "options": [], "answer": None, "vocab_img": "hem-voc-20-bird-1024.png"},
    {"level": 3, "skill": "قراءة قصة قصيرة", "prompt": "«ذهبت ليلى إلى الشاطئ وبنت قصراً من الرمال». ماذا بنت ليلى؟", "options": ["بيتاً","قصراً من الرمال","برجاً","سداً"], "answer": "قصراً من الرمال", "vocab_img": "hem-voc-23-beach-1024.png"},
    {"level": 3, "skill": "فهم النص", "prompt": "«زرع المزارع البذور في الربيع». متى زرع المزارع؟", "options": ["الصيف","الشتاء","الخريف","الربيع"], "answer": "الربيع", "vocab_img": "hem-voc-29-seed-1024.png"},
    {"level": 3, "skill": "قراءة جملة قصيرة", "audio_prompt": True, "prompt": "اقرأ بصوت عالٍ: «الأسرة تجلس معاً»", "reading_text": "الأسرة تجلس معاً", "options": [], "answer": None, "vocab_img": "hem-voc-33-family-1024.png"},
    {"level": 3, "skill": "فهم جملة مقروءة", "prompt": "«تنمو الأشجار في الحديقة». أين تنمو الأشجار؟", "options": ["الصحراء","الحديقة","البحر","المدينة"], "answer": "الحديقة", "vocab_img": "hem-voc-21-garden-1024.png"},
    {"level": 3, "skill": "طلاقة القراءة", "audio_prompt": True, "prompt": "اقرأ بصوت عالٍ: «الوادي عميق وجميل»", "reading_text": "الوادي عميق وجميل", "options": [], "answer": None, "vocab_img": "hem-voc-32-valley-1024.png"},
    {"level": 3, "skill": "قراءة قصة قصيرة", "prompt": "«جمع الأطفال الأصداف على الشاطئ». ماذا جمع الأطفال؟", "options": ["الحجارة","الأصداف","الأسماك","الرمال"], "answer": "الأصداف", "vocab_img": "hem-voc-26-shells-1024.png"},
    {"level": 3, "skill": "فهم النص", "prompt": "«في المكتبة كتب كثيرة ومتنوعة». أين الكتب؟", "options": ["الفصل","الحديقة","المكتبة","البيت"], "answer": "المكتبة", "vocab_img": "hem-voc-22-library-1024.png"},
]

# الأنشطة الأساسية (30 = 10 لكل مستوى) + التقوية (15 = 5 لكل مستوى)
ACTIVITIES = []

# ─── المستوى 1: الاستعداد للقراءة ─────────────────────────
# 10 أساسية
l1_core = [
    {"skill": "تمييز الحرف بصرياً", "type": "core_activity", "prompt": "اضغط على جميع حروف «ب» في الصف", "options": ["ب","ت","ب","ث","ب","ن"], "answer": ["ب","ب","ب"], "audio": "LET-01.mp3"},
    {"skill": "تمييز الحروف المتشابهة", "type": "core_activity", "prompt": "ميّز بين «ح» و«خ» و«ج»: اضغط على «ح»", "options": ["ج","ح","خ","ح","ج","ح"], "answer": ["ح","ح","ح"], "audio": "LET-02.mp3"},
    {"skill": "مطابقة شكل الحرف", "type": "core_activity", "prompt": "طابق الحرف «ن» في أشكاله المختلفة", "options": ["نـ","ـنـ","ـن","ن"], "answer": ["نـ","ـنـ","ـن","ن"], "audio": "LET-03.mp3"},
    {"skill": "تسمية الحرف", "type": "core_activity", "prompt": "سمّ الحرف: «ش»", "options": ["سين","شين","صاد","ثاء"], "answer": "شين", "audio": "LET-04.mp3"},
    {"skill": "ترتيب الحروف", "type": "core_activity", "prompt": "رتّب الحروف: ج، ب، أ", "options": ["أ،ب،ج","ب،أ،ج","ج،أ،ب","أ،ج،ب"], "answer": "أ،ب،ج", "audio": "LET-05.mp3"},
    {"skill": "تمييز الحرف بصرياً", "type": "core_activity", "prompt": "اضغط على حرف «ع» في كل مكان", "options": ["ع","غ","ع","خ","ع","ه"], "answer": ["ع","ع","ع"], "audio": "LET-06.mp3"},
    {"skill": "تمييز الحروف المتشابهة", "type": "core_activity", "prompt": "ميّز «ص» من «ض» و«ط» و«ظ»", "options": ["ط","ص","ض","ظ","ص","ط"], "answer": ["ص","ص"], "audio": "LET-01.mp3"},
    {"skill": "مطابقة شكل الحرف", "type": "core_activity", "prompt": "طابق حرف «ف» في موضعه الصحيح في الكلمة «فُطُور»", "options": ["فـ","ـف","ف","ـفـ"], "answer": "فـ", "audio": "LET-02.mp3"},
    {"skill": "تسمية الحرف", "type": "core_activity", "prompt": "سمّ الحرف: «خ»", "options": ["حاء","خاء","جيم","غين"], "answer": "خاء", "audio": "LET-03.mp3"},
    {"skill": "ترتيب الحروف", "type": "core_activity", "prompt": "أيّ الحروف يأتي بين «ث» و«ح»؟", "options": ["ج","ب","د","ذ"], "answer": "ج", "audio": "LET-04.mp3"},
]
# 5 تقوية المستوى 1
l1_reinf = [
    {"skill": "تمييز الحرف بصرياً", "type": "reinforcement_activity", "prompt": "تقوية: اضغط على كل حرف «أ» مختلف الشكل", "options": ["إ","أ","آ","ا"], "answer": ["إ","أ","آ","ا"], "audio": "LET-05.mp3"},
    {"skill": "تمييز الحروف المتشابهة", "type": "reinforcement_activity", "prompt": "تقوية: ميّز «ز» من «ر» و«و» و«ن»", "options": ["ن","ز","ر","و","ز"], "answer": ["ز","ز"], "audio": "LET-06.mp3"},
    {"skill": "مطابقة شكل الحرف", "type": "reinforcement_activity", "prompt": "تقوية: طابق «ق» في نهاية الكلمة", "options": ["ـق","ـك","ـف","ـب"], "answer": "ـق", "audio": "LET-01.mp3"},
    {"skill": "تسمية الحرف", "type": "reinforcement_activity", "prompt": "تقوية: سمّ الحرف: «ل»", "options": ["نون","لام","راء","واو"], "answer": "لام", "audio": "LET-02.mp3"},
    {"skill": "ترتيب الحروف", "type": "reinforcement_activity", "prompt": "تقوية: رتّب: ه، و، ن", "options": ["ن،و،ه","ه،و،ن","و،ن،ه","ن،ه،و"], "answer": "ه،و،ن", "audio": "LET-03.mp3"},
]

# ─── المستوى 2: بناء الكلمة ─────────────────────────────────
l2_core = [
    {"skill": "تركيب المقطع", "type": "core_activity", "prompt": "ما الكلمة؟ بَ + يْ + ت", "options": ["بات","بيت","بوت","بتة"], "answer": "بيت", "audio": "SYL-01.mp3"},
    {"skill": "تحليل الكلمة لمقاطع", "type": "core_activity", "prompt": "قسّم كلمة «مَدَّ» إلى مقاطع", "options": ["مَ-دَّ","مَدَّ","م-د-ّ","مَدْ-دَ"], "answer": "مَدْ-دَ", "audio": "SYL-02.mp3"},
    {"skill": "قراءة كلمة بسيطة", "audio_prompt": True, "type": "core_activity", "prompt": "اقرأ بصوت: «نَخْلَة»", "reading_text": "نَخْلَة", "options": [], "answer": None, "audio": "SYL-03.mp3", "vocab_img": "hem-voc-09-palm-tree-1024.png"},
    {"skill": "مطابقة الكلمة بالصورة", "type": "core_activity", "prompt": "صورة 🏀 — اختر الكلمة الصحيحة", "options": ["كرة","قدم","لعب","كأس"], "answer": "كرة", "audio": "SYL-04.mp3", "vocab_img": "hem-voc-10-ball-1024.png"},
    {"skill": "كتابة كلمة مسموعة", "audio_prompt": True, "type": "core_activity", "prompt": "استمع ثم اختر: «زهرة»", "reading_text": "زهرة", "options": ["زهرة","زهور","زيرة","زهور"], "answer": "زهرة", "audio": "WRD-01.mp3", "vocab_img": "hem-voc-28-flower-1024.png"},
    {"skill": "تركيب المقطع", "type": "core_activity", "prompt": "ما الكلمة؟ كِ + تَ + ب", "options": ["كتب","كتاب","كتبة","كتبت"], "answer": "كتب", "audio": "SYL-05.mp3"},
    {"skill": "تحليل الكلمة لمقاطع", "type": "core_activity", "prompt": "قسّم كلمة «وَلَد» إلى مقاطع", "options": ["وَ-لَد","وَل-دَ","وَلَ-د","و-ل-د"], "answer": "وَ-لَد", "audio": "SYL-06.mp3"},
    {"skill": "قراءة كلمة بسيطة", "audio_prompt": True, "type": "core_activity", "prompt": "اقرأ بصوت: «ضَوْء»", "reading_text": "ضَوْء", "options": [], "answer": None, "audio": "SYL-07.mp3", "vocab_img": "hem-voc-15-light-1024.png"},
    {"skill": "مطابقة الكلمة بالصورة", "type": "core_activity", "prompt": "صورة 💧 — اختر الكلمة", "options": ["ماء","عصير","لبن","مشروب"], "answer": "ماء", "audio": "SYL-08.mp3", "vocab_img": "hem-voc-11-glass-of-water-1024.png"},
    {"skill": "كتابة كلمة مسموعة", "audio_prompt": True, "type": "core_activity", "prompt": "استمع ثم اختر: «بطة»", "reading_text": "بطة", "options": ["بطة","بطبط","بطيخ","بطاء"], "answer": "بطة", "audio": "WRD-02.mp3", "vocab_img": "hem-voc-12-duck-1024.png"},
]
l2_reinf = [
    {"skill": "تركيب المقطع", "type": "reinforcement_activity", "prompt": "تقوية: ما الكلمة؟ سَ + يَّ + ار + ة", "options": ["سيارة","سيرة","سارة","سيار"], "answer": "سيارة", "audio": "SYL-09.mp3", "vocab_img": "hem-voc-13-car-1024.png"},
    {"skill": "تحليل الكلمة لمقاطع", "type": "reinforcement_activity", "prompt": "تقوية: كم مقطعاً في «حَقِيبَة»؟", "options": ["2","3","4","5"], "answer": "4", "audio": "SYL-10.mp3"},
    {"skill": "قراءة كلمة بسيطة", "audio_prompt": True, "type": "reinforcement_activity", "prompt": "تقوية: اقرأ بصوت: «مَعْلَمَة»", "reading_text": "مَعْلَمَة", "options": [], "answer": None, "audio": "SYL-11.mp3", "vocab_img": "hem-voc-19-teacher-1024.png"},
    {"skill": "مطابقة الكلمة بالصورة", "type": "reinforcement_activity", "prompt": "تقوية: صورة 🌸 — اختر الكلمة", "options": ["وردة","شجرة","عشب","بذرة"], "answer": "وردة", "audio": "SYL-12.mp3", "vocab_img": "hem-voc-28-flower-1024.png"},
    {"skill": "كتابة كلمة مسموعة", "audio_prompt": True, "type": "reinforcement_activity", "prompt": "تقوية: استمع ثم اختر: «حقيبة المدرسة»", "reading_text": "حقيبة المدرسة", "options": ["حقيبة المدرسة","كتاب المدرسة","قلم المدرسة","دفتر المدرسة"], "answer": "حقيبة المدرسة", "audio": "WRD-03.mp3", "vocab_img": "hem-voc-17-school-bag-1024.png"},
]

# ─── المستوى 3: الطلاقة والفهم ──────────────────────────────
l3_core = [
    {"skill": "قراءة جملة قصيرة", "audio_prompt": True, "type": "core_activity", "prompt": "اقرأ بصوت: «الولد يحب الكتب»", "reading_text": "الولد يحب الكتب", "options": [], "answer": None, "audio": "WRD-04.mp3"},
    {"skill": "فهم جملة مقروءة", "type": "core_activity", "prompt": "«الأم تطبخ في المطبخ». أين الأم؟", "options": ["الغرفة","المطبخ","الحديقة","الشارع"], "answer": "المطبخ", "audio": "WRD-05.mp3"},
    {"skill": "طلاقة القراءة", "audio_prompt": True, "type": "core_activity", "prompt": "اقرأ بطلاقة: «ذهب أحمد إلى المدرسة مبكراً»", "reading_text": "ذهب أحمد إلى المدرسة مبكراً", "options": [], "answer": None, "audio": "WRD-06.mp3", "vocab_img": "hem-voc-18-school-1024.png"},
    {"skill": "قراءة قصة قصيرة", "audio_prompt": True, "type": "core_activity", "prompt": "اقرأ: «في الصباح ذهبت نور إلى الحديقة»", "reading_text": "في الصباح ذهبت نور إلى الحديقة", "options": [], "answer": None, "audio": "WRD-07.mp3", "vocab_img": "hem-voc-21-garden-1024.png"},
    {"skill": "فهم النص", "type": "core_activity", "prompt": "«زار يوسف المكتبة وقرأ قصة». ماذا فعل يوسف في المكتبة؟", "options": ["لعب","كتب","قرأ قصة","نام"], "answer": "قرأ قصة", "audio": "WRD-08.mp3", "vocab_img": "hem-voc-22-library-1024.png"},
    {"skill": "قراءة جملة قصيرة", "audio_prompt": True, "type": "core_activity", "prompt": "اقرأ بصوت: «النجوم تلمع في السماء»", "reading_text": "النجوم تلمع في السماء", "options": [], "answer": None, "audio": "WRD-09.mp3", "vocab_img": "hem-voc-14-star-1024.png"},
    {"skill": "فهم جملة مقروءة", "type": "core_activity", "prompt": "«تحلّق الأسرة حول مائدة الطعام». ماذا فعلت الأسرة؟", "options": ["تحلّقت حول المائدة","ذهبت للحديقة","ذهبت للمدرسة","سافرت"], "answer": "تحلّقت حول المائدة", "audio": "WRD-10.mp3", "vocab_img": "hem-voc-33-family-1024.png"},
    {"skill": "طلاقة القراءة", "audio_prompt": True, "type": "core_activity", "prompt": "اقرأ بطلاقة: «الوادي الجميل ممتد بين الجبال»", "reading_text": "الوادي الجميل ممتد بين الجبال", "options": [], "answer": None, "audio": "WRD-11.mp3", "vocab_img": "hem-voc-32-valley-1024.png"},
    {"skill": "قراءة قصة قصيرة", "audio_prompt": True, "type": "core_activity", "prompt": "اقرأ: «جلس الأطفال على الشاطئ وشاهدوا الأمواج»", "reading_text": "جلس الأطفال على الشاطئ وشاهدوا الأمواج", "options": [], "answer": None, "audio": "WRD-12.mp3", "vocab_img": "hem-voc-23-beach-1024.png"},
    {"skill": "فهم النص", "type": "core_activity", "prompt": "«بذرت فاطمة البذور ثم سقتها بالماء». ماذا فعلت فاطمة أولاً؟", "options": ["سقت النبات","بذرت البذور","قطفت الثمار","أكلت الثمار"], "answer": "بذرت البذور", "audio": "WRD-13.mp3", "vocab_img": "hem-voc-29-seed-1024.png"},
]
l3_reinf = [
    {"skill": "قراءة جملة قصيرة", "audio_prompt": True, "type": "reinforcement_activity", "prompt": "تقوية: اقرأ بصوت: «الفتى الذكي يقرأ كل يوم»", "reading_text": "الفتى الذكي يقرأ كل يوم", "options": [], "answer": None, "audio": "WRD-14.mp3"},
    {"skill": "فهم جملة مقروءة", "type": "reinforcement_activity", "prompt": "تقوية: «تسبح الأسماك في البحر». أين تسبح الأسماك؟", "options": ["النهر","البحر","البركة","الوادي"], "answer": "البحر", "audio": "WRD-15.mp3", "vocab_img": "hem-voc-24-sea-1024.png"},
    {"skill": "طلاقة القراءة", "audio_prompt": True, "type": "reinforcement_activity", "prompt": "تقوية: اقرأ بطلاقة: «الغيوم تجمعت في السماء»", "reading_text": "الغيوم تجمعت في السماء", "options": [], "answer": None, "audio": "WRD-16.mp3", "vocab_img": "hem-voc-31-clouds-1024.png"},
    {"skill": "قراءة قصة قصيرة", "audio_prompt": True, "type": "reinforcement_activity", "prompt": "تقوية: اقرأ: «المعلمة تشرح الدرس بصبر وحب»", "reading_text": "المعلمة تشرح الدرس بصبر وحب", "options": [], "answer": None, "audio": "WRD-17.mp3", "vocab_img": "hem-voc-19-teacher-1024.png"},
    {"skill": "فهم النص", "type": "reinforcement_activity", "prompt": "تقوية: «نزلت الأسرة على الشاطئ وجمعوا الأصداف». ماذا جمعوا؟", "options": ["الأحجار","الأصداف","الرمال","الأسماك"], "answer": "الأصداف", "audio": "WRD-18.mp3", "vocab_img": "hem-voc-26-shells-1024.png"},
]

ACTIVITIES = (
    [(1, a) for a in l1_core] + [(1, a) for a in l1_reinf] +
    [(2, a) for a in l2_core] + [(2, a) for a in l2_reinf] +
    [(3, a) for a in l3_core] + [(3, a) for a in l3_reinf]
)


def build_item(kind, level, skill_name, data, idx):
    is_audio = data.get("audio_prompt", False)
    interaction = "read_aloud" if is_audio else "multiple_choice"

    options_built = []
    correct_id = None
    for oi, opt in enumerate(data.get("options", []), 1):
        is_correct = isinstance(data.get("answer"), str) and opt == data["answer"]
        options_built.append({
            "id": oi,
            "text": opt,
            "is_correct": is_correct,
            "order_index": oi,
        })
        if is_correct:
            correct_id = oi

    step = {
        "order_index": 1,
        "prompt_text": data["prompt"],
        "expected_reading_text": data.get("reading_text"),
        "options": options_built,
        "assets": [{"asset_id": data["audio"], "type": "audio", "usage": "prompt"}] if data.get("audio") else [],
    }
    if data.get("vocab_img"):
        step["assets"].append({"asset_id": data["vocab_img"], "type": "image", "usage": "illustration"})

    sk = skill_key(level, skill_name)
    item_key = stable_key(kind, level, skill_name, idx)
    content_str = json.dumps({"kind": kind, "level": level, "skill": skill_name, "prompt": data["prompt"]}, ensure_ascii=False)
    checksum = hashlib.sha256(content_str.encode()).hexdigest()[:16]

    return {
        "stable_key": item_key,
        "kind": kind,
        "level_id": level,
        "skill_key": sk,
        "skill_name": skill_name,
        "interaction_type": interaction,
        "order_index": idx,
        "version": "2.0",
        "status": "active",
        "checksum": checksum,
        "steps": [step],
        "vocab_img": data.get("vocab_img"),
        "audio_file": data.get("audio"),
    }


def main():
    catalog = []
    idx = 1

    for q in PRETEST_QUESTIONS:
        catalog.append(build_item("pretest_question", q["level"], q["skill"], q, idx))
        idx += 1

    for q in POSTTEST_QUESTIONS:
        catalog.append(build_item("posttest_question", q["level"], q["skill"], q, idx))
        idx += 1

    for level, a in ACTIVITIES:
        catalog.append(build_item(a["type"], level, a["skill"], a, idx))
        idx += 1

    # ─── Validate counts ───────────────────────────────────────────────────────
    pretest = [c for c in catalog if c["kind"] == "pretest_question"]
    posttest = [c for c in catalog if c["kind"] == "posttest_question"]
    core = [c for c in catalog if c["kind"] == "core_activity"]
    reinf = [c for c in catalog if c["kind"] == "reinforcement_activity"]

    errors = []
    if len(pretest) != 30: errors.append(f"FAIL: pretest={len(pretest)} (want 30)")
    if len(posttest) != 30: errors.append(f"FAIL: posttest={len(posttest)} (want 30)")
    if len(core) != 30: errors.append(f"FAIL: core={len(core)} (want 30)")
    if len(reinf) != 15: errors.append(f"FAIL: reinf={len(reinf)} (want 15)")

    for item in catalog:
        for field in ["stable_key", "kind", "level_id", "skill_key", "interaction_type", "checksum"]:
            if not item.get(field):
                errors.append(f"FAIL: missing {field} in item {item.get('stable_key')}")

    if errors:
        print("VALIDATION FAILED:")
        for e in errors: print(" -", e)
        exit(1)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"OK Catalog built: {len(catalog)} items")
    print(f"   pretest={len(pretest)}, posttest={len(posttest)}, core={len(core)}, reinf={len(reinf)}")
    print(f"   -> {OUT_PATH}")


if __name__ == "__main__":
    main()
