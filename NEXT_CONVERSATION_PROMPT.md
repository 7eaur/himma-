# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت المسؤول الهندسي الكامل عن منصة هِمّة في `7eaur/himma-`.

فرع التنفيذ: `audit/comprehensive-repository-review-2026-09-10`.

ابدأ دائمًا بجلب HEAD الحالي وآخر CI قبل أي تعديل، ثم اقرأ بالترتيب:
1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-13_A10_W3_RUN840_ACTIVE_AR.md`
2. `docs/maintenance/HIMMA_A10_W3_AUTOMATION_CHECKPOINT_2026-09-13_RUN840_ACTIVE_AR.md`
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
- Run #833 = SUCCESS؛ `AUD-A11Y-001` CLOSED.
- Run #834 = SUCCESS؛ `AUD-A04-007` و`AUD-A11Y-002` CLOSED.
- Run #835 = SUCCESS؛ `AUD-A11Y-003` CLOSED.
- Run #836 = SUCCESS؛ `AUD-A04-006` CLOSED.
- Run #837 = SUCCESS؛ `AUD-A04-002` CLOSED.
- Run #838 / ID `34717561661` = SUCCESS؛ `AUD-A04-003` CLOSED.
- Run #839 / ID `34718862139` = SUCCESS على `4d66d0d72f1685e04d1adfc42d855289ba76419f`؛ `AUD-A04-005` CLOSED.
- Batch الحالية فقط: `AUD-A04-008 — filtered audio-review context`.
- exact code-bearing SHA: `56854c5a903a6b86dcec1653129f8ca91d3b6ea7`.
- Quality Gate #840 / ID `34721724505` بدأ على هذا SHA وكان `QUEUED` عند آخر توثيق.
- أضيف backend regression حقيقي للفلترة/metadata/pending→rerecord/replacement→graded/history preservation.
- أضيف Playwright regression للسياق المفلتر، profile return link، valid grading، وrerecord UI.
- `AUD-PERF-004` ما يزال OPEN؛ المحاولة الجزئية السابقة أُعيدت بالكامل.

## أول إجراء إلزامي

اجلب HEAD الحالي وافحص Run #840 قبل أي تعديل.

- إذا كان #840 ما يزال ACTIVE/QUEUED: لا تبدأ أي تغيير كود ولا batch موازية.
- إذا SUCCESS: أغلق `AUD-A04-008` بواسطة exact-SHA evidence، حدّث Master Gap Register وcontinuity/status/progress، ثم اختر gap واحدة فقط تالية من W3.
- إذا FAILURE: افتح jobs وحدد أول failure حقيقي، أصلحه من root cause، ولا تضعف الاختبار.

## W3 المتبقي بعد نجاح #840

- `AUD-A04-001` remaining AdminUI/presentation unification where ownership is proven.
- `AUD-PERF-004`: complete local/build-time font strategy; runtime Google Fonts dependency ما يزال OPEN.
- cross-device/scenario integrity وفق Master Gap Register.
- final exact-SHA W3 Green gate.

لا تعتبر W3 Green حتى تُغلق كل بنودها ويصبح Security + Frontend + Backend + Integration/Playwright Green على exact SHA واحد بعد آخر تعديل.

بعد W3 فقط: W4 ثم W5 ثم W6. **A11 والنشر خارج الجدولة الحالية وممنوعان.**

قيود ثابتة: لا Docker، لا fake ASR، لا Temporary Audio Skip، لا حذف history، لا دمج Speech/Pronunciation Lab، لا final merge، لا Deploy/Railway/Production، لا إضعاف tests، ولا PASS claim دون exact-SHA evidence.
