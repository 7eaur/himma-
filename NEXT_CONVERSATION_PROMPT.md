# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت المسؤول الهندسي الكامل عن منصة هِمّة في `7eaur/himma-`.

فرع التنفيذ: `audit/comprehensive-repository-review-2026-09-10`.

قبل أي تعديل اجلب HEAD الحالي وآخر Quality Gate/CI، ثم اقرأ حرفيًا بالترتيب:
1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-13_A10_W3_FINAL_GATE_ACTIVE_AR.md`
2. `docs/maintenance/HIMMA_A10_W3_AUTOMATION_CHECKPOINT_2026-09-13_FINAL_GATE_ACTIVE_AR.md`
3. `docs/maintenance/HIMMA_A10_W3_EXECUTION_CHECKPOINT_2026-09-12_AR.md`
4. `docs/ops/STATUS.md`
5. `docs/ops/progress.json`
6. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`

Repository code + migrations + executable tests/CI + canonical contracts هي Source of Truth.

## الحالة الحالية
- A00–A09 CLOSED AUDIT.
- W1 CLOSED GREEN — `ea132c9afbe152d0afa5ae581c058ce3248a0c48`, Run #813 / ID `34467329988`.
- W2 CLOSED GREEN — `77ac72174a9e21163f6341ea8e0fcc172269eac3`, Run #822 / ID `34548388760`.
- W3 ACTIVE حتى نجاح final exact-SHA gate.
- `AUD-A04-001` CLOSED GREEN — SHA `c8fb6277527558c185167ba6d7a5059a1c9e90aa`, Run #846 / ID `34726957359`.
- `CROSS_DEVICE_SCENARIO_INTEGRITY` CLOSED GREEN — SHA `1df3a25b751ad5782b5064ae7c7b6b9353dece86`, Run #847 / ID `34728306429`.
- Current batch only: `W3_FINAL_EXACT_SHA_GATE`.

## إلزامي
افحص final W3 Quality Gate أولًا. إذا بقي ACTIVE/QUEUED فلا تبدأ أي كود أو W4. إذا FAILURE اقرأ أول failure حقيقي وأصلحه من root cause دون إضعاف الاختبارات، ثم شغّل gate جديدًا على exact SHA. إذا SUCCESS بالكامل في Security/Frontend/Backend/Integration-Playwright، أغلق W3 رسميًا ووثّق exact SHA/Run ID ثم ابدأ أول gap فقط من W4.

بعد W3 Green فقط: W4 ثم W5 ثم W6. إذا أصبحت W6 Green توقف. ممنوع A11 أو Deploy/Railway/Production أو final merge.

قيود ثابتة: لا Docker، لا fake ASR، لا Temporary Audio Skip، لا حذف history، لا دمج Speech/Pronunciation Lab، ولا إضعاف tests.
