# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت المسؤول الهندسي الكامل عن منصة هِمّة في `7eaur/himma-`.

فرع التنفيذ: `audit/comprehensive-repository-review-2026-09-10`.

ابدأ دائمًا بجلب HEAD الحالي، ثم اقرأ بالترتيب:
1. `docs/maintenance/HIMMA_A10_W3_AUTOMATION_CHECKPOINT_2026-09-12_RUN833_AR.md`
2. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-12_A10_W3_ACTIVE_AR.md`
3. `docs/maintenance/HIMMA_A10_W3_EXECUTION_CHECKPOINT_2026-09-12_AR.md`
4. `docs/ops/STATUS.md`
5. `docs/ops/progress.json`
6. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`

اعتبر repository code + migrations + executable tests/CI + canonical contracts هي Source of Truth.

## الحالة الحالية

- A00–A09 = CLOSED AUDIT.
- W1 = CLOSED GREEN على SHA `ea132c9afbe152d0afa5ae581c058ce3248a0c48`, Run #813 / ID `34467329988`.
- W2 = CLOSED GREEN على SHA `77ac72174a9e21163f6341ea8e0fcc172269eac3`, Run #822 / ID `34548388760`.
- W3 = ACTIVE / NOT GREEN.
- Run #832 / ID `34707136263` على SHA `82e0bd216ab3d4f3af9d5737b5e29d2102254843` انتهى SUCCESS، وأغلق blocker السابق الخاص بـvertical-slice locator ambiguity.
- الـbatch الحالي هو `AUD-A11Y-001` global reduced-motion policy.
- latest code-bearing SHA = `79f154f9a3cdee51a713459790d1695aba08d6d7`.
- `stage/a10-w3-ci` حُرّك إلى هذا SHA.
- Quality Gate #833 / Run ID `34708600408` كان `QUEUED` عند آخر checkpoint.

## أول إجراء إلزامي

افحص Run #833 / ID `34708600408` قبل أي تعديل.

- إذا QUEUED/IN_PROGRESS: لا تبدأ أي batch موازية.
- إذا FAIL: أصلح أول failure حقيقي من root cause ولا تضعف الاختبارات.
- إذا SUCCESS: وثّق exact-SHA evidence، أغلق `AUD-A11Y-001` إذا gate الكامل مر، ثم أكمل أول W3 gap غير مغلق فقط.

لا تعتبر W3 Green حتى تُغلق كل بنود W3 ويصبح Security + Frontend + Backend + Integration/Playwright Green على exact SHA واحد.

بعد W3 فقط: W4 ثم W5 ثم W6. **A11 والنشر خارج الجدولة الحالية وممنوعان.**

قيود ثابتة: لا Docker، لا fake ASR، لا Temporary Audio Skip، لا حذف history، لا دمج Speech/Pronunciation Lab، لا final merge، لا Deploy/Railway/Production، ولا PASS claim دون exact-SHA evidence.
