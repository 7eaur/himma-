# هِمّة V2 — خطة التنظيف التفصيلية: المرحلة 01 (المسارات والمستهلكون)

**التاريخ:** 2026-11-02 — Asia/Aden  
**المستودع:** `7eaur/himma-`  
**فرع التعديل المباشر:** `v2/01-learning-foundation-20261007`  
**حالة المرحلة:** تنفيذ إصلاح أول مثبت بالمصدر، وبوابات GitHub قيد التحقق؛ الجرد الجزئي لا يساوي إغلاق المرحلة أو قبول إصدار التسليم.  
**تنسيق الجرد:** `CONFIRMED_ACTIVE` مستخدم، `COMPATIBILITY` توافق تاريخي، `CANDIDATE` مرشح لتوحيد/حذف بعد فحص المستهلكين، `FIXED_SOURCE_PENDING_GATES` تعديل مرفوع يحتاج نجاح الاختبارات.

## المبدأ
لا تعتمد على اسم الملف أو قدمه للحذف. لكل هدف: (1) موضعه، (2) المستهلكين، (3) أثره على البيانات والصلاحيات، (4) القرار، (5) الاختبار، (6) إثبات SHA النشر. لا حذف لترحيل تاريخي مطبق أو صوت معتمد أو مسار مستخدم من الطالب دون استبدال آمن.

## 01-A — مسارات الطالب في Web

| المسار | الحكم | سبب القرار / العمل التالي |
|---|---|---|
| `/student` | CONFIRMED_ACTIVE | `apps/web/src/app/student/page.tsx` يستهلك `/api/v2/student/home`؛ لوحة الطالب V2 |
| `/student/login` | CONFIRMED_ACTIVE | تسجيل الدخول الحالي |
| `/student/assessment-v2/[sessionId]` | CONFIRMED_ACTIVE | يستهلك جلسات V2 |
| `/student/learning-v2` | CONFIRMED_ACTIVE | خريطة V2 تستدعي `/api/v2/lessons/catalog` |
| `/student/learning-v2/[sessionId]` | CONFIRMED_ACTIVE | درس V2 والتفاعل، تسجيل الأحداث |
| `/student/retry/[taskId]` | CONFIRMED_ACTIVE | إعادة تسجيل V2 |
| `/student/activity/[id]` | COMPATIBILITY | صفحة Redirect إلى `/student` فقط؛ لا تعلم V1 عليها، لكن افحص الروابط الخارجية والاختبارات قبل حذف route |
| `/student/session/[id]` | COMPATIBILITY | Redirect إلى `/student` فقط؛ لا تطابق session IDs القديمة مع V2 |
| `/student/activity/layout.tsx` وما تحته، `/student/session/[id]/layout.tsx` | CANDIDATE | أغلفة بسيطة لا تتضمن وظيفة واضحة مستقلة؛ يمكن حذفها بعد اتخاذ قرار مصير مسارات redirect |

**ممنوع:** ربط معرّف V1 بجلسة V2 بالتخمين أو قطع روابط الاستئناف القديمة دون مسار إرجاع آمن.

## 01-B — مسارات المشرف في Web

| المسار | الحكم | السبب |
|---|---|---|
| `/admin`, `/admin/students`, `/admin/students/new`, `/admin/students/[id]` | CONFIRMED_ACTIVE | بيانات الطالب والمشرف V2 من `/api/v2/student/admin/*` |
| `/admin/content-preview` | CONFIRMED_ACTIVE | بنك V2: `/api/v2/content/admin/bank` |
| `/admin/v2-media`, `/admin/reports`, `/admin/skill-reports` | CONFIRMED_ACTIVE | ملفات الوسائط والتقارير V2 |
| `/admin/settings` | CONFIRMED_ACTIVE | ما زالت تستهلك `/api/researcher/account` و`/api/researcher/supervisors` من API المشترك؛ **لا تحذف هذه الـEndpoints** |
| `/admin/v2-review-center` | CONFIRMED_ACTIVE | مركز واحد يحتوي تبويبات قراءات الاختبارات والدروس والسجل المقيّم |
| `/admin/v2-assessments`, `/admin/v2-lesson-review`, `/admin/v2-reviewed-recordings` | CANDIDATE | صفحات منفصلة تركب المكونات نفسها الموجودة بالمركز الموحد؛ ضع Redirect دائمًا مع tab مناسب بعد تحديث الاختبارات والروابط وفحص deep links |
| `/admin/audio-review`, `/admin/account` | COMPATIBILITY | تحول إلى مركز المراجعات والإعدادات؛ راجع الاحتفاظ بمعاملات query مثل student_id في الروابط القديمة |
| `/admin/login` | CONFIRMED_ACTIVE | تسجيل الدخول |

