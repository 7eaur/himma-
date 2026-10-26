# قائمة عمل هِمّة V2 للعمال — مصدر الأولويات

**ملاحظة:** هذه قائمة بدء. لا تعد أي مهمة منجزة من مجرد توثيق. المشرف يحدّث الحالة والأولوية والأدلة مع HEAD الحي.

| الأولوية | الرمز | المهمة | القبول المطلوب | التعيين الابتدائي | الحالة |
|---|---|---|---|---|---|
| P0 | HV2-001 | إغلاق نتائج CI Integration وM09 المعلقة على آخر functional SHA وتحديد الأعطال الحقيقية | نجاح backend/frontend/security/integration وM04/M09 على نفس SHA أو تسجيل blocked واضح، وتثبيت سلوك القبلي/الاستئناف | A | PENDING_GATES — A dca18efe ACK retry patch ACCEPTED (CI/M04/M09 same SHA SUCCESS); HV2-002 pretest end-to-end and B latest browser gates still OPEN |
| P0 | HV2-002 | رحلة طالب جديد من التسجيل إلى أول سؤال، حفظ إجابة ثم refresh/resume، وعزل V1 تمامًا | E2E مثبت بحساب اصطناعي؛ لا استدعاء V1 /api/profile؛ تفويض/401/403/409/503 | B | PENDING_GATES — first-login/pretest/start/save/refresh/503/retry E2E included and green on 54120663; remaining 401/403/409/422 and live permissions matrix OPEN |
| P1 | HV2-003 | Student360 V2 و19 درسًا ومراجعة خصوصية رمز الدخول عند التبديل بين ملفات الطلاب | لقطة شاشة فعلية وتحليل فشل المصدر والتعافي وعدم تسرب اسم/رمز طالب سابق | B | PENDING_GATES — B 54120663 Chromium test REWORK ACCEPTED patch-only (CI/M04/M09 same SHA SUCCESS); live device/visual/privacy evidence OPEN |
| P1 | HV2-004 | معالجة المشغّل الصوتي/الفيديو وأشكال أسئلة البناء/الترتيب على الهاتف | اختبارات targeted + فيديو timeout/error/retry وCSS RTL على 360/390/430/768/1440 | A | PENDING_GATES — A 33267f07/6d421cd0 media fail-closed ACCEPTED patch-only via combined 54120663 CI/M04/M09 SUCCESS; question types/RTL/device evidence OPEN |
| P1 | HV2-005 | تقارير المشرف V2 منفصلة عن V1 ومنع التقدم/الدرجات غير الرسمية | API + UI + تحكم auth/null policy، مراجعة visual وE2E؛ لا تصدير بيانات طفل خاصة | A/B بعد HV2-001 | BLOCKED_BY_HV2-001 |
| P2 | HV2-006 | جرد وسائط/بنك P09.2 وتجربة سؤال/خيار بكل نوع دون اختلاق أصول | جرد delta موثق، حالات missing/fail-closed، وأصول TEST_ONLY مميزة | وفق توجيه المشرف | BLOCKED_BY_P09_1 |
| P2 | HV2-007 | بوابة الأجهزة الحقيقية Safari/Android وخصوصية S3 | دليل أجهزة حقيقية أو `BLOCKED_EXTERNAL_DEVICE` وتقرير متطلبات اختبار يدوي | إشراف/مالك | BLOCKED_EXTERNAL_DEVICE |

## قواعد الاختيار
1. الالتزام بأي `BLOCKER` أحدث في `SUPERVISOR_DIRECTIVES.md` قبل أعمدة التعيين.
2. المهمة نفسها يجوز أن يكملها B بعد A **إذا سلّم A commit واضحًا وانتهى Lease**، ولا يعملان على الملفات نفسها بالتزامن.
3. لا تنقل `READY` إلى `DONE` إلا بقبول تقني من C وقرار المالك إذا كانت بوابة تربوية/نشر. حالة `IN_PROGRESS` لا تعني نجاحًا.
4. إذا بقي CI ساعة كاملة قيد التشغيل: واصل فحص ملفات مستقلة وتحضير اختبارات مستهدفة، ولا تنتظر بلا عمل أو تعيد تشغيل بوابة شاملة لكل تغيّر صغير.

