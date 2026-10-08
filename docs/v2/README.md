# هِمّة V2 — Source of Truth للتخطيط

**الحالة:** تخطيط V2 المتوازن معتمد كأساس التنفيذ  
**الفرع:** `v2/01-learning-foundation-20261007`  
**التاريخ:** 2026-10-08

## الهدف

هذا المجلد هو المرجع الوحيد لتخطيط Himma V2 قبل التنفيذ.

V2 ليست إعادة بناء للمنصة من الصفر. هي تطوير متدرج فوق النظام الحالي لتحويل الأنشطة إلى دروس حقيقية وتحسين الدعم والتكيف والقياس مع أقل تعقيد ضروري.

## Baseline المعتمد

- **13 Skill Groups**
- **19 Core Lessons**
  - L1 = 6
  - L2 = 6
  - L3 = 7
- **12 Support Groups**
- Pretest = 30
- Posttest = 30
- Core Check = 3–5 بنود، الافتراضي 4
- Support Check = 2–3 بنود
- تطوير adaptation الحالي بدل استبداله
- Evidence/Error Tags خفيفة بدل Mastery Engine كبير
- AI واضح، لكن Advanced ASR ليس blocker
- CMS الكامل مؤجل إلى أن تثبت الحاجة

## ترتيب القراءة

| # | المرجع | الملف |
|---|---|---|
| 01 | النموذج التعليمي | `01_V2_MODEL_AR.md` |
| 02 | المهارات والمستويات | `02_SKILLS_AND_LEVELS_AR.md` |
| 03 | خريطة الـ19 Core Lesson | `03_CORE_LESSON_MAP_AR.md` |
| 04 | الـ12 Support + التكيف | `04_SUPPORT_AND_ADAPTATION_AR.md` |
| 05 | القياس والأدلة | `05_ASSESSMENT_AND_EVIDENCE_AR.md` |
| 06 | عقد محتوى الدرس | `06_LESSON_CONTENT_CONTRACT_AR.md` |
| 07 | دور AI | `07_AI_ROLE_AR.md` |
| 08 | إعادة استخدام V1 والترحيل | `08_V1_REUSE_MIGRATION_AR.md` |
| 09 | خطة التنفيذ | `09_IMPLEMENTATION_ROADMAP_AR.md` |
| — | القرارات الحالية | `DECISIONS_AR.md` |

## قاعدة الحقيقة

- Runtime الحالي يبقى منفصلًا حتى تنفيذ Migration مع اختبارات.
- لا تعتمد وثائق V2 المحذوفة أو التاريخية كمصدر قرار.
- Git history يحتفظ بالتاريخ عند الحاجة، لكن الملفات الموجودة في `docs/v2` هي المرجع الحالي.
- أي تعديل مستقبلي جوهري يحدث هذه الوثائق معًا ولا ينشئ خطة موازية جديدة.

## الخطوة التالية

العمل التالي هو **مرحلة A من `09_IMPLEMENTATION_ROADMAP_AR.md`**:

1. Contract تفصيلي لكل درس من الـ19.
2. محتوى الشرح والأمثلة والتدريب.
3. Independent Check.
4. Support content.
5. إعادة Mapping للقبلي والبعدي.
