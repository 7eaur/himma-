# قائمة عمل هِمّة V2 للعمال — مصدر الأولويات

**ملاحظة:** هذه قائمة بدء. لا تعد أي مهمة منجزة من مجرد توثيق. المشرف يحدّث الحالة والأولوية والأدلة مع HEAD الحي.

| الأولوية | الرمز | المهمة | القبول المطلوب | التعيين الابتدائي | الحالة |
|---|---|---|---|---|---|
| P0 | HV2-001 | إغلاق نتائج CI Integration وM09 المعلقة على آخر functional SHA وتحديد الأعطال الحقيقية | نجاح backend/frontend/security/integration وM04/M09 على نفس SHA أو تسجيل blocked واضح، وتثبيت سلوك القبلي/الاستئناف | A | PENDING_GATES — A c9e53bb3 race patch ACCEPTED only; CI 40252522540 FAIL (Student360 lint), latest combined CI/M09 pending; exact-SHA full gate required |
| P0 | HV2-002 | رحلة طالب جديد من التسجيل إلى أول سؤال، حفظ إجابة ثم refresh/resume، وعزل V1 تمامًا | E2E مثبت بحساب اصطناعي؛ لا استدعاء V1 /api/profile؛ تفويض/401/403/409/503 | B | REWORK on historical 125f1bd6 (CI integration + M09 FAIL); newer c9e53bb3 M09 SUCCESS but combined HEAD full CI/M09 not proven |
| P1 | HV2-003 | Student360 V2 و19 درسًا ومراجعة خصوصية رمز الدخول عند التبديل بين ملفات الطلاب | لقطة شاشة فعلية وتحليل فشل المصدر والتعافي وعدم تسرب اسم/رمز طالب سابق | B | PENDING_GATES — 709d94c2 lint regression fixed; frontend/backend/security + M04 SUCCESS, integration/M09 still IN_PROGRESS at C review; cross-profile browser evidence required |
| P1 | HV2-004 | معالجة المشغّل الصوتي/الفيديو وأشكال أسئلة البناء/الترتيب على الهاتف | اختبارات targeted + فيديو timeout/error/retry وCSS RTL على 360/390/430/768/1440 | A | PENDING_GATES — c9e53bb3 stale-checkpoint patch ACCEPTED only; 3838cccb ACK retry pending M09, full CI and broader question-template coverage pending |
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
