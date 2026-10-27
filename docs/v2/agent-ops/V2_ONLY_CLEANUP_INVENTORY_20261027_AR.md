# السجل التنفيذي الموحد للمشاكل والتنظيف والقبول — هِمّة V2

**التاريخ:** 2026-10-27 — Asia/Aden  
**الحالة:** OPEN / P09 FUNCTIONAL PENDING / P10 MEDIA PENDING / RELEASE BLOCKED  
**مستودع المشروع:** `7eaur/himma-`  
**الفرع الأساسي المطلوب:** `v2/01-learning-foundation-20261007`، HEAD المفحوص `57a6e0dd882d2a9a477dcfa0a553acefe987bdf5`  
**فرع إصلاح معزول:** `cleanup/v2-only-20261027`؛ أحدث رأس وظيفي قبل تحديث هذه الوثيقة `6fdb298b07b32348c8158bdae86b397822100f8d`. راجع HEAD عند كل استئناف.  
**الرابط المنشور للفحص:** https://himma-web-production-eafd.up.railway.app  
**التسليم:** `docs/v2/agent-ops/WORK_HANDOFF_20261027_AR.md`  
**مصفوفة قبول المتصفح:** `docs/v2/agent-ops/WORK_BROWSER_ACCEPTANCE_MATRIX_20261027_AR.md`  
**الوثائق التنفيذية الأخرى:** `docs/v2/work-owner/CURRENT_STATUS_AR.md`، `docs/v2/09_IMPLEMENTATION_ROADMAP_AR.md`، `docs/v2/22_FULL_SYSTEM_COVERAGE_AND_ACCEPTANCE_MATRIX_AR.md`، `docs/v2/25_V1_TO_V2_FEATURE_PARITY_REGISTER_AR.md`، `docs/v2/51_P08_P10_SUPERVISOR_STUDENT_UX_PLAN_AR.md`.

> هذه **قائمة المشاكل والمتطلبات والفحوص الواجبة**، لا شهادة بأن كل المسارات والملفات وبيانات الإنتاج قد اختبرت. اذكر الدليل عند إغلاق كل بند. مصدر القرار: طلب المالك الصريح اللاحق بحذف V1 من الواجهات والكود ثم بياناته بعد backup وجرد وموافقة نهائية؛ هذا يغيّر سياسة الإبقاء على أرشيف V1 الظاهر المنصوص عليها في التسليم الأقدم. لا يُسمح بحذف الدليل أو بيانات المستخدمين تلقائيًا.

## 0) قرارات المالك الملزمة وغير القابلة للتجاوز

1. **V2 وحده المنتج النهائي** للطالب والمشرف: قبلي → تسكين L1/L2/L3 → درس + فيديو/تمهيد + تدريب موجّه + اختبار مستقل → دعم تلقائي مدمج → بعدي. لا أنشطة ومكافآت وتقارير V1 ضمن المنتج.
2. **لا أرشيف V1 داخل الواجهات** أو تبويبات أو روابط مخفية أو نسخ متنافسة؛ استبدال الوظائف النافعة بنظائر V2 وتغطيتها قبل حذف القديم.
3. **لا نصوص تطويرية** مثل TEST ONLY، candidate_preview، preview، fixture، not_implemented، ملاحظات هندسية أو توجيهات للمطور في تجربة الطفل. يُزال السبب الحقيقي لعدم الجاهزية قبل إزالة تحذير لازم.
4. **بنك المحتوى المعتمد لا يعاد تأليفه اعتباطًا**؛ يتضمن 300 سؤال، 19 درسًا، 12 دعمًا، 30 قبليًا و30 بعديًا، وستة أنواع تفاعل، دون كتابة حرة. افحص النص والتشكيل والخيارات والجواب الخاص وربط الصور والصوت والفيديو لكل بند.
5. **سياسة حذف V1 التاريخي:** وافق المالك على الحذف المبدئي *مع شرط سابق صارم*: جرد ملفات/جداول/علاقات/أعداد الصفوف والأثر، نسخة احتياطية قابلة للاستعادة تم اختبارها، كشف حذف تفصيلي وموافقة نهائية مستقلة قبل أي DELETE/DROP/TRUNCATE/migration مدمّرة.
6. **فرع تنظيف وبيئة معاينة منفصلان** أولًا؛ منع النشر المباشر والإدماج أو تغيير Railway production قبل نجاح CI/M04/M09 وقبول المتصفح وتفويض الإصدار.
7. المهام المجدولة A وB وC متوقفة؛ **ممنوع تشغيلها أو استبدالها بمهمات مجدولة**. العمل تفاعلي فقط، `CONTROL.json` يبقى PAUSED.
8. لا أسرار أو أكواد دخول أو أصوات/صور حقيقية للأطفال في GitHub أو ملفات لقطات الاختبار. بيانات وهمية فقط، اختبار العزل بين حسابين وRBAC.
9. الحل الجذري أولًا، لا ترقيعات/إخفاء بصري فقط، ولا إعلان إغلاق بلا إثبات API + UI + E2E + محتوى + جهاز + نشر مطابق.

