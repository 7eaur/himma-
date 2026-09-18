# فهرس التوثيق القانوني — هِمّة

**Updated:** 2026-09-18

## نقطة الدخول

1. START_HERE_AR.md — الملف الرئيسي الوحيد لبدء أي محادثة جديدة.
2. NEXT_CONVERSATION_PROMPT.md — توجيه مختصر للبدء من START_HERE.

## وثائق CURRENT / AUTHORITATIVE

- docs/ops/STATUS.md — الحالة المختصرة الحالية.
- docs/ops/progress.json — الحالة المقروءة آليًا.
- docs/ops/RESUME_HERE.md — نقطة الاستئناف.
- docs/specs/SOURCE_OF_TRUTH.md — ترتيب القوة ومالكو الحقيقة.
- docs/specs/SYSTEM_SPEC.md — مواصفات المنتج الحالية.
- docs/specs/ARCHITECTURE_BASELINE.md — المعمارية الحالية.
- .agents/rules/00-himma-core.md — قواعد المنتج الأساسية.
- .agents/rules/10-delivery-protocol.md — بروتوكول التنفيذ.
- .agents/rules/20-security-quality.md — الأمن والجودة.
- docs/ops/DECISIONS.md — ADRs المقبولة.
- docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_CURRENT_AR.md — عقد الصوت الحالي.
- docs/ops/EVIDENCE_INDEX.md — الأدلة الحالية.
- docs/maintenance/HIMMA_BRANCH_INVENTORY_2026-09-18_AR.md — حالة الفروع.
- docs/ops/OPEN_ITEMS.md — المفتوح فقط.
- docs/ops/PROJECT_STATE.md — وصف الحالة الحالية.
- docs/ops/RELEASE_DEPLOYMENT_CURRENT_AR.md — النشر الحالي.
- VERSION.md — وسم الإصدار/الحالة.

## وثائق HISTORICAL / EVIDENCE ONLY

كل الملفات المؤرخة القديمة من الأنواع التالية تاريخ فقط ما لم يذكر هذا الفهرس صراحة أنها Current:
- HIMMA_MASTER_CONTINUITY_HANDOFF_*
- *_CHECKPOINT_*
- A00–A10 audit/execution snapshots.
- Recovery/P01/P02 historical reports.
- UX handoff/progress files بتاريخ 2026-09-17.
- RELEASE_DEPLOYMENT_2026-09-17_AR.md.
- HIMMA_A09_BRANCH_CLASSIFICATION_2026-09-10_AR.md.
- progress_2026-08-28.json وCURRENT_STATE_2026-08-28_AR.md.

لا تحذف هذه الملفات؛ هي provenance/chronology ودليل قرارات سابقة. لكنها لا تصف current state.

## قاعدة إزالة التعارض

إذا وجدت وثيقة تاريخية تقول:
- NOT MERGED
- NOT DEPLOYED
- no production DB
- prototype only
- stop before A11
- old student-audio blocking behavior
- old Temporary Audio Skip
- old branch as active

فلا تطبقها. ارجع إلى START_HERE_AR.md ثم current authority files أعلاه ثم live evidence.

## لماذا نحفظ التاريخ؟

للتدقيق، root-cause analysis، traceability، وإثبات كيف وصل المشروع للحالة الحالية. حفظ التاريخ لا يعني أن كل صياغة تاريخية ما زالت نافذة.
