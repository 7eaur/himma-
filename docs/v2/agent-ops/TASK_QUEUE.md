# قائمة عمل هِمّة V2 للعمال — مصدر الأولويات

**ملاحظة:** هذه قائمة بدء. لا تعد أي مهمة منجزة من مجرد توثيق. المشرف يحدّث الحالة والأولوية والأدلة مع HEAD الحي.

| الأولوية | الرمز | المهمة | القبول المطلوب | التعيين الابتدائي | الحالة |
|---|---|---|---|---|---|
| P0 | HV2-001 | إغلاق نتائج CI Integration وM09 المعلقة على آخر functional SHA وتحديد الأعطال الحقيقية | نجاح backend/frontend/security/integration وM04/M09 على نفس SHA أو تسجيل blocked واضح، وتثبيت سلوك القبلي/الاستئناف | A | PENDING_GATES — A dca18efe ACK retry patch ACCEPTED (CI/M04/M09 same SHA SUCCESS); HV2-002 pretest end-to-end and B latest browser gates still OPEN |
| P0 | HV2-002 | رحلة طالب جديد من التسجيل إلى أول سؤال، حفظ إجابة ثم refresh/resume، وعزل V1 تمامًا | E2E مثبت بحساب اصطناعي؛ لا استدعاء V1 /api/profile؛ تفويض/401/403/409/503 | B | PENDING_GATES — C1248: B1230 POST identity/kind ACCEPTED patch-only (CI/M04/M09 green on 7ea8d58c); B1235 payload guard a1d7c00 integration/M09 pending; full live/device acceptance OPEN |
| P1 | HV2-003 | Student360 V2 و19 درسًا ومراجعة خصوصية رمز الدخول عند التبديل بين ملفات الطلاب | لقطة شاشة فعلية وتحليل فشل المصدر والتعافي وعدم تسرب اسم/رمز طالب سابق | B | PENDING_GATES — B 54120663 Chromium test REWORK ACCEPTED patch-only (CI/M04/M09 same SHA SUCCESS); live device/visual/privacy evidence OPEN |
| P1 | HV2-004 | معالجة المشغّل الصوتي/الفيديو وأشكال أسئلة البناء/الترتيب على الهاتف | اختبارات targeted + فيديو timeout/error/retry وCSS RTL على 360/390/430/768/1440 | A | PENDING_GATES — C1248: A1204 stale audio race ACCEPTED patch-only (CI/M04/M09 green on c424e247); real media/device validation OPEN |
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

## توجيه C — 20261026-0745-C
1. **P0 / B HV2-002:** لا تعلن نجاح E2E الجديد قبل انتهاء CI `40269530363` وM09 `40269530381` على `f9c250e7`. backend/frontend/security وM04 نجحت؛ integration وM09 قيد التنفيذ. بعدها 404/cross-student وprivacy/ownership.
2. **P1 / A HV2-004:** `1d5b3e5e` **ACCEPTED patch-only** عبر CI/M04/M09 على نفس SHA؛ استكمل ترتيب الصور/تركيب الكلمات وRTL/المقاسات وأدلة شاشة فعلية. لا تغلق المرحلة.
3. **RELEASE_BLOCKER:** Railway web `f9c250e7` وAPI `89f0b1db` online، لكن `checkSuites=false` لكليهما؛ لا اعتماد إصدار حتى قرار المالك. لا يوجد دليل مباشر يستلزم PAUSED.
4. **HV2-003/005/006/007:** أبقها مفتوحة بحسب بواباتها؛ اختبار 19 درسًا وخصوصية الصوت static/CI فقط، دون أجهزة/S3 حي.

## تحديث A — 2026-10-26 08:06 Asia/Aden
- `HV2-004`: Commit `898971de` وصف نصوص الخيارات والمقاطع لقارئ الشاشة وRTL وأهداف لمس 44px مع اختبارَي Jest. Frontend type/lint/unit PASS في CI job، بينما exact-SHA CI/M04/M09 لم تكتمل كلها بعد؛ **PENDING_GATES** حتى مراجعة C.
- `HV2-002`: CI/M04/M09 على `f9c250e7` أصبحت SUCCESS؛ تظل 404/cross-student ومراجعة C مطلوبة. لا تعديل على نطاق B.
- `RELEASE_BLOCKER`: Railway `checkSuites=false` مستمر، والنشر الآلي ليس قبول QA.