## 1) مفتاح الحالة وأدلة التنفيذ

- **CONFIRMED:** مثبت بملف مصدر أو سجل CI. **PARTIAL_FIX:** تعديل موجود لكن لم يقبل بكامل البوابات. **VERIFY:** اختبار واجب دون دليل عطل قطعي. **BLOCKED_EXTERNAL:** يتطلب بيئة/جهاز/وسيط/صلاحية خارج نطاق الفحص.
- حالات القبول: `OPEN`، `FIXED_PENDING_TEST`، `TEST_FAILED`، `ACCEPTED`، `BLOCKED_EXTERNAL`.
- كل بند عند الإغلاق: **SHA + unit/API + Playwright + viewport + نتيجة Network + حالة error/empty/permission + live SHA + رابط/لقطة منقحة**.
- العدد 22 مسارًا مُلزمًا = 15 مشرفًا + 7 طالب؛ الصفحة العامة `/` أيضًا لا تهمل. افحص أي modal/button/hidden route إضافي.

## 2) P0 — فشل المسار الرئيسي والأمان وبوابات الإصدار

| ID | الحالة/الدليل | أصل المشكلة | الحل الجذري المطلوب | معيار الإغلاق |
|---|---|---|---|---|
| HV2-P0-01 | PARTIAL_FIX — `services/api/v2_assessment_runtime.py` | طالب جديد قد يحصل على `migration_review` بسبب جلسة pretest V1 فارغة؛ حل W1 يستكمل shell فقط إن لم يحوِ أي محاولة/دليل ويحتفظ بالتاريخ. | إثبات التسجيل من إنشاء الطالب، فحص الجلسات الاصطناعية والفعلية دون تبديل دليل، استكمال shell الفارغ بحراسة idempotency/lock أو ترحيل آمن بموافقة. | أول دخول يفتح سؤال 1/30، إجابة→2/30 بعد reload؛ لا إعادة محاولات؛ السجل التاريخي الحقيقي لا يُفقد ولا يتجاوز سياسة retake. |
| HV2-P0-02 | FIXED_PENDING_TEST — `services/api/protected.py`، `services/api/v2_assessment_runtime.py` | أهلية فتح الاختبار البعدي كانت تعتمد على `build_journey_summary`/أنشطة V1 رغم انتقال V2 إلى `posttest_ready`. | صلاحية الاختبار البعدي تُشتق لرحلة V2 من `StudentJourney` والإصدار المثبت والقبلي الرسمي V2؛ منع احتساب قبلي V1، حفظ قرار المشرف المصرح فقط. نُفذ مبدئيًا في commit `dcec6ede` مع اختبارات `db0774bf` وتصحيح مصادقة fixture `24691767`. | طالب V2 بلا core V1 يستطيع فتح بعدي رسمي، الطالب غير الجاهز/غير المعتمد يُرفض، POST المكرر لا ينشئ جلسة ثانية؛ CI + E2E + live. |
| HV2-P0-03 | PARTIAL_FIX — `apps/web/src/app/admin/(dashboard)/students/[id]/page.tsx` | زر فتح بعدي V2 كان داخل تبويب «الاختبارات التاريخية V1»؛ غير مرئي حتى فتح الأرشيف، رغم أثره على مسار V2. | نُقل مبدئيًا إلى لوحة ملف V2 مع إعادة جلب readmodel في `87aa0c01`؛ احذف التبويب القديم كله بعد اختبار الاختيار والإتاحة والرفض والتحديث. | الزر الصحيح ظاهر لمشرف في سياق V2 ويطابق حالة eligibility الخادمية، لا يعتمد على تبويب V1، واختبارات E2E تنجح. |
| HV2-P0-04 | VERIFY — `services/api/assessment.py`، `services/api/activity_runtime.py`، `main.py` | مسارات GET/POST القديمة ما زالت مسجلة وقد تنشئ جلسات/تقدم V1 أو تقبل روابط مباشرة حتى لمتعلم يسير في V2. | جرد كل endpoint ومستهلك، منع كتابة V1 في النظام V2 على مستوى الخادم، تحويل routes القديمة بعد إثبات تكافؤ V2، إزالة routers تدريجيًا وليس بشكل أعمى. | اختبارات بدء/إرسال عبر `/assessment/*` و`/activities/*` لحساب V2 لا تكتب أي تقدم قديم، مع نجاح V2 المعتمد وإزالة صفحات V1. |
| HV2-P0-05 | CONFIRMED — Railway Production | خدمات الويب والـAPI مرتبطة مباشرة بفرع العمل V2 و`checkSuites=false`؛ تعديل مباشر قد ينشر دون قبول. | فصل staging/preview بقاعدة بيانات وأصول وSecrets مختلفة؛ إلزام gates قبل أي تغيير Production، rollback وتكافؤ SHA في web/API. | staging مستقل مثبت، CI/M04/M09 على exact SHA، موافقة نشر مستقلة، rollback عملي وsmoke على الإصدار نفسه. |
| HV2-P0-06 | TEST_FAILED — CI/M09 commit `6fdb298b` | Backend وFrontend وSecurity نجحت، لكن **7 اختبارات Playwright أخفقت في CI** وتبعها فشل اختبار المتصفح في M09؛ منها توقعات قديمة لعنوان لوحة المشرف/تبويب V1، وأيضًا تعطل مسار زر فتح البعدي في E2E يجب تحليل trace له. | افتح artifacts/errors واحدًا واحدًا، صنف «اختبار قديم بعد إزالة UI» مقابل «خلل تشغيل»، حدث test assertions للمنتج الجديد دون إسقاط سيناريوهات الأمان/القرارات، أصلح العطل الخادمي إن ثبت، أعد CI/M04/M09. | ثلاث بوابات SUCCESS **على HEAD واحد**؛ صفر P0/P1 Playwright وإثبات صحيح لكل تدفق. مراجع: CI #40460012368، M09 #40460012348، M04 #40460012352 (PASS). |
| HV2-P0-07 | VERIFY — الإنتاج والمتصفح | وجود SUCCESS deployment أو screenshots صناعية لا يثبت عمل كل زر على الرابط المنشور. الوصول المباشر للمتصفح غير متاح في أدوات هذه المحادثة؛ سجل Work القديم يثبت اختبارًا محدودًا فقط. | متصفح Work Cloud Browser بعد تجهيز staging وحسابات اختبار، network/trace، اختبار 22 صفحة وكل حالات البيانات وتصرف الأزرار، ثم إنتاج بعد التفويض. | سجلات E2E وصور خاصة منقحة ونتيجة خادمية؛ real Safari/Android حيث يلزم. |

