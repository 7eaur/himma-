# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت المسؤول الهندسي الكامل عن منصة هِمّة في `7eaur/himma-`.

فرع التنفيذ: `audit/comprehensive-repository-review-2026-09-10`.

ابدأ دائمًا بجلب HEAD الحالي وآخر CI قبل أي تعديل، ثم اقرأ بالترتيب:
1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-13_A10_W3_RUN842_GREEN_AR.md`
2. `docs/maintenance/HIMMA_A10_W3_AUTOMATION_CHECKPOINT_2026-09-13_RUN842_GREEN_AR.md`
3. `docs/maintenance/HIMMA_A10_W3_EXECUTION_CHECKPOINT_2026-09-12_AR.md`
4. `docs/ops/STATUS.md`
5. `docs/ops/progress.json`
6. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`

اعتبر repository code + migrations + executable tests/CI + canonical contracts هي Source of Truth.

## الحالة الموثقة
- A00–A09 = CLOSED AUDIT.
- W1 = CLOSED GREEN on `ea132c9afbe152d0afa5ae581c058ce3248a0c48`, Run #813 / ID `34467329988`.
- W2 = CLOSED GREEN on `77ac72174a9e21163f6341ea8e0fcc172269eac3`, Run #822 / ID `34548388760`.
- W3 = ACTIVE / NOT GREEN.
- `AUD-A04-008` CLOSED GREEN on exact SHA `562b4eb3ef831cf7b8b51bd7d5e33145917cb382`, Run #842 / ID `34723513642`.
- #842 all jobs SUCCESS: Security + Frontend + Backend + Integration/Playwright.
- First remaining selected batch: `AUD-PERF-004` only.
- `AUD-A04-001` and final scenario/exact-SHA W3 gate remain afterward unless separately proven closed.

## AUD-PERF-004 root fix contract
Current `globals.css` performs runtime Google Fonts `@import`. Fix atomically by using `next/font/google` from root layout, wiring generated CSS variables into existing `--font-student` / `--font-researcher` tokens, removing the remote CSS import, and adding executable browser/network regression that proves no request reaches `fonts.googleapis.com` or `fonts.gstatic.com`.

A prior partial attempt was reverted because it changed layout without removing the runtime CSS import; do not repeat that partial state.

After the code batch, move `stage/a10-w3-ci` to the final code-bearing SHA and inspect the full gate. While any gate is ACTIVE/QUEUED, do not start another batch.

بعد W3 فقط: W4 ثم W5 ثم W6. A11 والنشر خارج الجدولة وممنوعان.

قيود ثابتة: لا Docker، لا fake ASR، لا Temporary Audio Skip، لا حذف history، لا دمج Speech/Pronunciation Lab، لا final merge، لا Deploy/Railway/Production، ولا إضعاف tests.
