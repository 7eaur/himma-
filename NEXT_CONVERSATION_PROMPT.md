# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت المسؤول الهندسي الكامل عن منصة هِمّة في `7eaur/himma-`.

فرع التنفيذ: `audit/comprehensive-repository-review-2026-09-10`.

قبل أي تعديل اجلب HEAD الحالي وآخر Quality Gate/CI، ثم اقرأ حرفيًا بالترتيب:
1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-13_A10_W3_CROSS_DEVICE_INTEGRITY_ACTIVE_AR.md`
2. `docs/maintenance/HIMMA_A10_W3_AUTOMATION_CHECKPOINT_2026-09-13_CROSS_DEVICE_INTEGRITY_ACTIVE_AR.md`
3. `docs/maintenance/HIMMA_A10_W3_EXECUTION_CHECKPOINT_2026-09-12_AR.md`
4. `docs/ops/STATUS.md`
5. `docs/ops/progress.json`
6. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`

Repository code + migrations + executable tests/CI + canonical contracts هي Source of Truth.

## الحالة الحالية
- A00–A09 CLOSED AUDIT.
- W1 CLOSED GREEN — `ea132c9afbe152d0afa5ae581c058ce3248a0c48`, Run #813 / ID `34467329988`.
- W2 CLOSED GREEN — `77ac72174a9e21163f6341ea8e0fcc172269eac3`, Run #822 / ID `34548388760`.
- W3 ACTIVE / NOT GREEN.
- `AUD-PERF-004` CLOSED GREEN — exact code SHA `33263107047447ae758ca2092209100ab541efdd`, Quality Gate #845 / Run ID `34725817618`.
- `AUD-A04-001` CLOSED GREEN — exact code SHA `c8fb6277527558c185167ba6d7a5059a1c9e90aa`, Quality Gate #846 / Run ID `34726957359`; Security/Frontend/Backend/Integration-Playwright كلها SUCCESS.
- Current batch only: `CROSS_DEVICE_SCENARIO_INTEGRITY`.
- Exact code SHA الحالي: `1df3a25b751ad5782b5064ae7c7b6b9353dece86`.
- أضيف اختبار Playwright تنفيذي يثبت بقاء canonical Student Detail/Journey truth متطابقًا عند 320px و768px و1440px، دون تغيير domain/data behavior.
- Quality Gate #847 / Run ID `34728109762` بدأ على نفس exact code SHA، وآخر حالة موثقة QUEUED/ACTIVE.

## إلزامي
افحص #847 أولًا. إذا بقي ACTIVE/QUEUED فلا تبدأ أي كود آخر. إذا FAILURE اقرأ أول failure حقيقي وأصلحه من root cause داخل `CROSS_DEVICE_SCENARIO_INTEGRITY` فقط ولا تضعف الاختبارات. إذا SUCCESS بالكامل، أغلق هذا البند ووثّق exact evidence ثم نفّذ فقط final exact-SHA W3 Green gate قبل أي انتقال إلى W4.

بعد W3 Green فقط: W4 ثم W5 ثم W6. إذا أصبحت W6 Green توقف. ممنوع A11 أو Deploy/Railway/Production أو final merge.

قيود ثابتة: لا Docker، لا fake ASR، لا Temporary Audio Skip، لا حذف history، لا دمج Speech/Pronunciation Lab، ولا إضعاف tests.
