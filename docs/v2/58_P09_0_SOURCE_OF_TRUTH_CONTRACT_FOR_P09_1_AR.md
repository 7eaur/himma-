# هِمّة V2 — عقد توحيد مصدر بيانات الواجهات قبل P09.1

**النوع:** مخرج تصميم وتحقيق ضمن P09.0، **وليس بدء تنفيذ P09.1**  
**التاريخ:** 2026-10-25  
**أساس الإثبات:** قراءة فعلية لـ `services/api/v2_assessment_runtime.py` و`v2_lesson_runtime.py` و`db/learning_models.py` ولوحة `apps/web/src/app/student/page.tsx` والواجهات الإدارية.  
**المرجع:** `56_P09_0_LIVE_UI_SOURCE_BASELINE_AND_GAP_REGISTER_AR.md` و`57_P09_0_VERIFIED_VISUAL_QA_EVIDENCE_AR.md`.

## 1. سبب المشكلة الجذري (وليس ترقيع شكل)

- تحتوي `/student` على استدعاءات `/api/profile` و`/api/activities/status` و`/api/journey` و`/api/rewards` الخاصّة بـV1، مع `/api/v2/assessments/current-action`. لذلك قد تُعرض نسب إكمال أنشطة V1 ونجومها بجانب مسار الـ19 درسًا في V2.
- يوجد بالفعل **محرك القرار V2**: `GET /v2/assessments/current-action` يراجع تقييم V2 الجاري و`StudentJourney` و`LessonSession` وحالة البعدي ويُصدر `action/kind/state/href/label`. يجب عدم تكرار شجرة القرار في React.
- `GET /v2/lessons/catalog` يحسب قائمة الدروس، لكنه يشتق `first_for_level` من `Student.current_level`، ثم يقرأ `StudentJourney.current_level`، وهذا مصدران مختلفان لمستوى واحد يحتاجان توثيق أولوية صريحة.
- المشرف يعرض `/api/researcher/students` و`/api/researcher/reports/summary` القديمة، بينما توجد مصادر V2 منفصلة في `/v2/assessments/admin/students/{id}/summary` و`/v2/assessments/admin/reports/summary`. لا يجوز خلط أرقام V1 وV2 تحت عنوان «تقدم V2».
- `StudentJourney` يُثبّت `content_release_id`، و`LessonSession` يثبّت نفس مرجع الإصدار في كل محاولة. القراءة يجب أن تُسقط النتائج من **إصدار الجلسة** لا من نسخة بنك متغيرة حديثًا.
- لا يوجد عقد rewards V2 معتمد للتصحيح الآلي والنجوم، ولذلك `/api/rewards` يظل تراثيًا ولا يجوز استخدامه لقياس تقدم V2 أو إعطاء شارة جديدة.

## 2. ملكية البيانات والعقد المقترح للقراءة فقط

| معلومة UI | مصدر الحقيقة المطلوب | معايير الثبات |
|---|---|---|
| قرار الانتقال الآن | `StudentJourney` + أحدث `AssessmentSession` رسمي + `LessonSession` نشط، بإخراج مركز من `current-action` | تقييم معلّق يتقدم على بداية درس، والتسكين المعلق لا يتجاوز؛ لا اعتماد تلقائي لدرجات قراءة |
| المستوى والدرس الحالي | `StudentJourney.current_level/current_lesson_id` عندما يوجد، مع fallback تاريخي معلن فقط للحساب القديم | `Student.current_level` لا يتجاوز قرار التسكين V2 |
| الدروس الـ19 وحالاتها | `ContentRelease` المثبّتة + `LessonSession` لكل `lesson_id` | `done/current/locked/skipped` من حالة صحيحة، لا من المظهر أو V1 activities |
| تقدم الطالب في V2 | عدد `LessonSession` الرسمية `status=completed` من إجمالي الدروس **المتاحة** في مساره المثبت؛ افصل الدروس السابقة التي تجاوزها التسكين | لا تستخدم `core_completed_items/10` أو `activities/status`؛ لا تحول غياب البيانات إلى صفر إتقان |
| صوت الطفل والمراجعات | `LessonQuestionResponse` و`AssessmentQuestionResponse` و`AudioSubmission` و`V2ReviewRetryTask` | آخر تسجيل مقيم فقط قابل للتشغيل؛ pending لا يحسب درجة ولا يُعرض في الأرشيف |
| الاختبار القبلي/البعدي | `AssessmentSession` الرسمي و`official_for_reporting` وإجابات `graded` | درجات null تعني غير محسوبة، لا 0؛ اعرض انتظار قرار المشرف |
| تقارير المشرف | read-model من V2 assessment/lesson/skill evidence | افصل بيانات V1 التاريخية تحت عنوان واضح؛ لا تنسب تحسنًا أو مهارة غير مقيمة |
| النجوم والشارات | **مؤجلة** حتى إصدار دفتر أحداث V2 رسمي idempotent | لا تنسخ نجوم V1 ولا تمنح نجومًا بسبب صورة أو حالة مؤقتة |
| البنك والوسائط | `ContentRelease` + سجل `get_release`/مفاتيح `get_media` ضمن حدود الوصول | لا تصل `private_answer` ولا S3 key للطالب؛ وسيط `TEST_ONLY` يبقى موسومًا |
| رموز دخول الأطفال | إرجاع صلاحيات محكومة من خدمة الطلاب وواجهة تخفيه افتراضيًا | لا تعرض مفتاح الدخول صريحًا في كل صف أو لقطة مراجعة، وراجع أثر التصدير |

