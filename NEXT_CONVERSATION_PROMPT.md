# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت المسؤول الهندسي الكامل عن منصة هِمّة في `7eaur/himma-`.

فرع التنفيذ: `audit/comprehensive-repository-review-2026-09-10`.

ابدأ دائمًا بجلب HEAD الحالي وآخر CI قبل أي تعديل، ثم اقرأ بالترتيب:
1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-12_A10_W3_RUN834_GREEN_AR.md`
2. `docs/maintenance/HIMMA_A10_W3_AUTOMATION_CHECKPOINT_2026-09-12_RUN834_GREEN_AR.md`
3. `docs/maintenance/HIMMA_A10_W3_EXECUTION_CHECKPOINT_2026-09-12_AR.md`
4. `docs/ops/STATUS.md`
5. `docs/ops/progress.json`
6. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`

اعتبر repository code + migrations + executable tests/CI + canonical contracts هي Source of Truth. لا تعتمد على الذاكرة أو ملخص سابق وحده.

## الحالة الموثقة

- A00–A09 = CLOSED AUDIT.
- W1 = CLOSED GREEN على SHA `ea132c9afbe152d0afa5ae581c058ce3248a0c48`, Run #813 / ID `34467329988`.
- W2 = CLOSED GREEN على SHA `77ac72174a9e21163f6341ea8e0fcc172269eac3`, Run #822 / ID `34548388760`.
- W3 = ACTIVE / NOT GREEN.
- Run #833 / ID `34708600408` = SUCCESS على `79f154f9a3cdee51a713459790d1695aba08d6d7`; `AUD-A11Y-001` CLOSED.
- Run #834 / ID `34710221396` = SUCCESS على exact code SHA `c180146b10467199e6833bacb77873eddcea2143`; Security + Frontend + Backend + Integration/Playwright PASS.
- `AUD-A04-007` CLOSED بواسطة #834.
- `AUD-A11Y-002` CLOSED بواسطة executable contrast evidence داخل #834.
- `AUD-A04-001` ما يزال OPEN لبقية admin presentation ownership خارج Settings.

## أول إجراء إلزامي

اجلب HEAD الحالي وآخر Quality Gate. إذا وجدت commit/batch/CI أحدث من هذا التوثيق وكان ACTIVE أو غير مغلق، **لا تبدأ batch موازية**؛ افهمه وأكمل منه فقط.

إذا لم يوجد عمل أحدث متداخل، أكمل gap واحدًا فقط من W3 وفق severity/dependency، ثم اختبر exact SHA ووثّق قبل فتح غيره.

المتبقي يشمل:
- `AUD-A04-001` remaining AdminUI/presentation unification.
- `AUD-A04-002` partial-source error/retry regressions.
- `AUD-A04-003` canonical Journey scenarios.
- `AUD-A04-005` responsive matrix 320/360/390/430/768/Desktop.
- `AUD-A04-006` final keyboard/dialog regression.
- `AUD-A04-008` filtered audio-review context E2E.
- `AUD-PERF-004`: runtime Google Fonts import ما يزال موجودًا في `globals.css`; المطلوب local/build-time strategy.
- `AUD-A11Y-003`: progressbar executable verification.
- scenario integrity + final exact-SHA W3 Green gate.

لا تعتبر W3 Green حتى تُغلق كل بنودها ويصبح Security + Frontend + Backend + Integration/Playwright Green على exact SHA واحد بعد آخر تعديل.

بعد W3 فقط: W4 ثم W5 ثم W6. **A11 والنشر خارج الجدولة الحالية وممنوعان.**

قيود ثابتة: لا Docker، لا fake ASR، لا Temporary Audio Skip، لا حذف history، لا دمج Speech/Pronunciation Lab، لا final merge، لا Deploy/Railway/Production، لا إضعاف tests، ولا PASS claim دون exact-SHA evidence.