## 3) P1 — لوحة المشرف: توحيد 15 مسارًا وإزالة التداخل

| ID | مسار/ملف | السبب أو الفجوة | التغيير النهائي المطلوب |
|---|---|---|---|
| HV2-ADM-01 | `/admin/login` | VERIFY جلسة/صلاحية وفشل دخول/انتهاء وصلاحية هاتف | Login/logout/expiry/invalid/role-guard، لا بيانات حساسة، RTL الهاتف. |
| HV2-ADM-02 | `/admin`، `v2_student_readmodel.py` | لوحة V2 مصدرها `/v2/student/admin/overview` مبدئيًا، بعد عرض V1 0/10 ورموز سابقًا؛ VERIFY اكتمال الأرقام ومراجعات/دعم | مصدر V2 واحد بلا access_code أو صفر مضلل عند الخطأ، فلاتر/قراءات/اختبارات/إشعارات وتقدم حقيقي. |
| HV2-ADM-03 | `/admin/account` | مجرد تحويل إلى `/admin/settings`، مساران لنفس الغرض | اعتماد وجهة واحدة ومراجعة الروابط وتبسيط التنقل مع الحفاظ على إدارة الحساب/كلمة المرور. |
| HV2-ADM-04 | `/admin/students` | مصدر V2 الحالي قائم؛ وصف الصفحة ما زال يشير لأرشيف V1، واختبارات البحث والفرز والعدد والخصوصية ناقصة | البحث/تصفية/حالة طالب/تقدم 19 درسًا، لا رمز مكشوف ولا آثار V1؛ حذف النصوص القديمة. |
| HV2-ADM-05 | `/admin/students/new` | إنشاء الطالب يستخدم `/researcher/students` المشترك مع النماذج القديمة | عدم إنشاء shell V1 غير لازم، منع double-submit، حساب اصطناعي → بدء قبلي V2، رمز جديد لا يعرض إلا في خطوة التسليم المصرح بها. |
| HV2-ADM-06 | `/admin/students/[id]` (631+ سطر) | CONFIRMED تبويبات overview/journey/tests/recordings/adaptation/history تخلط بيانات وأرقام V1؛ access-code field قد يصل للـfrontend؛ زر البعدي رُحّل مبدئيًا | Student360 V2 واحد: الحساب والصلاحيات، قبلي/بعدي مع اعتماد رسمي، دروس 19 ودعم، انتظار مراجعة، آخر تسجيل محفوظ/مراجع، مكافآت V2؛ لا history V1 أو override قديم أو reward V1. |
| HV2-ADM-07 | `/admin/v2-assessments` | ظاهر ويقرأ queues V2؛ VERIFY قرار مراجعة صوت، placement، retake، report واحتمال 500 سابق | happy/error/409/403/claim race/duplicate، 30/30، سبب المراجعة، تسجيلات خاصة، لا تداخل مع V1. |
| HV2-ADM-08 | `/admin/v2-lesson-review` | queue V2؛ VERIFY إقرار آخر صوت، تقييم، إعادة موجّهة | حالات pending/approved/rejected/claimed/stale/redo، مقاومة التكرار وحماية صلاحيات المشرف. |
| HV2-ADM-09 | `/admin/v2-reviewed-recordings` | موجود ولكن الاسم «أرشيف الصوت» لا يعادل أرشيف V1، يلزم تأكيد مصدره V2 فقط | قائمة مقيّمة فقط/آخر صوت محفوظ حسب القرار، مشغل مصادق، عدم عرض storage key، تحقق 403 عبر حسابين. |
| HV2-ADM-10 | `/admin/audio-review` | CONFIRMED واجهة V1 من 420 سطرًا، وروابط واردة من الإشعارات/ملف الطالب | استبدال المراجع بمراجعة V2؛ إغلاق/إزالة route بعد إثبات عدم استخدامه؛ لا أرشيف ظاهر. |
| HV2-ADM-11 | `/admin/content-preview` و`LegacyContentPreview.tsx` | إزالة زر أرشيف بنك V1 من الصفحة، لكن المكوّن القديم 1040 سطر ما زال في المستودع | تأكيد zero imports وإزالة المكوّن/ملفات CSS غير المستخدمة والاختبارات التنافسية، إبقاء مستعرض 300 سؤال بالترتيب وإجابات المشرف فقط. |
| HV2-ADM-12 | `/admin/v2-media` | معرض يعمل كبنية، لكن يوجد generic/shared TEST_ONLY وملفات غير مكتملة | جرد 89 asset_id، اعتماد/ربط الملفات الحقيقية، تشغيل 3 أنواع، missing/error/status واضحة للمشرف فقط، RTL بلا overflow؛ لا صور أو صوت افتراضي على أنه معتمد. |
| HV2-ADM-13 | `/admin/reports`، `services/api/reports.py` | CONFIRMED عنوان V1 واتصال `/api/researcher/reports/summary` وتصدير PDF/Excel قديم | تقارير V2 فعلية من تقييمات رسمية ورحلة مثبتة، قبلي/بعدي/تحسن/دعم/مستويات، PDF/Excel، منهجية ودقة القيم وحماية الصادرات. |
| HV2-ADM-14 | `/admin/skill-reports`، `services/api/skill_reports.py` | CONFIRMED يستخدم دليل الاستجابات V1 بدل SkillEvidence V2 | دليل مهارات V2 مع review official/retry/source version، تصدير Excel، عدم اختلاق «إتقان» أو نتائج نطق آلية. |
| HV2-ADM-15 | `/admin/settings` | وظائف الحساب والمشرفين موجودة على endpoints مشتركة؛ VERIFY RBAC والأدوار والأمان | CRUD وفق الصلاحيات الفعلية/تحديث الاسم/كلمة السر/المشرفين، validation وaudit وعدم كشف secrets. |
| HV2-ADM-16 | `AdminNotifications.tsx`، `admin_notifications.py` | CONFIRMED مصدر `/researcher/notifications` وروابط `/admin/audio-review` | إشعارات أحداث V2: مراجعة تقييم، مراجعة درس، صوت، إكمال/تنبيه؛ marked read + count + safe internal href، دون تدفقات V1. |
| HV2-ADM-17 | `layout.tsx` و`ReinforcementReviewPanel.tsx` | أزيل رابط الأرشيف والمكوّن القديم من shell، لكن الملف والخدمات لا تزال موجودة | تتبع كل المستهلكين وإزالة الخدمة/المكوّن والتبعيات غير اللازمة بعد passing tests، تنقل V2 واحد للهاتف والكمبيوتر. |