## توجيه المشرف C — 2026-10-26 08:50 Asia/Aden · `20261026-0850-C`
1. **P0 B / HV2-002:** `d7b639d9` أضاف اختبارات cross-student 404/owner replay وV1 isolation عبر Backend/Chromium BFF. [CI 40275015229](https://github.com/7eaur/himma-/actions/runs/40275015229) و[M09 40275015023](https://github.com/7eaur/himma-/actions/runs/40275015023) ما زالا IN_PROGRESS، M04 40275015096 SUCCESS؛ **PENDING_GATES** حتى انتهاء الاختبارين ثم مراجعة trace إن فشلا. لا إعلان نجاح كامل.
2. **P1 A / HV2-004:** `898971de` **ACCEPTED patch-only** عبر CI/M04/M09 SUCCESS على SHA واحد؛ المطلوب فحص RTL/overflow/صور وأهداف لمس على 360/390/430/768/1440 بلقطات حقيقية أو توثيق `BLOCKED_VISUAL`. لا تكرر patch المقبول.
3. **P1 HV2-003/005 + P2 HV2-007:** 19 درسًا/403/أرشيف الصوت مدعومة باختبارات مصدر وbackend؛ مراجعة Playwright ZIP/الأجهزة/S3 الحقيقية لم تتم؛ تبقى PENDING/EXTERNAL BLOCKED.
4. **RELEASE_BLOCKER:** Railway web `d7b639d9` / API `d25e2482` ONLINE لكن `checkSuites=false` لكليهما؛ لا اعتماد إصدار أو دمج أو نشر يدوي قبل قرار المالك. `CONTROL.mode=ACTIVE` دون دليل فساد حي.


## تحديث A — 2026-10-26 08:58 Asia/Aden
- HV2-004: `595fcb93` أضاف تغطية Playwright لشريط الترتيب المصور عبر 360/390/430/768/1440 و44px/overflow وإزالة/إعادة اختيار، مع صور عند تشغيل الاختبار. **PENDING_GATES** حتى CI/M04/M09 النهائية ومراجعة C؛ لا `VISUAL_VERIFIED` بعد.
- HV2-002: `d7b639d9` CI/M04/M09 **SUCCESS** على SHA واحد (40275015229/40275015096/40275015023). اترك قبول patch-only للمشرف، مع بقاء سيناريوهات production/devices مفتوحة.
- RELEASE_BLOCKER: Railway web بدأ BUILDING للـtest-only commit بينما CI/M09 لم ينتهيا؛ لا إعلان جاهزية نشر.

## تحديث B — 2026-10-26 09:30 Asia/Aden
- HV2-002: `86a9b4f41d1f` يضيف اختبار Chromium لنجاح POST الحقيقي مع ضياع ACK عند العميل في start/answer؛ يجب أن يبقى session_id وsubmit_key كما هما وأن يساوي عدد الإجابات المحفوظة 1 بعد reload. **PENDING_GATES** حتى CI 40280282347 / M04 40280282439 / M09 40280282476 ومراجعة C؛ لا تغيير لحالة DONE.
- اختبارات B السابقة `d7b639d9` أصبحت CI/M04/M09 SUCCESS على نفس SHA؛ تحتاج قبول C patch-only. Railway release blocker وغياب جهاز حقيقي مستمران.

## توجيه المشرف C — 2026-10-26 2026-10-26T09:51:40.083+03:00 · `20261026-0950-C`
1. **B / HV2-002 (P0):** `d7b639d9` cross-student 404/replay/V1 isolation **ACCEPTED patch-only** بعد CI/M04/M09 SUCCESS على نفس SHA. الاختبار الجديد `86a9b4f4` لفقد ACK بعد commit: M04 `40280282439` وM09 `40280282476` وCI `40280282347` جميعها **SUCCESS** على نفس SHA؛ **ACCEPTED test patch-only** مع استمرار HV2-002 PENDING_GATES للقبول الكامل. لا تخفف شرط نفس session_id/submit_key وanswered=1. افحص الفرق بين فقد ACK ومحاكاة 503 قبل الكتابة.
2. **A / HV2-004 (P1):** `595fcb93` **ACCEPTED test patch-only**؛ CI `40277135230` وM04 `40277135087` وM09 `40277135173` SUCCESS. C حمّل Playwright artifact `12630639993` وعاين الصور الخمس `360/390/430/768/1440`: الصورة الاصطناعية بقيت في الشريط، العناصر ملتفة دون قص أفقي ظاهر، والواجهة RTL. هذه **مراجعة بصرية فعلية للـfixture فقط**؛ لا تعني أجهزة حقيقية/وسائط تعليمية معتمدة أو اكتمال HV2-004.
3. **C / privacy:** `test_v2_student_readmodel.py` يتحقق من 19 درسًا وعدم ظهور access_code/private_answer؛ `test_v2_audio_archive.py` يتحقق من 403 وإخفاء storage_key وأحدث تسجيل مراجَع. اختبارات المصدر/CI ليست دليلًا على سلامة S3 حي أو عدم تسرب فعلي في جهاز حقيقي.
4. **RELEASE_BLOCKER:** Railway web `86a9b4f` ONLINE/SUCCESS، API `d25e2482` ONLINE/SUCCESS، و`source.checkSuites=false` للخدمتين. Web intermediate `8e4d64d` FAILED ثم إصلاحه نجح في النشر؛ خطر النشر قبل QA مثبت. `CONTROL.mode=ACTIVE` لغياب دليل فساد/تسرب حي؛ يمنع اعتماد إصدار/دمج/نشر يدوي إلى قرار المالك.

## تحديث A — 2026-10-26 10:09 Asia/Aden · `20261026-1003-A`
- **HV2-004:** `f4f305ef` أضاف fail-closed لصور `ready` التي يفشل تحميلها في المتصفح وللصوت الذي يفشل تشغيله، مع فك الحظر بعد إعادة تشغيل الصوت؛ اختبارا Jest جديدان. **PENDING_GATES** على CI `40283675056` / M04 `40283675067` / M09 `40283675071`، كلها IN_PROGRESS عند التسليم؛ لا تغلق المهمة حتى مراجعة C.
- **HV2-002:** يبقى للعامل B حسب D-024؛ لا تغيّر صلاحيات الطالب/الجلسات من عمل A هذا.
- **Release:** Railway web BUILDING على `f4f305ef` وAPI SKIPPED، مع استمرار D-027؛ لا إعلان جاهزية ولا دمج.

## تحديث WORKER_A — 2026-10-26T11:09:06.814+03:00 · `20261026-1106-A`
- **HV2-001 / CI unblock:** `67fbc499` أصلح تطبيع URL في اختبار الصور المصطفة؛ [CI 40290066904](https://github.com/7eaur/himma-/actions/runs/40290066904) frontend unit tests SUCCESS (81 tests historical, new exact-head frontend job success), بينما backend/integration وم04/م09 حسب الحالة الحية: in_progress/null / in_progress/null. لا تغير حالة PENDING_GATES إلى DONE قبل مراجعة C.
- **HV2-004:** إصلاح اختبار فقط؛ الحفاظ على fail-closed للوسائط الحقيقية. الاختبار المرئي TEST_ONLY لا يعني جهازًا حقيقيًا.
- **HV2-002:** B `d1646ffb` CI فشل بسبب اختبار A الموروث؛ M04/M09 SUCCESS. راجع CI على `67fbc499` المجمّع قبل اعتماد إصلاح B، واحتفظ بحماية اختلاف session ID.
- **RELEASE_BLOCKER:** Railway `checkSuites=false` مستمر؛ لا نشر يدوي أو دمج.

## تحديث المشرف C — 2026-10-26 11:49:43 Asia/Aden · `20261026-1146-C`
1. **P0 B — HV2-002:** بعد قبول GET guard `d1646ffb` على النسخة المدمجة `67fbc499`، اكتشفت فجوة تغطية **POST/answer → onLessonChange → setAssessment** دون مطابقة `session_id`؛ أضف تحقق هوية ونوع، fail-closed، وChromium regression مع استئناف سليم. لا تتداخل مع ملفات A.
2. **P1 A — HV2-004:** A1003 fail-closed media + A1106 Jest URL assertion **ACCEPTED patch-only** على CI/M04/M09 SUCCESS SHA `67fbc499`؛ ركّز على أصول فعلية وقوالب أخرى، ولا تكرر إصلاح URL.
3. **P1 B — HV2-003:** تبقى PENDING_GATES لمراجعة الأجهزة/الخصوصية البصرية الحية. مصدر 19 درسًا و403 موجود لكن لا يغني عن اختبار واقعي.
4. **RELEASE BLOCKED:** Railway web `67fbc499` وAPI `d25e2482` مختلفان؛ `checkSuites=false` للخدمتين. لا تغيير Railway/دمج main/إعلان قبول إصدار.
5. **التحقق:** CI `40290066904` (4/4 jobs SUCCESS)، M04 `40290066702`، M09 `40290066736` SUCCESS؛ artifacts موجودة لكن لم تُفحص الصور بصريًا الآن.

## تحديث A — 2026-10-26T09:08:05.674Z / 20261026-1204-A
- HV2-004: أصلح سباق أحداث الصوت القديمة عند إيقاف/تبديل Audio على `c424e2476030`، وأضاف اختبارَي Jest. حالة الفحوص عند التسليم: backend=in_progress/pending, frontend=completed/success, security=completed/success; M04 completed/success; M09 in_progress/pending. **PENDING_GATES** حتى C؛ لا إعلان اكتمال الأجهزة/وسائط حقيقية.
- B يحتفظ بملف POST assessment guard ضمن parallel lease مستقل؛ لا تعديل نطاقه. D-030 release blocker مستمر.

## تحديث WORKER_B — 2026-10-26 12:09 Asia/Aden · `20261026-1230-B`
- **HV2-002 P0:** `7ea8d58c32bd` يضيف guard لاستجابة POST/answer على `session_id` و`kind` ويخفي السؤال عند mismatch ثم يستعيد حالة الجلسة بـGET؛ اختبارا Chromium جديدان (committed answer + wrong ID / wrong kind + resume answered=1).
- **لا قبول مبكر:** CI `40297215729` / M04 `40297215649` / M09 `40297215668` IN_PROGRESS على SHA الجديد عند التسليم؛ يجب فحص Chromium الفعلي والـtraces قبل قبول C.
- **HV2-003:** لم تُعدّل ملفات Student360؛ تظل مراجعة الأجهزة/الخصوصية البصرية الحية مفتوحة.
- **A1204:** إصلاح سباق الصوت محفوظ `c424e247`، lease A محرر؛ لا تتداخل معه. **RELEASE_BLOCKER:** Railway checkSuites=false للخدمتين والنشر الآلي مستمر، دون أي تعديل إعدادات.

## تحديث B — 2026-10-26T12:39:15+03:00
- HV2-002: `a1d7c00ebaa2` أضاف fail-closed لحمولات GET/POST الناقصة أو progress غير صالح، و3 اختبارات Chromium داخل البوابة الحالية. **PENDING_GATES** حتى CI 40301000442 / M04 40301000136 / M09 40301000316 على SHA نفسه؛ frontend/security SUCCESS وقت التسليم. لا تنقل HV2-002 إلى DONE قبل مراجعة C والتحقق الحي.
- `7ea8d58c` CI/M04/M09 SUCCESS الآن (تصحيح حقيقة تاريخية عند B1230)، لكن هذا لا يعتمد التعديل الأحدث. `checkSuites=false` خطر نشر مفتوح.

## توجيه أولوية المشرف C — 2026-10-26 12:52 Asia/Aden · 20261026-1248-C
1. **P0 / B HV2-002:** نتيجة CI integration `40301000442` وM09 `40301000316` على `a1d7c00` قبل أي قبول. إن فشل الاختبار الجديد افحص trace/سبب المصدر ولا تُضعف assertions. عند النجاح ارفع حالة patch للمشرف.
2. **P0 / B HV2-002 بعد البوابة:** حالة Browser `answered=2 → answered=1` مع نفس session/kind، ACK متراجع صالح بنيويًا، ثم recovery GET دون duplicate POST. لا تعتبر اختبار `answered=-1` إثباتًا لهذه الحالة.
3. **P1 / A HV2-004:** `c424e247` ACCEPTED patch-only؛ تابع الوسائط الفعلية وRTL دون تعديل ملفات B أو اختلاق أصول.
4. **P1 / C HV2-003 وخصوصية الصوت:** فحص مصدر 19 درسًا/403/audio archive قائم، وتمت مشاهدة عينات Playwright سابقة، لكن الأجهزة الحقيقية/S3/الخصوصية الحية لا تزال PENDING/EXTERNAL.
5. **حاجز إصدار:** Railway `checkSuites=false` للخدمتين وAPI/Web SHA مختلفان، دون دليل توافق حي. لا دمج main أو تغيير النشر أو اعتماد إصدار.
