# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت المسؤول الهندسي الكامل عن منصة هِمّة في `7eaur/himma-`.

فرع التنفيذ: `audit/comprehensive-repository-review-2026-09-10`.

ابدأ دائمًا بجلب HEAD الحالي وآخر CI قبل أي تعديل، ثم اقرأ بالترتيب:
1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-13_A10_W3_RUN842_ACTIVE_AR.md`
2. `docs/maintenance/HIMMA_A10_W3_AUTOMATION_CHECKPOINT_2026-09-13_RUN842_ACTIVE_AR.md`
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
- Runs #833–#839 أغلقت `AUD-A11Y-001`, `AUD-A04-007`, `AUD-A11Y-002`, `AUD-A11Y-003`, `AUD-A04-006`, `AUD-A04-002`, `AUD-A04-003`, `AUD-A04-005` على exact-SHA gates Green.
- Batch الحالية فقط: `AUD-A04-008 — filtered audio-review context`.
- Run #840 / ID `34721724505` = FAILURE على `56854c5a903a6b86dcec1653129f8ca91d3b6ea7`: response contract كان يعيد `status: ok` بدل الحالة المحفوظة `graded/rerecord_required`.
- root fix الأول: `0afcb5e157038e0453f146afb9d1521f1156c347`.
- Run #841 / ID `34723091853` = FAILURE على `0afcb5e...`: Security/Frontend SUCCESS، Backend نفّذ 855 اختبارًا وكانت النتيجة `1 failed, 854 passed`; الفشل الوحيد كان في اختبار W3 الجديد بسبب استخدام relationship غير موجود `AudioSubmission.response`.
- ORM الرسمي يعرّف `AudioSubmission.response_id` فقط؛ تم الحفاظ على assertion نفسه وتحويله لمسار IDs الرسمي `AudioSubmission → AttemptResponse → Attempt → AssessmentSession`.
- root correction/code SHA الحالي: `562b4eb3ef831cf7b8b51bd7d5e33145917cb382`.
- Quality Gate #842 / ID `34723513642` يعمل على exact SHA `562b4eb3...`; آخر حالة موثقة `QUEUED`.
- `AUD-PERF-004` ما يزال OPEN.

## أول إجراء إلزامي

اجلب HEAD الحالي وافحص Run #842 قبل أي تعديل.

- إذا كان #842 ACTIVE/QUEUED: لا تبدأ أي تغيير كود ولا batch موازية.
- إذا SUCCESS: أغلق `AUD-A04-008` بواسطة exact-SHA evidence، حدّث Master Gap Register وcontinuity/status/progress، ثم اختر gap واحدة فقط تالية من W3.
- إذا FAILURE: افتح job logs وحدد أول failure حقيقي وأصلحه من root cause فقط، ولا تضعف الاختبار.

## W3 المتبقي بعد نجاح #842

- `AUD-A04-001` remaining AdminUI/presentation unification where ownership is proven.
- `AUD-PERF-004`: complete local/build-time font strategy; runtime Google Fonts dependency ما يزال OPEN.
- cross-device/scenario integrity وفق Master Gap Register.
- final exact-SHA W3 Green gate.

لا تعتبر W3 Green حتى تُغلق كل بنودها ويصبح Security + Frontend + Backend + Integration/Playwright Green على exact SHA واحد بعد آخر تعديل.

بعد W3 فقط: W4 ثم W5 ثم W6. **A11 والنشر خارج الجدولة الحالية وممنوعان.**

قيود ثابتة: لا Docker، لا fake ASR، لا Temporary Audio Skip، لا حذف history، لا دمج Speech/Pronunciation Lab، لا final merge، لا Deploy/Railway/Production، لا إضعاف tests، ولا PASS claim دون exact-SHA evidence.