## 4) P1 — الطالب: 7 صفحات وكل مسار تعليمي

| ID | مسار/ملف | المشكلة أو فحص الإغلاق |
|---|---|---|
| HV2-STU-01 | `/student/login` | رمز صحيح/خاطئ، rate-limit، جلسة منتهية، خروج ثم دخول طالب ثان، عدم استمرار الهوية القديمة. |
| HV2-STU-02 | `/student`، `V2StudentDashboard.tsx` | GET V2 فقط موجود، href type guard أُصلح سابقًا؛ لكن `test_only` ورسالة «معاينة TEST ONLY» و`rewards.state=not_implemented_v2`، حالة migration_review للبيانات القديمة. تجربة طفل نظيفة بخطوة واحدة وتشجيع صحيح وحالات pending/error دون مفاهيم تطوير. |
| HV2-STU-03 | `/student/assessment-v2/[sessionId]` | القبلي والبعدي 30/30: الإجابات والمراجعة الصوتية، 401/403/404/409/503، الانتظار، save/resume، repeated POST وACK lost، لا تسريب private_answer. |
| HV2-STU-04 | `/student/learning-v2` | CONFIRMED «معاينة رحلة التعلم V2»/TEST ONLY، نصوص مرتبطة بالترشيح؛ 19 درساُ، locked/current/completed/skipped، دعم داخل نفس المسار وليس تجربة فرعية مرهقة. |
| HV2-STU-05 | `/student/learning-v2/[sessionId]` | عرض تمهيد وهدف وفيديو وصوت وصور + تدريب وتلميح + اختبار مستقل + دعم + تسجيل آخر صوت؛ autoplay/retry/ACK/reload/200% zoom/keyboard/touch؛ التحقق من أصل وسائط حقيقي. |
| HV2-STU-06 | `/student/activity/[id]` | CONFIRMED صفحة V1 تشغيلية (556 سطرًا) تستعمل `/activities/session`؛ حظر الدخول من مسار V2 وحذف page/layout/CSS غير المستخدمة بعد اختبار غياب الروابط. |
| HV2-STU-07 | `/student/session/[id]` | CONFIRMED صفحة اختبار V1 تشغيلية (518 سطرًا) تستعمل `/assessment/session`؛ نفس المعالجة مع إنفاذ Server guard وليس redirect تجميلي فقط. |

