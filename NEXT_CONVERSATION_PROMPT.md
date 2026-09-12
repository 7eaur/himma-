# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت المسؤول الهندسي الكامل عن منصة هِمّة في `7eaur/himma-`.

فرع التنفيذ: `audit/comprehensive-repository-review-2026-09-10`.

قبل أي تعديل اجلب HEAD الحالي وآخر Quality Gate/CI، ثم اقرأ حرفيًا بالترتيب:
1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-13_A10_W3_RUN843_ACTIVE_AR.md`
2. `docs/maintenance/HIMMA_A10_W3_AUTOMATION_CHECKPOINT_2026-09-13_RUN843_ACTIVE_AR.md`
3. `docs/maintenance/HIMMA_A10_W3_EXECUTION_CHECKPOINT_2026-09-12_AR.md`
4. `docs/ops/STATUS.md`
5. `docs/ops/progress.json`
6. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`

Repository code + migrations + executable tests/CI + canonical contracts هي Source of Truth.

## الحالة الحالية
- A00–A09 CLOSED AUDIT.
- W1 CLOSED GREEN — SHA `ea132c9afbe152d0afa5ae581c058ce3248a0c48`, Run #813 / ID `34467329988`.
- W2 CLOSED GREEN — SHA `77ac72174a9e21163f6341ea8e0fcc172269eac3`, Run #822 / ID `34548388760`.
- W3 ACTIVE / NOT GREEN.
- `AUD-A04-008` CLOSED GREEN — SHA `562b4eb3ef831cf7b8b51bd7d5e33145917cb382`, Run #842 / ID `34723513642`.
- Current batch only: `AUD-PERF-004`.
- Current exact code SHA: `e10dfe7bba8ea47ebc3fc6fca92c015d80ffe115`.
- Quality Gate #843 / Run ID `34724452979` is ACTIVE/QUEUED on that SHA.

## إلزامي
افحص #843 أولًا. إذا بقي ACTIVE/QUEUED فلا تبدأ أي كود آخر. إذا FAILURE أصلح أول failure حقيقي فقط ولا تضعف الاختبار. إذا SUCCESS بالكامل، أغلق `AUD-PERF-004` رسميًا ثم حدّث التوثيق وحدد gap واحدة فقط تالية من W3.

بعد W3 فقط: W4 ثم W5 ثم W6. ممنوع A11 أو Deploy/Railway/Production أو final merge.

قيود ثابتة: لا Docker، لا fake ASR، لا Temporary Audio Skip، لا حذف history، لا دمج Speech/Pronunciation Lab، ولا إضعاف tests.
