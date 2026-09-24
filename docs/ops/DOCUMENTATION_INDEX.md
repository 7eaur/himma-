# فهرس التوثيق الحالي — هِمّة

**Updated:** 2026-09-24

## نقطة الدخول

- `START_HERE_AR.md` — الملخص التشغيلي ونقطة الدخول الوحيدة.

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
- `docs/handoff/**`
- كل ملف مؤرخ باسم يوم أو مرحلة أو Run أو Checkpoint أو Audit.

## قاعدة الأرشيف

لا نحذف التاريخ لمجرد أنه قديم. يبقى في Git ويعامل كـ`HISTORICAL / REFERENCE ONLY`. إذا تعارض مع المصادر الحالية، تُقدّم المصادر الحالية ثم الكود الحي والاختبارات والتشغيل.

## قاعدة منع التكرار

- حالة العمل تُحدّث في `STATUS.md` و`progress.json` فقط.
- أدلة التشغيل تُحدّث في `EVIDENCE_INDEX.md` فقط.
- تفاصيل Railway تُحدّث في `RELEASE_DEPLOYMENT_CURRENT_AR.md` فقط.
- لا يُنشأ handoff جديد لكل تشغيل أو عائق مؤقت.