**فحوص جامعة للطالب:** 360/390/430/768/1440، RTL وfocus/reduced-motion/contrast، شبكة بطيئة وانقطاع، عدم إخفاء إجابة صحيحة/حكم رسمي، لا استخدام الكتابة الحرة، لا تكرار الصوت أو الأسئلة أو المكافآت. اختبر دخول N جديد، L قديم، P بدأ بندًا، R ينتظر التسكين/المراجعة، S مستوى 1/2/3/دعم، U غير مفوض وعابر الحسابات.

## 5) P1 — البنك المعتمد والوسائط وإصدار المحتوى

| ID | مثبت بالمصدر/العدد | المطلوب |
|---|---|---|
| HV2-MED-01 | `services/api/v2_content/compiler.py`: 300 سؤال = guided 119 + independent 75 + support 46 + pre 30 + post 30. الأنواع: choose_one 107، listen_choose_one 52، sequence 57، build_word 18، choose_image 4، read_aloud 62؛ **write_text صفر**. | تدقيق جميع IDs/ترتيب الأقسام/الخيارات والتشكيل والأهداف والتمهيد ودليل القراءة والجواب الخاص، عدم تسريب مفاتيح الطالب، ربط كل بند بالوسائط ومصدره المثبت. لا إعادة تأليف معتمد دون سبب. |
| HV2-MED-02 | 89 أصلًا: **19 فيديو `missing_new`، 14 صوتًا `missing_new`، 33 صوتًا مختارًا من V1 pending owner review، 23 صورة من V1 pending owner review** في ملفات authoring الأربعة. | جرد الأصول الجديدة المنتجة خارج repo ومطابقتها بـ asset_id؛ تحقق الترخيص/النطق والتشكيل/حقوق المحتوى/جودة الصوت؛ تحديث manifest والاعتماد برقم إصدار لا بعبارة جاهز فقط. |
| HV2-MED-03 | `v2_content/media.py`، `readiness.py`، `v2_lesson_runtime.py`: fallback أصوات/صور V1 وفيديو `shared_test_only_video`، لا تُحسب publishable. | فصل fallback الاختبار عن إنتاج V2، عدم حذف ملفات V1 المستخدمة حتى استبدالها، لا إخفاء warning قبل `publishable` وQA الحقيقيين. |
| HV2-MED-04 | `services/api/v2_content/compiler.py` يقرأ ملفات `docs/v2/content-bank/*_DRAFT.json` وحالات metadata draft/not_published رغم اعتماد المستخدم للبنك. | التمييز بين **اعتماد المحتوى التربوي من المالك** و**حالة نشر/ربط الملفات داخل manifest**؛ تثبيت revision/checksum/migration إلى release approved بعد اكتمال الدليل دون تغيير الأسئلة المعتمدة. |
| HV2-MED-05 | `services/api/v2_adaptation_runtime.py:_complete_lesson` يجلب `get_release()['lessons']` الحالي، بينما رحلة الطالب تحمل `content_release_id`. | اختبر تغيّر release أثناء رحلة فعلية؛ اجعل ترتيب الانتقال/الدرس التالي من snapshot pinned إن ثبت الخلل، لا تخلط إصدارين أو تقفز درسًا. |
| HV2-MED-06 | `v2_lesson_runtime.py`: بعض مسارات catalog/start تعتمد `student.current_level` عند غياب journey وتعرض preview. | حافظ على تسكين V2 الرسمي فقط؛ لا يدخل الطالب مراحل خطأ بسبب legacy current_level؛ اختبر L1/L2/L3 وتخطيات التسكين. |
| HV2-MED-07 | الأصول التعليمية غير نفس تسجيلات الأطفال الخاصة؛ `v2_lesson_runtime` يحوي fixture endpoints و`v2_content_api` candidate endpoints. | إذن RBAC لكل نوع، لا نشر fixture في production، player H.264/AAC/VTT على Safari/Android، أمن audio upload وprivate S3 عبر حسابين، لا تصدير روابط أو storage keys. |

## 6) P1 — المكافآت والسياسة التربوية والعمليات المتبقية