## مراجعة C — 2026-10-26 04:47 Asia/Aden
1. **أولًا:** A يتابع CI Integration على أحدث SHA وظيفي (بعد إصلاح B)، ويقرأ نتيجة M09 للفيديو `3838cccb`؛ لا يعيد كتابة VideoPlayer إن نجحت الاختبارات.
2. **ثانيًا:** B يتابع M09/CI على `709d94c2`، ويتحقق من Browser cross-profile A→B→A مع استجابات متأخرة ورمز مخفي. لا تقبل HV2-003 قبل PASS.
3. **ثالثًا:** استمر في HV2-002 إلى أن يثبت pretest start/save/retry/resume مع حساب تجريبي على نسخة مدمجة واحدة؛ فشل `125f1bd6` تاريخي وليس حكمًا على `709d94c2`.
4. **حاجز إصدار:** `checkSuites=false` على Railway للخدمتين؛ لا إعلان جاهزية الإنتاج أو تعديل إعدادات النشر دون موافقة المالك.
5. **مؤجل:** HV2-005/006/007 حتى البوابات المطلوبة، مع بقاء الأجهزة الحقيقية وS3 تحت `BLOCKED_EXTERNAL_DEVICE`.

## تحديث A — 2026-10-26 05:08 Asia/Aden
- HV2-001: `709d94c2` الآن **CI + M04 + M09 SUCCESS على SHA واحد** (CI 40254864101, M04 40254864104, M09 40254864109). لا تعتبر المهمة CLOSED قبل اعتماد C وتغطية HV2-002.
- HV2-004: `3838cccb` M09 SUCCESS؛ `dca18efe` أصلح إعادة إرسال إجابة بعد فقد ACK مع اختبارات Unit. **PENDING_GATES** على SHA الجديد: CI 40257452139 / M04 40257452187 SUCCESS / M09 40257452180. لا تغيّر حالات الجدول الأصلية دون مراجعة المشرف.
- Railway auto-deployed dca18efe قبل اكتمال CI/M09؛ `checkSuites=false` للخدمتين؛ RELEASE_BLOCKER D-005 لا يزال قائمًا.

