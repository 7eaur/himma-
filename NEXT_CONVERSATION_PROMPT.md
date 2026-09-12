# NEXT CONVERSATION PROMPT — منصة هِمّة

استخدم هذا النص عند بدء محادثة جديدة لمتابعة التنفيذ دون إعادة العمل السابق:

---

أنت الآن المسؤول الهندسي الكامل عن **منصة هِمّة** في المستودع:

`7eaur/himma-`

فرع التنفيذ الحالي:

`audit/comprehensive-repository-review-2026-09-10`

ابدأ **فعليًا** بجلب HEAD الحالي للفرع، ولا تعتمد على SHA محفوظ دون التحقق منه.

بعدها اقرأ بالترتيب:

1. `docs/maintenance/HIMMA_A10_W3_AUTOMATION_CHECKPOINT_2026-09-12_RUN832_AR.md`
2. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-12_A10_W3_ACTIVE_AR.md`
3. `docs/maintenance/HIMMA_A10_W3_EXECUTION_CHECKPOINT_2026-09-12_AR.md`
4. `docs/ops/STATUS.md`
5. `docs/ops/progress.json`
6. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
7. W1/W2 checkpoints عند الحاجة لإثبات التاريخ، ولا تعِد تنفيذهما.

اعتبر repository code + migrations + executable tests/CI + canonical content contracts هي Source of Truth التنفيذية.

## الحالة التي يجب أن تفهمها قبل أي تعديل

- A00–A09 = **CLOSED AUDIT**. لا تعِدها.
- A10/W1 = **CLOSED GREEN** على SHA `ea132c9afbe152d0afa5ae581c058ce3248a0c48`، Run ID `34467329988`, #813.
- A10/W2 = **CLOSED GREEN** على SHA `77ac72174a9e21163f6341ea8e0fcc172269eac3`، Run ID `34548388760`, #822.
- A10/W3 = **ACTIVE / NOT GREEN**.
- BFF cache blocker القديم أُصلح قبل هذه النقطة.
- MinIO CI bootstrap blocker القديم أُصلح قبل هذه النقطة.
- Run #831 / Run ID `34705138024` على SHA `ff9c415bb697ca6247ae3a27e66d2c7adc5200c8`: Security PASS، Backend PASS، Frontend PASS، Integration setup PASS، لكن Playwright E2E FAIL.
- root cause المثبت في #831 كان locator ambiguity في `apps/web/tests/e2e/vertical-slice.spec.ts`: النص `5 من 10` طابق أيضًا `5 من 10 أساسي`.
- تم إصلاح الاختبار بدقة selector فقط، دون تغيير المنتج أو تخفيف assertion.
- أحدث code-bearing SHA لهذه الدفعة = `82e0bd216ab3d4f3af9d5737b5e29d2102254843` (`fix(e2e): disambiguate canonical progress assertion`).
- `stage/a10-w3-ci` حُرّك إلى هذا exact SHA للتحقق.
- Quality Gate #832 / Run ID `34707136263` على exact SHA `82e0bd216ab3d4f3af9d5737b5e29d2102254843` كان **IN PROGRESS** عند آخر checkpoint.

## أول إجراء إلزامي

افحص أولًا Quality Gate #832 / Run ID `34707136263`.

- إذا كان ما يزال `IN PROGRESS`: لا تبدأ أي batch موازية ولا تغييرات جديدة؛ افحصه فقط واترك نقطة الاستمرار واضحة.
- إذا `FAIL`: اقرأ job logs، حدد أول failure حقيقي، وأصلح root cause دون إضعاف الاختبارات.
- إذا `GREEN`: وثّق exact-SHA evidence ثم أكمل أول W3 gap غير مغلق فقط وفق checkpoint/Gap Register.

لا تعتبر W3 Green لمجرد نجاح #832 إذا كانت بقية بنود W3 غير مغلقة بعد.

ثم أكمل **كل W3** وفق checkpoint/Gap Register، بما في ذلك ما لم يغلق فعليًا من AdminUI consistency، partial-source errors، canonical Journey، responsive matrix، dialogs/tabs accessibility، student-filtered audio review، local/build-time fonts، reduced motion، semantic contrast، progress semantics، وscenario integrity.

بعد W3 Green انتقل إلى W4 ثم W5 ثم W6 فقط. **A11 والنشر خارج الجدولة الحالية**.

W4 يجب أن يغلق أيضًا ملاحظات الشارات/النجوم/الصور الموثقة: approved badge catalog، L3 `نجم الفهم` migration-compatible display، student/admin badge visuals، reward error state، stable asset/catalog identity، audio rerecord ضمن star retry semantics، وعدم منح pending audio reward مبكرًا.

## قيود ثابتة

- لا Docker.
- لا Deploy ولا Railway ولا Production ولا final merge ضمن هذه الجدولة.
- لا fake ASR ولا Temporary Audio Skip.
- لا حذف academic/audio/reward history.
- لا دمج Speech/Pronunciation Lab branches؛ research only.
- `deployment/platform-sandbox` reference only.
- Production ASR غير معتمد؛ machine advisory وHuman Supervisor Review authority.
- لا تدّعي PASS دون exact-SHA evidence.
- لا تغيّر الاختبارات لإخفاء bug حقيقي؛ أصلح root cause، وأي تعديل test يجب أن يحافظ على قوة contract أو يزيد دقته.
- إذا كان CI أو batch سابق ما يزال ACTIVE/RUNNING، لا تنشئ مسار عمل متعارضًا.

لا تكتفِ بتقرير. أكمل التنفيذ من نقطة التوقف، ووثّق كل batch وSHA وrun evidence داخل ملفات الاستمرارية.