- **HV2-RWD-01:** `services/api/v2_student_readmodel.py` يعيد `rewards: {state: not_implemented_v2}`؛ واجهة الطالب لا تعرض نجومًا صحيحة. اعتماد تصميم **نجوم مشاركة/إنجاز حدثية** لا درجة امتحان، وسجل Ledger رسمي V2 ب`event_key` وحيد، 1–3 نجوم لخطوات مثبتة فقط، وشارات إنهاء مستوى فعلي؛ لا نقاط للمحاولات المكررة/السرعة/التسكين التلقائي أو عقوبة عند الدعم. حسم الأرقام والتسمية في `docs/v2/DECISIONS_AR.md` وتفعيل source-of-truth واختبارات idempotency وretake/retry.
- **HV2-RWD-02:** لا خلط لجدول `reward_events` القديم أو عناصر `CanonicalRewardBadge` القديمة مع مكافآت V2 قبل بناء ledger وmapping جديد.
- **HV2-ADM-RPT:** نتائج البعدي/القبلي والتقوية والتقارير والإشعارات يجب أن تعتمد الحالات الرسمية بعد مراجعة الصوت، لا حالات pending أو درجة من تجربة V1.
- **HV2-UX-01:** توحيد تسمية المستويات (الحروف وأصواتها؛ الحركات والمقاطع؛ قراءة الكلمات؛ المدود والكلمات الأطول؛ قراءة الجمل وفهمها كـمحاور مهارية) مع المستويات الثلاثة المعتمدة في رحلة الطالب، وعدم اختزال أهداف المهارات إلى Labels غير مفهومة.
- **HV2-OPS-01:** الحمل والأداء: pagination/filter، عدم `N+1` في cohort/readmodel، مؤشرات query زمنية، استجابات stale وclient navigation بين طالب A→B→A، double-submit، 503 وretry، بناء ومراقبة logs وإعادة تشغيل صحيحة بعد تحديث الخدمات.

## 7) جرد المكونات والـAPI والبيانات المرشحة للإزالة

### 7.1 مرشح إزالته من الواجهة بعد إثبات عدم وجود مستهلك
- `apps/web/src/app/admin/(dashboard)/content-preview/LegacyContentPreview.tsx` (حوالي 1040 سطر)، وCSS/tests القديمة إن لم تُعد مطلوبة.
- `apps/web/src/components/ReinforcementReviewPanel.tsx` وما يتبعه بعد التأكد من غياب استيرادات أخرى. الاستيراد العام رُفع سابقًا.
- `apps/web/src/app/admin/(dashboard)/audio-review/page.tsx` (420 سطرًا) **بعد** استبدال كل الإحالات والمراجعات عبر V2.
- `apps/web/src/app/student/activity/[id]/page.tsx` (556 سطرًا)، `student/session/[id]/page.tsx` (518 سطرًا)، والتبعيات **بعد** ضمان API route guard وغياب استخدام المسارات.
- تبويبات V1 وأرقام rewards/adaptation/history داخل `students/[id]/page.tsx` تُزال عبر إعادة بناء Student360، ولا تُحذف الصفحة كلها.
- نسخ تقارير V1 وصفحاتها وشاراتها ونصوص TEST ONLY: أزل النسخة المنافسة **بعد** اكتمال بديل V2؛ لا تجعل تقريرًا غير موجود بدل تقرير قديم.
- اختبارات E2E لواجهة V1 القديمة (مثال `vertical-slice.spec.ts` وبعض `admin-responsive.spec.ts`): **أعد كتابة اختبار رحلة V2**، لا تحذف اختبارات RBAC/IDOR/score/private media دون بديل مكافئ.
- ملفات الصور/الأصوات القديمة لا تُحذف إذا ما زالت مرجعًا في manifest V2، حتى بعد إعادة تسميتها أو نقلها؛ اعمل hash/import/update/test أولًا.

### 7.2 API/router مرشح للعزل التدريجي لا الحذف الفوري
- `services/api/main.py`: assess/activities/assessment_view/learning_experience/journey/adaptation/adaptation_runtime/reinforcement_review/review/reports/skill_reports/admin_notifications/reward_catalog القديم.
- لا تحذف `protected.py` أو `auth` أو `Student` أو `AssessmentSession` لأنها **مشتركة** مع V2 حاليًا. فك تداخل models والوظائف تدريجيًا مع migration غير مدمرة.
- `recordings.py` و`audio_submissions` قد يخدمان الصوت الحالي؛ استخرج dependency graph قبل حذف أي handler أو column.
- `ContentRelease` و`PrivateContentBankSnapshot` ضروريان لتثبيت V2؛ لا تعتبر كلمتي legacy في docstring سببًا للحذف.