## 3. Read-models الملزمة المقترحة في P09.1

**`StudentV2HomeDTO`** (صلاحية الطالب صاحب الجلسة فقط): 
- `mode: "v2" | "legacy"`؛ اختيار `legacy` فقط عند عدم وجود رحلة V2 وتوجيه تاريخي مؤكد.
- `current_action: {action,kind?,state?,href?,label}` مع الالتزام بالـenum الوارد من backend.
- `journey: {placement_state,current_level,current_lesson_id,content_release_version,status}` بدون بيانات الطالب الخاصة غير اللازمة للواجهة.
- `progress: {completed_lessons,assigned_lessons,skipped_by_placement,pending_review,display_percent|null}`.
- `rewards: {state:"not_implemented_v2"}` حتى اعتماد rewards، بلا نجوم صفرية مصطنعة.
- `data_status: "ready"|"partial"|"unavailable"`؛ فشل أحد المصادر لا ينتج تقدمًا فارغًا صامتًا.

**`SupervisorStudentV2DTO`** (دور مشرف فقط): بيانات الطالب المختصرة، مصدر ومستوى التسكين، 19 درسًا وحالاتها، نتيجتا التقييم الرسمي، إجابات القراءة التي تنتظر المراجعة، آخر تسجيل مُقيّم، قائمة فجوات الوسائط، إصدار المحتوى. تظل عملية التسكين والمراجعة عبر مسارات POST الحالية بصلاحياتها، لا عبر read-model يسمح بالتعديل.

**`SupervisorV2CohortDTO`** (صلاحية مشرف): إجمالي الأعضاء، `pending_pretests` و`pending_reviews` و`completed_posttests` من V2 الرسمية، وعدد المحاولات التي لم تراجع. يَرجع `null` للمقاييس غير المتحققة، ويكشف `data_as_of` و`source_release` لا مجرد رقم قديم.

## 4. تدقيقان إلزاميان قبل البرمجة

1. `current-action` يفحص أولًا تقييمًا V2 جاريا ثم رحلة الطالب ثم الدرس؛ يجب اختبار علاقة حالة `placement_pending_review` وعدم بدء القبلي مرة ثانية عند انتهاء كل الأسئلة والانتظار، وكذلك حساب الطالب الذي لديه `StudentJourney` ولا `LessonSession`.
2. `lesson_catalog` يبني `first_for_level` من `Student.current_level` لكنه يبني القفل من `StudentJourney.current_level`؛ ينبغي تفضيل رحلة V2 المثبّتة في جميع أجزاء القرار مع اختبار تباعد الحقلين، وبلا تغيير تاريخ V1.

## 5. مصفوفة اختبارات يجب أن ينجح بها P09.1 قبل اعتمادها

- Student V2 جديد بلا تسكين → pretest؛ مكتمل قبلي ينتظر مشرفًا → انتظار حقيقي؛ بعد التسكين → الدرس الصحيح، بدون قفز.
- درس في وضع `waiting_review` → لا يحتسب completed ولا يسجل تقدمًا وهميًا؛ واجهة الطالب تعرض انتظارًا قابلًا للاستئناف.
- درس مكتمل + دعم محدد/فجوة → يبقى دعم V2 في المستوى الصحيح، ولا يخفيه تقدم V1.
- استجابة قبلي/بعدي رسمية غير مكتملة → النتيجة null؛ لا تحسب درجة ولا تعطي نجومًا.
- حساب V1 تاريخي بدون رحلة V2 → تجربة legacy مستقرة، ولا تُنشئ رحلة جديدة لمجرد GET.
- تناقض `Student.current_level` مقابل `StudentJourney.current_level` → أولوية الرحلة V2 واختبار Regression.
- طالب يحاول الوصول إلى read-model زميله أو قائمة المشرف أو تسجيله → 403/404 بلا تسريب.
- ملخصات 19 درسًا متوازنة حسابيًا، وتُحسب `skipped_by_placement` منفصلة عن `completed`؛ القيم الجزئية متميزة عن الفارغة.
- refresh/filter متزامن للمشرف → الرد الأخير فقط، ولا يظل صوت طفل آخر أو تقرير قديم بعد فشل المصدر.
- Test-only media/ASR → لا عرض «نجح التقييم بالذكاء الاصطناعي» دون إثبات، ولا اعتماد إعلامي لأي وسيط اختبار.
- Safari/Android audio/permissions ببرهان جهاز حقيقي في بوابة P09/P10 المستقلة، وليس بمرور Chromium فقط.

## 6. ترتيب التنفيذ بعد إغلاق P09.0 واعتماد المالك

`P09.1-A` اختبار قرار current-action والتسكين وعدم التكرار؛ `P09.1-B` read-model backend مع قيود الصلاحية والإصدارات؛ `P09.1-C` واجهة الطالب وتحويل حسابات legacy؛ `P09.1-D` واجهة المشرف وتقارير الطلاب؛ `P09.1-E` E2E + screenshots + QA + توثيق. **لا تبدأ هذه الأعمال قبل اعتماد Gate P09.0؛ هذا المستند عقد تسليم فقط.**

**قرار تقني ثابت:** إنشاء مصدر read-model مركزي بقراءة فعلية من قاعدة V2، لا تغيير أسماء الدوال القائمة، ولا استبدال scoring/speech-review، ولا إنشاء قاعدة بيانات موازية أو كسر إصدارات المحاولات القديمة.