**أدلة مستهلكين تمنع الحذف الفوري:** `apps/web/tests/e2e/admin-responsive.spec.ts` يستخدم الصفحات المنفصلة، و`audio-review-filtered-context.spec.ts` يبدأ من الرابط القديم، و`p03-screenshots.spec.ts` يصور صفحة مراجعة مستقلة. يجب تحويلها إلى اختبار المركز الموحد قبل إزالة صفحات التوافق نهائيًا.

## 01-C — API: تداخل المسارات V1/V2

- `services/api/main.py` ما زال يسجل router سابقًا مثل `assessment`, `activity_runtime`, `adaptation`, `review`, `recordings`, بجانب routers V2.
- `/assessment/start`: وُجد **تعريفان POST للمسار نفسه**؛ `assessment_retake.start_assessment_with_retake_policy` يُسجَّل أولًا، و`assessment.start_assessment` كان محجوبًا بالتسجيل اللاحق.
- **إصلاح منفذ:** حذف الدالة/الديكوريتر القديم المحجوب من `services/api/assessment.py` (commit `3438799ea77b6a1e10fe2d2beebf2c1040fb268f`)، والإبقاء على المالك المفرد `assessment_retake`. أضيف اختبار مستوى التطبيق لا يكتفي باختبار routers الفردية في `services/api/test_assessment_route_ownership.py` (commit `c9b73fca9026a0084fbc496ccfdfa7e5c26bfe69`). **الاختبارات لم تتأكد بعد على SHA نهائي**.
- **لا يجوز حذف كل `assessment*` أو `recordings.py` في هذه المرحلة:** الاختبارات `test_v1_student_guard.py` توثق أن طلاب V2 يمنعون من الكتابة إلى المسارات القديمة، بينما طالب بلا رحلة V2 كان ما يزال يستطيع بدء القبلي القديم. حذف الحارس `v1_student_guard.py` دون تعطيل أو ترحيل المسارات قد يعيد خطأ خلط بيانات الطالب.
- واجهة المشرف لا تزال تحتاج `/researcher/account`, `/researcher/supervisors` ضمن `protected.py`؛ هذه مسارات مشتركة نشطة وليست بقايا مهجورة.
- صفحتا الطالب القديمتان هما Redirect فقط، لكن API V1 **لم يتحول بالكامل إلى Redirect أو 410**؛ هذه أهم فجوة باقية قبل وصف المنتج بأنه V2-only.
- `services/api/activities.py` و`activities_v4.py` غير مسجلين كـrouters بحسب `test_activity_route_ownership.py`، لكنهما قد يحويان دوال خدمة يستخدمها `activity_runtime.py`. لا تحذفهما لمجرد عدم وجود `router`.

## 01-D — وسائط تحمل تسمية "test-fixtures" على مسارات V2

- `services/api/v2_lesson_runtime.py` ما زال يعرّف `/v2/lessons/test-fixtures/{video|audio|image}`؛ تستعمل أصولًا من allowlist ومقاطع فيديو مؤقتة.
- الوصول يتطلب `_require_preview_student`، والذي يعيد 503 عندما تكون البيئة `ENV=production` أو `trial` بدون `HIMMA_TRIAL_V2_PREVIEW=true`. يجب التحقق من إعدادات Railway وتشغيل الدروس الفعلي **قبل أي ادعاء أنها معطلة أو تعمل في الإنتاج**.
- لا يُحذف هذا المسار قبل تأكيد تغيير روابط الوسائط المعتمدة في V2 إلى مصدر `/sessions/{session_id}/media/{asset_id}` أو مسار إنتاجي ثابت موثق، والتأكد من سلامة الصوت/الفيديو وعدم فقد التقدم.