### 7.3 DB / SQL: جرد مبدئي **ليس إذنًا للحذف**
- **جداول مرشحة للفحص:** `content_items`، `content_steps`، `content_options`، `content_asset_links`، `scoring_policies`، `scoring_rules`، `attempts`، `attempt_responses`، `activity_step_responses`، `adaptation_decisions` (V1)، `reward_events` (V1)، `reinforcement_cycles`، `researcher_notifications`، `speech_analysis_jobs` و`speech_analyses`؛ **لا تجزم بحذفها** قبل تتبع FK والمستهلكين الحاليين وسلامة السجلات.
- **جداول مشتركة/حرجة V2 لا تمسّ مباشرة:** `users`، `students`، `auth_session_states`، `audit_logs`، `content_releases`، `assessment_sessions`، `assessment_retake_authorizations`، `audio_submissions`، `audio_reviews`، `operation_idempotency`، جميع جداول `student_journeys`، `lesson_sessions`، `lesson_progress_events`، `lesson_question_responses`، `support_assignments`، `skill_evidence`، `assessment_question_responses`، `placement_decisions_v2`، `private_content_bank_snapshots` وغيرها من V2.
- استخراج `information_schema` و`pg_constraint` وFK وviews/triggers والـrow counts وتوزيع الإصدار على السجلات وstorage references والبيانات المستخدمة في تقارير/مقارنات V2. **لم يُنفذ جرد SQL الحقيقي إلى الآن**.
- النسخ الاحتياطية الإنتاجية: pg_dump مضبوط ومتوافق + نسخة object storage ذات حقوق وصول مضبوطة + checksum + تجربة Restore في قاعدة منفصلة + RPO/RTO وخطة rollback. **لم تنشأ/تختبر بعد**.
- ملف موافقة مستقل قبل أي حذف: جدول `file/table/row selector | count | FK | consumer | V2 dependency | backup id | restore test | risk | approved by owner`. لا حذف بعد توقيع مجرد «نظف V1» العام.

## 8) سجل العمل المنفذ فعلًا على فرع التنظيف — لا يساوي قبولًا

1. `ed4cc648`: إزالة واجهة أرشيف بنك V1 من `content-preview/page.tsx`.
2. `a4933ea2`: إزالة أرشيف V1 من sidebar والمكوّن القديم المضاف عموميًا.
3. `a86bd9b5`: إنشاء هذا الجرد الأولي، الذي توسع الآن إلى سجل كامل.
4. `dcec6ede`: نقل قرار أهلية فتح البعدي إلى V2، مع الاعتماد المرحلي على حقول التصريح المشتركة دون أي migration مدمرة.
5. `db0774bf` و`24691767`: اختبارات أهلية ما بعدي V2 وتعديل جلسة fixture المزدوجة بعد فشل Backend الأول؛ سجل سابق 1069 PASS + 1 FAIL، ثم أحدث Backend PASS على SHA `6fdb298b`.
6. `f6418fd8`، `f824c1ad`، `1af691d2`: تشغيل CI/M04/M09 على `cleanup/*` دون تغيير نشر production.
7. `1efb3f53`، `957833a1`: تعديل E2E ووحدة بنك V2 لإزالة افتراض زر أرشيف البنك.
8. `87aa0c01`، `6fdb298b`: نقل زر البعدي إلى سياق ملف V2 وإضافة تغطية E2E.

