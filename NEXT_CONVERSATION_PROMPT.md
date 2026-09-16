# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت الآن المسؤول الهندسي والمنتجي الكامل عن منصة **هِمّة** في المستودع:

`7eaur/himma-`

فرع التنفيذ:

`audit/comprehensive-repository-review-2026-09-10`

فرع CI المؤقت للموجة الحالية:

`stage/a10-w4-ci`

**مهم:** لا تعتمد على SHA محفوظ هنا قبل التحقق. أول خطوة إلزامية هي Fetch للـlive execution HEAD ثم Fetch لآخر Quality Gate وCI helper branch. توجد commits توثيق بعد آخر code candidate.

## اقرأ أولًا — بالترتيب

1. `docs/ops/STATUS.md`
2. `docs/ops/progress.json`
3. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-16_A10_W4_MEDIA_002_GATE_FAIL_AR.md`
4. `docs/maintenance/HIMMA_A10_W4_MEDIA_002_GATE_FAIL_2026-09-16_AR.md`
5. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_STATUS_UPDATE_2026-09-16_AR.md`
6. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
7. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_EXECUTION_ADDENDUM_2026-09-12_AR.md`
8. `docs/ops/HIMMA_W4_OWNER_CLIENT_APPROVAL_2026-09-14.md`
9. `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md`
10. `START_HERE_AR.md`
11. `AGENTS.md` ثم ملفات `.agents/rules/` المشار إليها فيه.

إذا احتجت فهم التاريخ/root cause قبل تعديل W5/W6، اقرأ ملفات A00–A09 وW1/W2/W3 المذكورة بالتفصيل داخل الـMaster Continuity Handoff. لا تعيد تنفيذ التدقيق؛ اقرأه لفهم سبب القرارات فقط.

## Source of Truth

الترتيب التنفيذي:

`live code + PostgreSQL migrations/schema + executable tests/CI + current canonical contracts/approved decisions + current STATUS/progress + historical audit docs`

المحادثات السابقة ليست Source of Truth.

## الحالة المثبتة

- A00–A09: CLOSED AUDIT.
- W1: GREEN — `ea132c9afbe152d0afa5ae581c058ce3248a0c48`, #813 / `34467329988`.
- W2: GREEN — `77ac72174a9e21163f6341ea8e0fcc172269eac3`, #822 / `34548388760`.
- W3: GREEN — `62e34b151e46b406cf3936201f80010abbe9d8d1`, #848 / `34729450663`.
- W4: **IN PROGRESS؛ لا تعتبرها Green بعد**.
- W5: NOT STARTED.
- W6: NOT STARTED.

W4 المغلق Green:

- `AUD-BADGE-008`
- `AUD-BADGE-004`
- `AUD-BADGE-005`
- `AUD-BADGE-007`
- `AUD-BADGE-003`
- `AUD-BADGE-001`
- `AUD-BADGE-002`

آخر W4 Green batch:

`AUD-BADGE-002`

Exact code SHA:

`f7c6885518e206266bcb1d8805b636931f3ac554`

Quality Gate #856 / Run ID `34807098480` = full SUCCESS بما فيه Integration + Playwright.

## الموافقات التي لا يجوز طلبها مرة أخرى

`docs/ops/HIMMA_W4_OWNER_CLIENT_APPROVAL_2026-09-14.md` معتمد:

- `BDG-01..BDG-06` هي حزمة الشارات الرسمية.
- `lexical_stimulus` يمثل معنى الكلمة مباشرة.
- `story_context` سياقي/مساند.
- `سَمَك` يستخدم direct fish representation.
- `نُور` يستخدم direct light/illumination representation.

`AUD-MEDIA-002` لم يعد ينتظر academic approval.

## نقطة التوقف الفعلية — AUD-MEDIA-002

آخر **code candidate** قبل commits التوثيق:

`e642aa4b27974c2ec11970fa768f58195188f3f1`

تم تنفيذ:

- `services/api/w4_media_semantics.py`
- تعديل `services/api/canonical_release.py`
- `services/api/test_w4_lexical_media_semantics.py`

العقد الحالي المقصود:

- `L2-CORE-09/R03` → `VOC-05` → `سَمَك` → `lexical_stimulus`.
- `L2-CORE-09/R05` → `VOC-15` → `نُور` → `lexical_stimulus`.

Quality Gate #857 / Run ID `35040922310` على exact SHA `e642aa4...` = **FAILURE**:

- Frontend SUCCESS.
- Security SUCCESS.
- Backend canonical validation/migrations/model drift/seed idempotency SUCCESS.
- pytest: `1 failed, 866 passed`.
- Integration SKIPPED بسبب backend failure.

الاختبار الوحيد الفاشل:

`test_sep8_approval_projection.py::test_every_declared_image_relationship_is_semantic_and_exact`

الـActual الحالي وفق القرار الأحدث:

`VOC-05 / image / lexical_stimulus / سَمَك`

بينما `STEP_MEDIA` التاريخي داخل `content_approval_contract_2026_09_08.py` ما يزال يتوقع:

`VOC-05 / image / context / سمك`

الاختبارات الجديدة الخاصة بـW4 media semantics نجحت. **لا ترجع المنتج إلى context ولا تضعف/تتخطى الاختبار القديم.** المطلوب حل Root Cause: توحيد owner-of-truth للـfinal release بحيث تحفظ Sep-08 كتاريخ عند الحاجة وتستهلك authority الأحدث المعتمدة في التحقق النهائي.

## أول مهمة الآن

ابدأ من هذه النقطة فقط:

1. Fetch live execution HEAD وفرق commits بعد `e642aa4...` للتأكد أن ما بعده توثيق فقط قبل لمس الكود.
2. اقرأ:
   - `services/api/content_approval_contract_2026_09_08.py`
   - `services/api/w4_media_semantics.py`
   - `services/api/canonical_release.py`
   - `services/api/test_sep8_approval_projection.py`
   - `services/api/test_w4_lexical_media_semantics.py`
   - owner/client approval doc.
3. أصلح تضارب authority من الجذر، لا symptom.
4. لا تغيّر R01/R02/R04 بدون evidence؛ العقد الحالي يغيّر R03/R05 فقط.
5. لا skip/xpass/delete للاختبارات.
6. بعد root fix، commit على execution branch.
7. حرّك `stage/a10-w4-ci` **fast-forward** إلى exact new audit HEAD؛ هذا فرع تشغيل فقط ولا يُدمج.
8. تحقق أن Quality Gate الجديد يحمل نفس `head_sha`.
9. لا تغلق `AUD-MEDIA-002` أو W4 إلا بعد نجاح Backend + Frontend + Security + Integration/Playwright كلها على نفس SHA.
10. بعد Green فقط: حدّث checkpoint/STATUS/progress/gap overlay إلى W4 GREEN ثم ابدأ W5 وفق Master Gap Register.

## بعد W4

الترتيب إلزامي:

`W4 → W5 → W6`

عند W6 Green توقف. لا تنفذ A11/Deploy/Railway/Production/final merge إلا بتكليف صريح جديد.

## قيود ثابتة

No Docker. No fake ASR. No Temporary Audio Skip. No history deletion. No Speech/Pronunciation Lab merge. No final merge. No weakened tests. No runtime repair overlays. لا PASS/CLOSED بلا exact-SHA evidence. Production ASR (`AUD-A03-008`) يبقى blocked حتى external provider/calibration/privacy/cost/governance approval.

**لا تكتفِ بتقرير حالة. بعد قراءة الملفات والتحقق الحي، نفّذ الإصلاح الفعلي وتابع Quality Gate حتى النتيجة.**