## تحديث B — 2026-10-26 05:35 Asia/Aden
- HV2-003: `f4497b84` فصل فشل اتصال المصادر التاريخية الاختيارية عن تحميل هوية الطالب ومصدر V2، وأضاف اختبار network abort/retry وتباطؤ A→B→A في الاتجاهين.
- **فجوة بوابة مهمة:** لم تكن اختبارات cross-device وpartial-source ضمن CI/M09؛ `129dcbcd` أضافها في كلا المسارين. `PENDING_GATES` حتى [CI 40259709522](https://github.com/7eaur/himma-/actions/runs/40259709522) و[M09 40259709545](https://github.com/7eaur/himma-/actions/runs/40259709545) يثبتان مرورها.
- [M04 40259653164](https://github.com/7eaur/himma-/actions/runs/40259653164) SUCCESS على functional SHA؛ لا يغني عن Playwright الجديد. HV2-002 يظل مفتوحًا لاختبار pretest/start/save/resume وتفويض الحالات الحقيقية.
- D-005 ما زال قائمًا: Railway auto-deployed `f4497b84` قبل CI/M09؛ لا تعديل نشر دون موافقة المالك.

## توجيه C — 2026-10-26 05:53–05:57 Asia/Aden (مراجعة 20261026-0553-C)
1. **P0 — B / HV2-003 REWORK:** [CI 40259709522](https://github.com/7eaur/himma-/actions/runs/40259709522) و[M09 40259709545](https://github.com/7eaur/himma-/actions/runs/40259709545) على `129dcbcd` فشلا في **اختبارَي Chromium نفسهما** (38 PASS / 2 FAIL). افتح [job integration 121370847217](https://github.com/7eaur/himma-/actions/runs/40259709522/job/121370847217) و[release-readiness 121369221383](https://github.com/7eaur/himma-/actions/runs/40259709545/job/121369221383)، وافحص traces/Playwright artifact، وحدد نقطة التعليق في اختبار A→B→A بدل زيادة timeout أو حذف assertions. أصلح test harness أو runtime حسب السبب المثبت، مع الحفاظ على إخفاء هوية ورمز الطالب السابق.
2. **P0 — B / اختبار V1 المكافآت:** اختبار `student-detail-partial-source-errors.spec.ts:71` يتوقع «النجوم» داخل `ملخص الطالب`؛ المصدر الحالي يعرض V2 summary في هذا الموضع، بينما «نجوم V1 التاريخية» في تبويب `overview`. صحح سياق الاختبار إلى تبويب V1، مع إبقاء شرط `—` عند الفشل و`0` فقط بعد نجاح retry؛ **لا تُعد عرض نجوم V1 إلى ملخص V2 لإرضاء اختبار قديم**.
3. **A / HV2-001/004:** إصلاح `dca18efe` مقبول **كـpatch فقط** بعد نجاح CI/M04/M09 على نفس SHA. لا تكرر فحصًا ناجحًا؛ استكمل أنواع الأسئلة/RTL، ولا تتداخل مع ملفات Student360 المحجوزة لبقية العمل. HV2-002 (قبلي/حفظ/استئناف) لا يزال مفتوحًا.
4. **C / RELEASE_BLOCKER:** Railway web نشر `f4497b84` SUCCESS، بينما إضافة اختبارَي Student360 للبوابات كشفت فشلهما لاحقًا؛ `checkSuites=false` للخدمتين. لا اعتماد إنتاج أو دمج. لا توجد أدلة تسرب حقيقية مثبتة؛ `CONTROL.mode=ACTIVE` مع حظر اعتماد الإصدار.
5. **أدلة غير مكتملة:** CI على docs HEAD `c4b977d` كان integration IN_PROGRESS وقت الفحص؛ M09 `f4497b84` IN_PROGRESS. لا تعتبر هذه نتائج نجاح. فحوص الخصوصية والـ19 درسًا وخصوصية التسجيلات هنا مصدر/اختبارات فقط، وليست اختبار أجهزة/S3 حي.

## تحديث A — 2026-10-26 06:04 Asia/Aden
- HV2-004: `33267f07` و`6d421cd0` fail-closed على الوسائط المرجعية الناقصة (audio/image/video) مع عدم كشف تلميحات التقييم؛ أربع اختبارات Jest وRTL text wrapping. Frontend/Security/M04 SUCCESS، CI Integration/M09 PENDING على SHA `6d421cd0`. لا نقل للحالة إلى DONE دون مراجعة C.
- HV2-003: لا تزال REWORK عند B (اختبارا Chromium فاشلان على `129dcbcd`)؛ لم يعدل A ملفات Student360.
- D-005/D-010: Railway auto-deployed `6d421cd0` قبل اكتمال CI/M09؛ RELEASE_BLOCKER باقٍ.

## تحديث WORKER_B — 2026-10-26 06:31 Asia/Aden
- **HV2-003:** عولجت أخطاء اختبارَي Chromium المشار إليهما في D-009 على SHA `54120663`؛ اختبار الانتقال يستخدم روابط Next حقيقية، ونجوم V1 داخل الأرشيف فقط. **لا تغيّر الحالة إلى DONE**: CI frontend/security SUCCESS، لكن E2E/CI backend/M04/M09 لم تنتهِ عند التسليم؛ المشرف C وحده يقرر قبول patch.
- **HV2-002:** لا يزال مفتوحًا؛ اختبار first-login/pretest/503/resume مدرج في CI/M09 ويحتاج نتائج Chromium على SHA متكامل.
- **تحذير:** SHA الوسيط `0e627eed` كان معطوب TypeScript؛ تم تصحيحه في `54120663`. لا تعتمد عليه.

## توجيه C — 2026-10-26 06:50 Asia/Aden (`20261026-0650-C`)
1. **B / HV2-002 P0:** E2E أول دخول/بدء/حفظ/refresh/503/retry أصبح ناجحًا ضمن CI/M09 على `54120663`؛ انتقل إلى مصفوفة التفويض وحالات 401/403/409/422 وعودة 503 في start/save/resume، مع اختبار عدم تكرار الإجابة. لا تغلق المهمة حتى التحقق.
2. **A / HV2-004 P1:** إصلاح منع إرسال السؤال عند غياب الوسائط/الفيديو غير المدعوم وعدم كشف correctness/hint في القبلي مقبول كـpatch. أكمل التغطية المرئية/RTL لقوالب الاختيار والترتيب/التركيب، ولا تفتح أسئلة تفتقر إلى أصولها.
3. **B / HV2-003 P1:** إصلاح الاختبارين مقبول على `54120663` بعد CI/M04/M09 SUCCESS؛ حافظ على العزل واطلب مراجعة صور Playwright/الأجهزة قبل قبول كامل.
4. **Release BLOCKED:** Railway web نشر `54120663` وAPI لم ينشر SHA مطابقًا؛ `checkSuites=false` للخدمتين. لا نشر أو دمج أو إعلان قبول مرحلة.
5. **C next:** راجع نتائج A/B الجديدة على exact SHA والـdiff، واحفظ حدود التدقيق الفعلي، واطلب Playwright artifacts فقط إذا كانت قابلة للقراءة بدون كشف بيانات خاصة.

## تحديث A — 2026-10-26 07:04 Asia/Aden
- HV2-004: `1d5b3e5e` أضاف عرض صور عناصر `sequence/build_word` داخل شريط الترتيب ومنع الإرسال عند `options=[]`، مع اختبارَي Jest. **PENDING_GATES** حتى نتائج [CI 40267045694](https://github.com/7eaur/himma-/actions/runs/40267045694) / [M04 40267045663](https://github.com/7eaur/himma-/actions/runs/40267045663) / [M09 40267045676](https://github.com/7eaur/himma-/actions/runs/40267045676) ومراجعة C. لا تعديل على مهمة B أو حالة RELEASE_BLOCKER.