**آخر دليل بوابات متحقق لSHA `6fdb298b` قبل تحديث الملف:**
- [M04 PASS #40460012352](https://github.com/7eaur/himma-/actions/runs/40460012352)
- [CI FAIL #40460012368](https://github.com/7eaur/himma-/actions/runs/40460012368): frontend PASS، security PASS، backend PASS، **integration FAIL (7 failed Playwright tests)**.
- [M09 FAIL #40460012348](https://github.com/7eaur/himma-/actions/runs/40460012348): product Backend PASS، browser product regression FAIL. راجع traceback/artifact قبل إرجاعه إلى «مجرد اختبارات قديمة».
- **ليس هناك إغلاق مرحلي** ولا نجاح لـ E2E الكامل ولا تحقق live؛ أي commits جديدة لهذا المستند تعيد شرط exact-SHA gates عند الإقرار النهائي.

## 9) خطة التنفيذ والاختبار بترتيب صارم

| المرحلة | العمل | بوابة الخروج — لا انتقال بلاها |
|---|---|---|
| W0 | قراءة handoff/matrix والفرع الحقيقي وRailway وCI وdiff ومصادر الحقيقة وسياسة V1؛ بناء staging مستقل وآمن | اختلاف SHA معروف، وصول التجربة محدد، تفعيل CI لفرع التنظيف، لا تداخل مع إنتاج |
| W1 | بداية الطالب الجديد/الجلسة القديمة الفارغة/القبلي/التسكين/صلاحية البعدي + حارس الروابط + رفض endpoints القديمة لمتعلم V2 | Backend/Frontend/CI/M04/M09 + E2E حسابات N/L/P/R/S/U، ولا خلط V1/V2 |
| W2 | لوحة المشرف 15 وجهة، Student360، الحسابات والرموز والخصوصية وRBAC ومراجعة الدروس/التسجيلات، إزالة archive UI | كل زر وحالة وخطأ وفلاتر ومعاينة على 390/768/1440، 403 IDOR؛ لا مؤشر من V1 |
| W3 | البنك 300 + 6 أنواع + 19 درسًا + 12 دعمًا + جرد 89 وسيطًا، تقرير V2 وملخص المهارات والتصدير والإشعارات | تصحيح كل 300 بند/تصفح الأصناف/preview audio/image/video، التقارير الحقيقية والتصدير، لا صفحات V1 |
| W4 | القرار النهائي لنجوم/شارات V2، ledger idempotent، واجهات طفل لا تشجع على التخمين أو المقارنة | grant once وإعادة المحاولة والتسكين والتقدم والمراجعة بلا تضخيم نجوم أو نقاط |
| W5 | تجربة الطالب العربية النهائية RTL، درس ثم تدريب واختبار ودعم وصوت، حالات فقد الشبكة ومراجعة، حذف النصوص التطويرية بعد توافر الأصل | اختبارات جميع حالات الرحلة، مستوى1/2/3، touch/keyboard/zoom والشاشات الست |
| W6 | فحص المتصفح المصادق للـ22 route + /، كل الحالات والأزرار + 300 سؤال و19 درسًا و12 دعمًا | P09 FUNCTIONAL READY WITH TEST MEDIA فقط عند zero P0/P1، أدلة screenshot/trace/API/SHA |
| W7 | ربط 19 فيديو و14 صوتًا جديدًا، موافقات 33 صوتًا +23 صورة ومراجعة نطق/تشكيل، S3 private cross-user، real-device | P10 MEDIA APPROVED بعد انتهاء QA وسلامة الحقوق والتشغيل وأصوات الطلاب |
| W8 | توحيد codebase/routers/DB، جرد نهائي، backup/restore، قرار الحذف النهائي، تنظيف branches/tests/scripts، release-candidate وتغيير النشر بموافقة | لا إصدار إلا بتوقيع المالك وبوابات SHA + rollback + smoke؛ لا DELETE إلى حين موافقة مستقلة |

**مهم:** تقارب العمل أحيانًا يبرر تجميع إصلاحات صغيرة قبل اختبار شامل، لكن **لا يجوز تخطي بوابة مرحلة أو تمييعها** بسبب طول E2E. وثق فرق accepted/test_pending/rework.

## 10) قالب واجب لكل سطر ملف/مسار قبل إزالته

`id | original path | feature owner V1/V2 | frontend imports | runtime API consumers | DB/FK | content/asset refs | replacement in V2 | regression tests | staging result | data backup/restore | DELETE allowed? | owner final approval`

لا تحذف ملفًا لمجرد أنه «يبدو قديمًا». لا تعلِن الجاهزية بمجرد إخفاء زر. لا تحذف DB أو ملفات الصوت ما دامت أجزاء من V2 تستعملها.

## 11) المراجع/المهام المفتوحة

- [Issue #9 — بوابة البعدي V2/V1](https://github.com/7eaur/himma-/issues/9)
- [Issue #10 — مسارات واجهات وAPI V1 القديمة](https://github.com/7eaur/himma-/issues/10)
- [Issue #11 — التقارير والإشعارات V1](https://github.com/7eaur/himma-/issues/11)
- [Issue #12 — auto deploy دون CI gating](https://github.com/7eaur/himma-/issues/12)
- [Issue #13 — تنظيف المنتج وإزالة TEST ONLY/الأرشيف](https://github.com/7eaur/himma-/issues/13)
- [ملف الاستلام](WORK_HANDOFF_20261027_AR.md)، [مصفوفة الاختبارات](WORK_BROWSER_ACCEPTANCE_MATRIX_20261027_AR.md).
- تقرير إعادة الفحص العربي المحلي `HIMMA_V2_COMPREHENSIVE_REAUDIT_20261027_AR.md` وُلد للمحادثة؛ **هذه الوثيقة في المستودع هي السجل الموحد القابل للمتابعة**.

## 12) القيود الحالية التي يجب أن تظهر في كل تقرير حالة

1. لا يوجد بعد إثبات اجتياز E2E للفرع؛ آخر CI/M09 فشلتا.
2. لا توجد بيئة Railway staging معزولة منشأة ومتحقق منها في هذه الجولة.
3. لم يُنفذ اختبار متصفح Work مباشر في هذه المحادثة على الرابط المنشور؛ لا تخلط سجل Work سابقًا بفحص حاضر.
4. لم يُنفذ جرد SQL production أو pg_dump/restore معتمد؛ لا عمليات حذف بيانات.
5. لا إثبات إنتاجي لتشغيل كل 89 أصلًا أو اعتماد 19 فيديو و14 صوتًا جديدًا.
6. لم تُنفذ مكافآت V2، ولم تكتمل تقارير/مهارات/إشعارات V2 أو إزالة routers القديمة.
7. A/B/C متوقفة، ولا نشر ولا دمج main ولا تعديل إنتاجي.

**النهاية المطلوبة:** كود V2 واحد قابل للاختبار والنشر، لوحة مشرف وطفل جاهزتان دون نصوص هندسية، مصادر الحقيقة مثبتة، بنك كامل ووسائط صحيحة، تقرير حذف معتمد ونسخة احتياطية مستعادة، ثم إصدار رسمي بموافقة المالك.
