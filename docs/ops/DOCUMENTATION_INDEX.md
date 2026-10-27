# فهرس التوثيق الحالي — هِمّة

**Updated:** 2026-10-07

## نقطة الدخول

- `START_HERE_AR.md` — الملخص التشغيلي ونقطة الدخول الوحيدة.
- `docs/handoff/HIMMA_CURRENT_PROJECT_HANDOFF_AR.md` — خريطة الاستلام الشاملة للمحادثة الجديدة؛ توجه للمصادر الملزمة ولا تستبدلها.

## مسار Himma V2 التخطيطي

يعمل Himma V2 في مسار مستقل عن Runtime الحالي. وجود هذه الوثائق لا يعني أن V2 مدمجة أو منشورة.

- `docs/v2/README.md` — الفهرس المتسلسل الوحيد لخطة V2 وحالة مراحلها.
- `docs/v2/01_EDUCATIONAL_MODEL_FOUNDATION_AR.md` — المرجع التعليمي الأساسي المعتمد لـ V2.
- `docs/v2/DECISIONS_AR.md` — سجل القرارات الجوهرية لمسار V2.

عند الحديث عن **التشغيل الحالي** تبقى مصادر Runtime أدناه هي المرجع.  
وعند الحديث عن **تصميم V2** يبدأ العمل من `docs/v2/README.md`.

## المصادر الحالية الملزمة

| المجال | الملف |
|---|---|
| الحالة البشرية المختصرة | `docs/ops/STATUS.md` |
| الحالة المقروءة آليًا | `docs/ops/progress.json` |
| ترتيب الحقيقة وعقود المنتج | `docs/specs/SOURCE_OF_TRUTH.md` |
| مواصفات النظام | `docs/specs/SYSTEM_SPEC.md` |
| حدود المعمارية | `docs/specs/ARCHITECTURE_BASELINE.md` |
| القرارات الثابتة | `docs/ops/DECISIONS.md` |
| أدلة الاختبار والتشغيل | `docs/ops/EVIDENCE_INDEX.md` |
| إصدار Railway الحالي | `docs/ops/RELEASE_DEPLOYMENT_CURRENT_AR.md` |
| البنود المفتوحة فقط | `docs/ops/OPEN_ITEMS.md` |
| خط الاستعادة المؤرشف | `docs/ops/RECOVERY_BASELINE_2026-09-21.md` |
| جرد التنظيف الجاري | `docs/maintenance/CLEANUP_INVENTORY_2026-09-24.md` |
| دليل دفعة التنظيف الأولى | `docs/maintenance/CLEANUP_BATCH_01_2026-09-24.md` |
| دليل دفعة التنظيف الثانية | `docs/maintenance/CLEANUP_BATCH_02_2026-09-24.md` |

## قواعد التنفيذ

- `.agents/rules/00-himma-core.md`
- `.agents/rules/10-delivery-protocol.md`
- `.agents/rules/20-security-quality.md`

## عقود الكود الحالية المهمة

- `services/api/canonical_release.py`
- `services/api/reading_text_policy_2026_09_21.py`
- `services/api/content_preview.py`
- `services/api/recordings.py`
- `apps/web/src/app/admin/(dashboard)/content-preview/page.tsx`
- `packages/content/training/himma_reading_training_corpus_v2026_09_21.jsonl`

## وثائق مساندة وليست مصدر حالة

هذه الملفات تبقى محفوظة للتفسير أو التسلسل الزمني، لكنها لا تُستخدم لتحديد الحالة الحالية:

- `docs/ops/CHANGELOG.md`
- `docs/ops/ROADMAP.md`
- `docs/ops/PROJECT_STATE.md`
- `docs/ops/RESUME_HERE.md`
- `VERSION.md`
- `NEXT_CONVERSATION_PROMPT.md`
- كل `docs/handoff/**` باستثناء `docs/handoff/HIMMA_CURRENT_PROJECT_HANDOFF_AR.md`
- كل ملف مؤرخ باسم يوم أو مرحلة أو Run أو Checkpoint أو Audit.

## قاعدة الأرشيف

لا نحذف التاريخ لمجرد أنه قديم. يبقى في Git ويعامل كـ`HISTORICAL / REFERENCE ONLY`. إذا تعارض مع المصادر الحالية، تُقدّم المصادر الحالية ثم الكود الحي والاختبارات والتشغيل.

## قاعدة منع التكرار

- حالة العمل تُحدّث في `STATUS.md` و`progress.json` فقط.
- أدلة التشغيل تُحدّث في `EVIDENCE_INDEX.md` فقط.
- تفاصيل Railway تُحدّث في `RELEASE_DEPLOYMENT_CURRENT_AR.md` فقط.
- مسار V2 يُفهرس في `docs/v2/README.md` ولا يكرر حالة Runtime.
- لا يُنشأ handoff جديد لكل تشغيل أو عائق مؤقت.
- خريطة الاستلام الثابتة الوحيدة هي `HIMMA_CURRENT_PROJECT_HANDOFF_AR.md` وتُحدّث فقط عندما تتغير صورة الاستلام ماديًا.
