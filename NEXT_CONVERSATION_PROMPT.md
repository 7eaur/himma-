# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت المسؤول الهندسي الكامل عن منصة هِمّة في `7eaur/himma-`.

فرع التنفيذ: `audit/comprehensive-repository-review-2026-09-10`.
فرع تشغيل W4 CI: `stage/a10-w4-ci`.

قبل أي تعديل اجلب HEAD الحالي وآخر Quality Gate/CI، ثم اقرأ حرفيًا بالترتيب:
1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-14_A10_W4_BADGE_003_GREEN_AR.md`
2. `docs/maintenance/HIMMA_A10_W4_AUTOMATION_CHECKPOINT_2026-09-14_BADGE_003_GREEN_AR.md`
3. `docs/ops/STATUS.md`
4. `docs/ops/progress.json`
5. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
6. `docs/ops/HIMMA_W4_OWNER_CLIENT_APPROVAL_2026-09-14.md`

Repository code + migrations + executable tests/CI + canonical contracts هي Source of Truth.

## الحالة المثبتة
- A00–A09 CLOSED AUDIT.
- W1 CLOSED GREEN — `ea132c9afbe152d0afa5ae581c058ce3248a0c48`, #813 / `34467329988`.
- W2 CLOSED GREEN — `77ac72174a9e21163f6341ea8e0fcc172269eac3`, #822 / `34548388760`.
- W3 CLOSED GREEN — `62e34b151e46b406cf3936201f80010abbe9d8d1`, #848 / `34729450663`.
- W4 IN PROGRESS / UNBLOCKED — NOT GREEN YET.
- `AUD-BADGE-008` CLOSED GREEN — `57495fb804d4f52f684aded176474155dace07d9`, #850 / `34731134319`.
- `AUD-BADGE-004` CLOSED GREEN — `fddc8a59190d1f6522f1639d4f8156982fbaf293`, #851 / `34732091325`.
- `AUD-BADGE-005` CLOSED GREEN by executable canonical completion evidence.
- `AUD-BADGE-007` CLOSED GREEN — `970416d707639a3cab2f0dfa930b9f78990afe20`, #853 / `34733663693`.
- `AUD-BADGE-003` CLOSED GREEN — exact code SHA `8736372f855e55646ce50712615b6274af94a9a8`, Quality Gate #854 / Run ID `34803602294`, SUCCESS including integration + Playwright E2E.

## الاعتمادات التي لا يجوز طلبها مرة أخرى
`docs/ops/HIMMA_W4_OWNER_CLIENT_APPROVAL_2026-09-14.md` هو القرار الكانوني المعتمد من مالك المنتج/العميل:
- حزمة الشارات الرسمية `BDG-01..BDG-06` معتمدة.
- `lexical_stimulus` يجب أن يمثل معنى الكلمة مباشرة.
- `story_context` صورة سياقية/مساندة وليست محفزًا لفظيًا مباشرًا.
- `سَمَك` يستخدم تمثيل سمك مباشرًا، و`نُور` يستخدم تمثيل الضوء/الإضاءة المباشر.

## أول بند غير مكتمل
`AUD-BADGE-001`.

نفذه أولًا فقط، مع الحفاظ على semantics الحالية: source unavailable ≠ empty success، وempty success = zero، وpopulated success = rewards الفعلية. يجب عرض الأصل المرئي الكانوني من Reward Catalog لا hardcoded parallel mapping. بعد exact-SHA GREEN gate وثّق الإغلاق ثم انتقل إلى `AUD-BADGE-002`، ثم `AUD-MEDIA-002` بالعقد المعتمد أعلاه.

لا تبدأ W5 قبل W4 GREEN. بعد W4: W5 ثم W6. إذا أصبحت W6 Green توقف.

ممنوع A11 أو Deploy/Railway/Production أو final merge. لا Docker، لا fake ASR، لا Temporary Audio Skip، لا حذف history، لا دمج Speech/Pronunciation Lab، ولا إضعاف tests.
