# خطة الصيانة والتحسين الشاملة — هِمّة

**التاريخ:** 2026-08-28  
**الحالة:** الخطة التنفيذية الحالية بعد المراجعة الأكاديمية والمنتجية

## المبدأ

لا ننفذ إصلاحات مشتتة. نثبت الحقيقة، ثم نصلح القلب الأكاديمي، ثم المحتوى/التقوية، ثم تجربة الطالب والمشرف، ثم التقارير والصوت والإطلاق.

---

## M00 — استعادة HEAD أخضر

**الأولوية:** P0/P1

الحالة عند إنشاء الخطة:

- HEAD الأساسي قبل commits التوثيقية: `0f46e7e9421e7617f72fd03de3199df955084cd0`.
- Run #206 / `33139416128`: frontend SUCCESS، backend SUCCESS، integration/Playwright FAILURE.

المطلوب:

1. فحص Playwright report/logs للرأس الحالي.
2. إصلاح السبب دون reset أو حذف سلسلة الإصلاحات الأخيرة.
3. إعادة تشغيل Quality Gate.
4. تحديث `STATUS.md` و`progress.json` بالدليل الجديد.

Gate: الثلاثة Frontend/Backend/Integration = SUCCESS.

---

## M01 — Placement Scoring & Gates

**الأولوية:** P1 أكاديمي

المطلوب:

- Scoring 20/40/40.
- L1 gate: الاستعداد <12/20.
- L2 reading/word gate.
- L3 basic reading/text accuracy gate.
- لا اختراع threshold غير معتمد؛ ضع setting أو blocker واضحًا.
- TEMP_AUDIO_SKIP يجعل القرار Provisional إذا غاب دليل صوتي لازم.

Tests:

- boundary values.
- section weights.
- gate overrides total score.
- neutral skipped audio.

---

## M02 — Adaptation State Machine

**الأولوية:** P1

المطلوب:

- Placement منفصل عن adaptation.
- 80+ pass.
- 70–79 guided retry.
- <70 weakness + reinforcement.
- 50/30/20 كـtrend/mastery.
- 10/10 core gate للترقية.
- Core Session مستقلة لكل مستوى.
- L1→L2→L3→journey complete.
- لا Posttest بعد L1/L2.

قرار يجب حسمه قبل إزالة الكود القديم:

- Automatic Demotion: المراجعة توصي بإلغائه من المسار العادي واعتماد support داخل المستوى + manual supervisor override فقط.

Gate:

- property/boundary tests.
- E2E لطلاب يبدأون L1/L2/L3.

---

## M03 — Reinforcement Content & Mapping

**الأولوية:** P1/P2

المطلوب:

- إضافة 18 تقوية جديدة فوق 15 الأصلية.
- Skill Family mapping.
- metadata للتقوية.
- return-to-core verification.
- max retry policy.
- supervisor intervention عند التعثر.
- no random fallback.

المراجع:

- `docs/specs/REINFORCEMENT_CONTENT_ADDITIONS_2026-08-28_AR.md`
- `docs/specs/ADAPTATION_REINFORCEMENT_REDESIGN_2026-08-28_AR.md`

Gate:

- كل core skill له mapping معتمد أو explicit supervisor path.
- لا skill gap صامت.

---

## M04 — Student Product UI

**الأولوية:** P2 لكن شرط تسليم المنتج

المطلوب:

- Full-screen learning stage.
- Unified Student Task Shell.
- Companion character 220–300px تقريبًا على desktop عند الحاجة.
- contextual instructions.
- حفظ والخروج.
- recording state machine.
- result/reward screen.
- L1/L2/L3 journey visibility.
- same system for pre/post/core/reinforcement.

Gate:

- desktop/mobile/tablet screenshots.
- no horizontal overflow.
- all interaction templates coherent.

---

## M05 — Supervisor Product UX

**الأولوية:** P2

المطلوب:

- Admin IA جديدة.
- Action Center dashboard.
- student list/search/filter.
- Student Profile tabs.
- reinforcement review drawer/page.
- audio review robust flow.
- account/security/supervisors settings grouping.
- audit/history surfaces.

Gate:

- supervisor can understand current student state without reading raw technical fields.
- common actions <= few clicks and clearly named.

---

## M06 — Responsive / Accessibility / Design QA

المقاسات الإلزامية:

- 390×844.
- 768×1024.
- 1024×768.
- 1440×900.

Checks:

- Touch >=44px.
- Focus visible.
- Keyboard admin.
- 200% zoom.
- contrast.
- RTL/shaping.
- reduced motion.
- no technical text to child.

---

## M07 — Research Reports

المطلوب:

- Pre/Post.
- absolute improvement.
- percentage improvement.
- skill errors.
- reading error categories where valid.
- time/attempts.
- start/final level.
- reinforcement history.
- Excel multi-sheet.
- PDF individual + aggregate.
- export audit log.

Gate: UI/Excel/PDF agree with DB.

---

## M08 — Real Speech Analysis

لا يبدأ كإغلاق نهائي قبل:

- representative recordings.
- provider selection.
- privacy/cost/transfer decision.
- confidence calibration.
- retention policy.

Architecture:

Reference-guided Arabic reading analysis.

Gate:

- real adapter.
- sample evaluation.
- manual review for low confidence.
- no unsupported phoneme/haraka claims.

---

## M09 — Release / UAT

- E2E UC scenarios.
- service failure/network/microphone cases.
- security/privacy.
- backup + restore.
- HTTPS/domain.
- monitoring/logging.
- synthetic-data UAT first.
- final manuals.

Gate: accepted ACs or written exemptions only.

---

## الأولويات

### P0

- current red CI.
- security/data loss/permission problems if discovered.

### P1

- scoring/placement correctness.
- adaptation state machine.
- reinforcement correctness.
- broken student journey.

### P2

- UI architecture.
- admin IA.
- responsive/accessibility.
- reports completeness.

### P3

- cosmetic polish after correctness.

---

## ممنوعات أثناء الصيانة

- لا reset/hard rollback للتخلص من المشكلة بدل إصلاحها.
- لا تعديل tests لتخفيض التوقعات.
- لا mocks في مسار يقال إنه إنتاجي.
- لا fake score للصوت.
- لا تعويض وسائط مفقودة بأصول غير معتمدة.
- لا تغيير قواعد أكاديمية بصمت.
- لا مزج تطوير P3 قبل حل P1.