## 01-E — قائمة أعمال المرحلة قبل إغلاقها

| رقم | مهمة تنفيذية محددة | الحالة |
|---|---|---|
| R13-01 | جرد مسارات Web V2 مقابل Redirect التاريخي | فحص مصدر أولي مكتمل |
| R13-02 | جرد Routers API ووصول V1 الحقيقي | تم اكتشاف التداخل؛ جرد المستهلكين/الاختبارات غير مكتمل |
| R13-03 | إزالة تكرار `POST /assessment/start` وإنشاء حارس انحدار | FIXED_SOURCE_PENDING_GATES |
| R13-04 | فصل واجهات مراجعة الصوت المنفصلة إلى Redirect نحو المركز دون كسر deep links | مرشح لمراجعة المستهلكين وتحديث الاختبارات |
| R13-05 | التحقق من جميع عملاء V1 القديمين وحصر أي بيانات/حسابات تاريخية | غير مكتمل؛ **لا تخترع نتيجة من GitHub فقط** |
| R13-06 | تصميم عقد V2-only لإغلاق V1 (410/404) مع حفظ بيانات الطلاب والصوت والترحيلات المطلوبة | يتطلب اختبار قاعدة بيانات وبيئة تشغيل |
| R13-07 | فحص استهلاك `review.py`, `recordings.py`, `researcher_journey.py`, `assessment_view.py`, `learning_experience.py` | لم يُحسم؛ لا حذف |
| R13-08 | مراجعة مسارات الوسائط `test-fixtures` وحالات ENV/HTTP وتشغيل إنتاجي | يتطلب تحقق Railway وإعدادات المصدر |
| R13-09 | نجاح Backend/Frontend/Security/Integration/M04/M09 + إعادة فحص المسارات على SHA نهائي | قيد الانتظار |
| R13-10 | نشر التغييرات والتحقق من الفصل والربط وحالات الطالب والمشرف الحية | لم يُنفذ |

## تقسيم بقية المستودع (بعد إغلاق جزء المسارات)

1. **المرحلة 02 Backend:** إنشاء جرد import/dependency لكل modules والسيرفر والخدمات والـjobs والـseeds، وإزالة الكود الميت فقط بعد اختبارات وحدة وتكامل.
2. **المرحلة 03 Web:** المكونات المكررة والـCSS والـempty/error/loading states، الروابط والتجاوب.
3. **المرحلة 04 DB:** جداول V1 والحراسة، Alembic migrations، علاقات الطلاب والتسجيلات والدرجات والوسائط؛ دون drop إنتاجي بغير خطة استرداد.
4. **المرحلة 05 Assets:** source-of-truth للبنك والصوت والصورة والفيديو، وحصر الملفات المعتمدة داخل مجلدات V1 قبل إعادة تنظيم المسارات.
5. **المرحلة 06 Tooling:** الاعتماديات وDocker وCI والاختبارات وسكربتات seed/repair والاختبارات التاريخية.
6. **المرحلة 07 Repo:** وثائق التشغيل والأرشيف والفروع والتبعيات الخارجية وتغيير default والحذف الآمن.
7. **المرحلة 08 Final acceptance:** فحص end-to-end للطلاب والمشرف، CI موفق على SHA ثابت، Railway Web/API على إصدار مطابق، واعتماد حالة التسليم.

## ضوابط التنفيذ
- لا تنشئ فرع معاينة أو خدمة Railway إضافية.
- لا تغيّر بيانات الإنتاج أو تشغّل cleanup destructive على جداول الطلاب.
- لا تعلن أن اختبارًا نجح لمجرد إرسال commit. لا تنشر SHA لم يجتز البوابات.
- لا تحول مسارات الطلاب القديمة إلى صفحات V2 بمعرف غير متوافق.
- أي كود مستخدم أو حارس أمان يبقى حتى يُثبت البديل واختباراته.

**هذا ملف متابعة فني حقيقي، وليس وثيقة إعلان إغلاق لجميع مراحل التنظيف.**
