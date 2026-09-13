# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت المسؤول الهندسي الكامل عن منصة هِمّة في `7eaur/himma-`.

فرع التنفيذ: `audit/comprehensive-repository-review-2026-09-10`.

قبل أي تعديل اجلب HEAD الحالي وآخر Quality Gate/CI، ثم اقرأ حرفيًا بالترتيب:
1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-13_A10_W3_A04_001_ACTIVE_AR.md`
2. `docs/maintenance/HIMMA_A10_W3_AUTOMATION_CHECKPOINT_2026-09-13_A04_001_ACTIVE_AR.md`
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
- `AUD-A04-008` CLOSED GREEN — `562b4eb3ef831cf7b8b51bd7d5e33145917cb382`, Run #842 / ID `34723513642`.
- `AUD-PERF-004` CLOSED GREEN — exact code SHA `33263107047447ae758ca2092209100ab541efdd`, Quality Gate #845 / Run ID `34725817618`; جميع Security/Frontend/Backend/Integration-Playwright نجحت.
- Current batch only: `AUD-A04-001`.
- Exact code SHA الحالي: `c8fb6277527558c185167ba6d7a5059a1c9e90aa`.
- التعديل الحالي يجعل Student Detail يعيد استخدام shared AdminUI primitives للـpage/panel/stat/action مع بقاء الأنماط الفريدة محلية ودون تغيير منطق البيانات/الأكاديمية.
- Quality Gate #846 / Run ID `34726957359` ACTIVE على نفس الـSHA.

## إلزامي
افحص #846 أولًا. إذا بقي ACTIVE/QUEUED فلا تبدأ أي كود آخر. إذا FAILURE اقرأ أول failure حقيقي وأصلحه داخل `AUD-A04-001` فقط ولا تضعف الاختبارات. إذا SUCCESS بالكامل بما فيه Integration/Playwright، قيّم ما إذا بقي presentation duplication مثبت داخل `AUD-A04-001` وأغلقه فقط عند استيفاء acceptance، ثم حدّث STATUS/progress/continuity/checkpoint قبل اختيار gap واحدة أخرى من W3.

بعد W3 فقط: W4 ثم W5 ثم W6. ممنوع A11 أو Deploy/Railway/Production أو final merge.

قيود ثابتة: لا Docker، لا fake ASR، لا Temporary Audio Skip، لا حذف history، لا دمج Speech/Pronunciation Lab، ولا إضعاف tests.
