# هِمّة V2 — P01: التدقيق الهندسي الجذري لـV1 وتصميم الهدف

**التاريخ:** 2026-10-18  
**الحالة:** **IN_PROGRESS — فحص المصدر والبنك والبنية موثق؛ V1 غير منشورة حاليًا بحسب تأكيد المالك 2026-10-18**؛ بوابة المرحلة لم تُغلق بعد.  
**المستودع:** `7eaur/himma-`  
**V1 baseline:** `stage/02-content`، SHA `4ecb27590f7c19cbe7823804b9919d91000415ef`.  
**V2 HEAD عند بدء هذا الفحص:** `6b13265a00e872e81c6ea23493aa7511d5426051` (يتغير عند تحديث هذه الوثيقة).  
**الخطة:** `09_IMPLEMENTATION_ROADMAP_AR.md`، **المصفوفة:** `22_FULL_SYSTEM_COVERAGE_AND_ACCEPTANCE_MATRIX_AR.md`.

> **فصل الأدلة:** هذا فحص مستودع حي ومراجع وقراءة تكوين Railway وGitHub Actions؛ ليس تشغيل E2E لـV2، ولا فحص واجهات بصري في متصفح متاح، ولا قراءة قاعدة إنتاج. لا توصف وظيفة «مختبرة» إلا بدليل تنفيذ. لا تغييرات على كود أو DB أو نشر.

## 1. مصادر الفحص المباشر

- GitHub `stage/02-content` لم يتغير خلال مراجعة P01؛ في مقارنة `stage/02-content...v2/01-learning-foundation-20261007` ظهرت **232 commit** للأمام، صفر للخلف قبل تحديث هذه الوثيقة، وفروقات تشغيل/واجهة غير مرتبطة فقط بالتوثيق.
- فُحصت ملفات واجهة الطالب `student/page.tsx`, `student/activity/[id]/page.tsx`, `student/session/[id]/page.tsx`، وصفحات ومجلدات الإدارة، والمكونات والخطوط والأصول العامة.
- فُحصت طبقة API: `activities.py`, `activity_runtime.py`, `content_runtime.py`, `content_student_view.py`, `canonical_content_compiler.py`, `canonical_content_publisher.py`, `adaptation.py`, `adaptation_runtime.py`, `learning_state_machine.py`, `placement_scoring.py`, `assessment.py`, `review.py`, `recordings.py`, `media.py`, `storage.py`.
- فُحص نموذج SQLAlchemy `db/models.py` و`db/activity_models.py` و`db/adaptation_models.py`، وجرد أسماء Alembic migrations حتى `0014` مع فرع إصدار عددي؛ **لم تُنفذ migrations في قاعدة بيانات فعلية**.
- فُحص بنك V2 المرجعي كامل الأعداد سابقًا: **19 درسًا و12 دعمًا و300 بند** (300 معرفًا فريدًا). البنك محفوظ ولم يُعدّل.
- GitHub CI وRailway الوصلات حيّة في تاريخ الفحص أدناه. **لا تعامل البيانات التاريخية المؤرخة على أنها إثبات تشغيل حالي**.

## 2. فروق مثبتة بين V1 وبنك V2 — Root causes

| رقم | الدرجة | المشكلة المثبتة | السبب الجذري في V1 | قرار الهدف + اختبار الإغلاق |
|---|---|---|---|---|
| R01 | P0 | لا توجد مراحل الدرس `intro→video→practice→check` | `student/activity/[id]/page.tsx` و`activities.py` مبنيان على `ContentItem/Step` وجولات نشاط، وليس درسًا بأربع مراحل؛ لا `video_media_id` في المشغّل | **REPLACE** مشغّل النشاط التعليمي ب`LessonPlayer` موحد مرتبط بخادم `LessonSession`؛ E2E L1-01 وL2-01 وL3-03 |
| R02 | P0 | لا مشغّل فيديو تعليمي ولا منظومة `asset ID→Video` | صفحة النشاط/الاختبار لا تعرض `<video>`، و`media.py` يخدم صورًا وMP3 ثابتة بmanifest، وليس ملفات فيديو درس | **NEW/REFACTOR** `VideoPlayer + MediaProvider` موحد بحالات/استئناف/إخفاقات؛ اختبار فيديو TEST_ONLY ثم تبديله دون تعديل منطق |
| R03 | P0 | بعض خيارات الأسئلة صوت بلا تسمية نصية | واجهة خيار V1 تستعمل `option.text` وتضع أصوات المثير في زر عام؛ 4 بنود V2 بها صوت مستقل داخل الخيارات | **REPLACE** `OptionRenderer` لخيارات نص/صورة/صوت مع زر استماع واختيار مستقلين؛ تحقق accessibility وخصوصية الإجابة |
| R04 | P0 | 21 `write_text` غير قابلة للتشغيل | اتحاد `Interaction` في صفحتي الطالب لا يحتوي `write_text`، و`ContentOption.text` مع `AttemptResponse.selected_option_id` يفترضان اختيارًا أو تسجيلًا | **NEW** واجهة كتابة عربية وعقد استجابة نص مفتوح/حفظ/rubric ومراجعة؛ اختبار قبول عدة صياغات صحيحة وpending-review |
| R05 | P0 | 62 `read_aloud` تتطلب دورة مراجعة متكاملة | V1 لديه `recordings/review` و`audio_submissions` ومراجعة بشرية؛ لا يمكن جعل مسار التدريب الجديد يعتمد تصحيحًا لحظيًا غير موجود | **KEEP + REFACTOR** خط التسجيل والمشرف، واجهة انتظار/إعادة، والتكيف لا يحسب pending إتقانًا؛ اختبار E2E لحالات الرفض/إعادة التسجيل |
| R06 | P0 | فصل التدريب عن تحقق الإتقان غير ممثل مباشرة في قوالب V1 | `ActivityRuntimeSubmitRequest.hint_used` يوجد في V1 لكن لا توجد كيانات دروس V2/roles/نسخ بنوك سارية بالقالب الجديد | **NEW/REFACTOR** evidence وattempt `role=practice/check/support/pre/post`، مع فصل الخصائص في API/scoring؛ اختبارات عدم احتساب hint كنجاح |
| R07 | P0 | 19 درسًا لا تتطابق مع قواعد «10 نشاط/مستوى» | `learning_state_machine.level_completion_state` يقيّد `completed_core_count` إلى 10 ويصف L3 عشر أنشطة؛ V2: 6/6/7 دروس | **REPLACE** الاعتماد العددي الثابت بسياسة مبنية على `LessonCatalog/SkillEvidence`؛ سيناريوهات إنهاء كل مستوى وتجنب التخطي غير الصحيح |
| R08 | P0 | مُجمّع/ناشر V1 غير صالح لاستيراد البنك كما هو | `canonical_content_compiler` ينشئ Round من كتالوج قديم، و`canonical_content_publisher._runtime_interaction` يعيد `multiple_choice/read_aloud`، و`_publish_steps` يمنع تغيير عدد الجولات القائمة | **NEW** `V2 compiler/validator` ونسخ محتوى غير قابلة للتغيير؛ استخدام البنى النافعة للاحتفاظ بالأمان مع importer جديد؛ 300 سؤال بلا فقد |
| R09 | P0 | تصميم V1 يعرض درجتي التسكين/النشاط بسياسات 50/80 و70/80 و10 Core | `placement_scoring` و`learning_state_machine` مكتوبان لقواعد V1 لا بنود V2 ومستوياتها الجديدة | **REVIEW/REPLACE POLICY** مقارنة مدروسة بالمحتوى والقياس والتكيف المتوازن، لا نقل thresholds تلقائيًا؛ 30 قبلي و30 بعدي ومراجعة بشرية |
| R10 | P0 | نموذج DB يمثل نوع جلسة واحدًا ضمن `pretest/posttest/core` | `AssessmentSession.session_type` CheckConstraint ولغة `Attempt` مرتبطة بالعنصر، ولا يوجد `LessonSession` مستقل أو resume stage للفيديو/التدريب/الدعم | **NEW SCHEMA** أو PostgreSQL نظيف بـV2 بعد P01: `LessonProgress/Attempt/Evidence/Review/ContentRelease` ومراجعة صلاحيات؛ test idempotency/transactions |
| R11 | P1 | التفاعلات والرفع مكررة بين صفحتي نشاط واختبار | `student/activity...` و`student/session...` تعيدان منطق MediaRecorder ورفع التسجيل بشكل مستقل | **REFACTOR** `RecordingFlow` و`InteractionRenderer` مشتركان دون كسر خصوصية التحكيم؛ نفس اختبارات الاختبار والدعم |
| R12 | P1 | صور/نص طويل لا يُضمن عرضها جيدًا في V2 | مكوّنات V1 مخصصة لبطاقات وجولات، وتحذيرات `EDUCATIONAL_UI_AUDIT_20261015_AR.md` لعرض المقروء والخيارات في الهاتف | **REFACTOR UI** مكون ReadingPassage وresponsive layouts؛ فحص 360/390/tablet/desktop بصريًا |
| R13 | P1 | فجوات صورة/صوت وملف يختلط فيه أصل الطالب بأصل تعليمي | `media.py` يبني الفهرس من ملفات تعليمية موجودة؛ تسجيل الطالب له S3 منفصل؛ مصدر الوسائط ليس نظام فيديو/حالات QA | **REFACTOR** `MediaManifest` بمصادر/حالات، وفصل recording storage عن learning assets، واختبارات missing/fallback/review |
| R14 | P1 | برمجيات V2 branch فيها إزالة أصول/مساعدات من V1 | مقارنة GitHub تثبت حذف صور `public/characters/boy-*.png` العليا و`useAudioRecorder.ts` و`idb.ts` و`StudentAudioReviewOverlay.tsx` بينما بقيت أصول `brand/logo-*.svg` وشخصيات متفرعة | **AUDIT BEFORE MERGE** مراجعة المراجع الفعلية والمكونات البديلة والاختبارات ثم حذف/إبقاء؛ **لا نفترض أن الحذف تسبب بعطل فعليًا** |
| R15 | P1 | نتيجة اختبار المحتوى لا تكفي إثبات جودة الأداء | بنك V2 صحيح بنيويًا لكن وسائط الفيديو 19 غير متوفرة و5 تنبيهات أصل (LET-01/VOC-07) وتحكيم قبلي/بعدي ناقص | **KEEP BANK** كمصدر، وإغلاق محتوى/أصول منفصل، وتفعيل النهائي في P10 فقط |

## 3. قرار الاحتفاظ/تغيير الجذور للمكونات

| المجال | القرار | لماذا |
|---|---|---|
| هوية هِمّة والشعار والألوان والشخصيات والرسومات | **KEEP/REFINE AFTER VISUAL AUDIT** | `public/brand` يحتوي 4 شعارات SVG، و`public/characters/boy,girl` متاحان؛ لا تسقط مع بيانات الطلاب |
| بنوك ومراجع الأصوات والصور التعليمية | **KEEP/REVIEW/REPLACE WEAK ASSETS** | تُستخدم مع V2 بعد تحقق النطق والمعنى والتراخيص؛ ليست تسجيلات طلاب شخصية |
| DB SQLAlchemy/PostgreSQL/Alembic | **REUSE PATTERNS, REFACTOR/NEW V2 DATABASE** | الأمان/الإصدارات/الردود موجودة، لكن قيود V1 مربوطة بالأنشطة؛ قاعدة V2 جديدة مقبولة دون بيانات طلاب قديمة |
| `OperationIdempotency` وعمليات commit آمنة | **KEEP PATTERN** | منع إعادة احتساب الإجابة والمكافأة والنتيجة |
| `canonical_content_compiler/publisher` | **REPLACE V1-SPECIFIC COMPILER** | فرض عدد الجولات ونوع التفاعل القديم لا يدعم بنك 300، مع إعادة الاستفادة من الأفكار الآمنة |
| Student Homepage/Journey | **REFACTOR/REDESIGN** | مسار جديد 19 درسًا لا 30 core، مع حفظ التنقل والمستوى وحالة الدعم |
| Activity + Assessment pages | **REPLACE DUPLICATION WITH SHARED RENDERER** | قالب واحد + UI حسب role، واجهة خيارات صوت ومحتوى صورة/نص/كتابة/قراءة |
| Audio Recording/Review | **KEEP CORRECT STATE MODEL, REFACTOR SHARED UI** | يمنع `pending` من احتساب نتائج كاذبة |
| Adaptation and reward | **REFACTOR/REVALIDATE** | قواعد الـ10 core وعتبات القديم لا تُنقل لدرس 3–4 بندًا بلا إعادة معايرة |
| Supervisor/Reports/Admin | **KEEP SECURITY MODEL, REDESIGN V2 PROJECTIONS** | يحتاج تقدم الدروس/أنواع دعم وكتابة ونص وصوت وتقارير قبلي/بعدي |
| Media Service | **EXTEND/REPLACE INDEX PROVIDER** | دعم فيديوهات وعقود media وأصول الاختبار STAGING مع منع نشر ناقص |

## 4. واقع GitHub Actions — الأدلة المؤكدة

**فرع مصدر كود V1 التاريخي (غير منشور حاليًا):** `stage/02-content`، HEAD `4ecb275...`.

أحدث GitHub Actions المدرجة لهذا الرأس في 2026-09-21:
- `Himma M04 — Responsive Visual Gate`: **success**، run `35551846252`.
- `Himma M09 — Release Readiness Gate`: **success**، run `35551846250`.
- `Himma CI — Quality Gate`: **failure**، run `35551846194`.
  - `frontend` و`backend` في ذلك التشغيل: **success**.
  - `security`: **failure** في خطوة **Scan current tree for committed secrets** (`gitleaks`).
  - `integration`: **skipped**؛ لذلك لا يجوز وصف هذا الرأس بأنه اجتاز CI كاملًا.
  - **حد النتيجة:** لا يكشف اسم الخطوة وحده عن وجود سر مكشوف؛ يلزم مراجعة لوج الفحص وسبب فشله ومعالجة إثباته قبل الدمج.
- فرع `v2/01-learning-foundation-20261007` لم تُظهر له GitHub Actions تشغيلًا في الاستعلام الحالي. إعداد `.github/workflows/ci.yml` يراقب `main,stage/*,recovery/*,b*/*,integration/*,audit/*` وPR إلى main، وليس `v2/*`؛ **بوابة الجودة على V2 ليست مثبتة**. يجب معالجة Trigger أو آلية PR/staging قبل إغلاق P01/P02.

## 5. ما أمكن التحقق منه على Railway

**المشروع المتصل:** `friendly-dream`، البيئة `production`، repo المصدر `7eaur/himma-` والفرع لخدمتي الويب وAPI `stage/02-content`. ظهرت خدمات `himma-web,himma-api,Postgres,Redis` وأحجام PostgreSQL/Redis وbucket `himma-audio` كموارد `live`.

**توضيح الحالة: أكد المالك بتاريخ 2026-10-18 أن V1 لم تعد منشورة.** معلومات Railway التالية تاريخية/تشخيصية فقط؛ لا نعتمدها لافتراض أن الموقع الحي يجب استرجاعه:
- `describe_environment` أظهر `himma-api` أحدث Deployment بحالة `FAILED` بتاريخ **2026-09-17**، و`himma-web` `latestDeployment=null` رغم وجود الخدمة واسم نطاق `himma-web-production.up.railway.app`.
- قائمة deployments أظهرت محاولات 2026-09-21 لهما بحالة `REMOVED` على commit `4ecb275...`. ترتيب موارد العرض/الإصدارات الحالية **ملتبس ويحتاج مصالحة مع Railway runtime/status والـlogs**؛ لا نستنتج قطع الخدمة لمجرد أحد حقول API.
- تقرير التشخيص للفشل القديم لم يُرجع تحليلًا، ولوج البناء أظهر إتمام صورة البناء بينما لوج Deploy المقتطع لم يظهر معلومات تحسم السبب.
- حاولنا فتح نطاق الويب بالأدوات المتاحة ولم نستطع الوصول إليه من بيئة الفحص. **هذا ليس دليلًا قاطعًا على عطل للمستخدم النهائي، ولا يُعد مراجعة واجهة مباشرة**.
- بيئة `himma-sandbox` في حساب Railway متصل آخر موجودة أيضًا؛ ليست مرجع الإنتاج ما لم يُثبت ربطها الفعلي. لا نغيّرها قبل القرار.

**قرار الفحص بعد توضيح المالك:** لا نحتاج إعادة نشر V1 ولا إثبات Health لها لإكمال P01؛ نستخدم الكود وGit history والأصول المرجعية. عند تشغيل V2 لاحقًا نجهز بيئة معزولة ببيانات طلاب اصطناعية، ونختبر Health/API/DB وواجهة الطالب والمشرف هناك. نراجع الخدمات القديمة فقط لمنع لمس إنتاج/أصول مهمة بالخطأ؛ لا تُنسخ أسرار Railway أو بيانات طلاب إلى المستودع.

## 6. التصميم المستهدف الذي سيُنفذ من P02

```text
V2 AUTHORING BANK [L1/L2/L3 + pre/post] — server/private
  ↓ schema validation + 300 ID/ref QA + approvals
Immutable ContentRelease + MediaManifest
  ↓ student projection allowlist (no answers / rubrics / hidden labels)
Student route → Pretest 30 → Placement/Skill Gaps → Journey
  ↓
LESSON SHELL [INTRO → VIDEO → GUIDED(3–4) → CHECK(3–4)]
              ↓ MediaProvider(TEST_ONLY staging / APPROVED real production)
              ↓ QuestionRenderer(text/image/audio/sequence/build/read/write)
              ↓ Attempts/Evidence(idempotent) → Adaptation/Support focus
              ↓ Support runner (focus only 2–3 check) → Resume lesson
              ↓ Next lesson/level → Posttest 30 → Report
  ↓
Supervisor: audio/writing review, progress, evidence, assets, reports
```

**خط فصل مطلوب:** الطالب لا ينقل بيانات التصحيح أو توصيات AI غير المعتمدة من الـAPI. المشرف وحده يستطيع تحكيم التسجيل والكتابة حيث يلزم. مشاهدة الفيديو ليست نجاحًا للمهارة.

## 7. مخرجات P01 المُنجزة حتى الآن وحدودها

**تم:**
1. تحديد رؤوس GitHub ومقارنة الحالة الحية للفرعين؛ فصل بنك المحتوى من تشغيل V1.
2. قراءة الشاشات ومكون التسجيل وبعض مسارات Backend/DB والتكيف وملفات assets وفهرس API وأسماء migrations.
3. استخراج 15 فجوة/قرار مجال موثق بالمسار والسبب والهدف والاختبار.
4. فحص حالة Actions ووجود مشكلة في تشغيل Security وتشغيل Integration على V1 وعدم ظهور CI لـV2.
5. استعلام Railway المتصل دون قراءة بيانات طلاب/أسرار، وتسجيل عدم وضوح حالة نشر الويب والـAPI.
6. إقرار تصميم V2 بقوالب موحدة ومشغل الفيديو المبكر والوسائط التجريبية في staging وإنتاج الأصول أخيرًا، دون فقد هوية/وسائط V1 النافعة.

**لم يثبت بعد (بوابات مفتوحة، لا نخفيها):**
- **G1 (الحالة: RESCOPED — لا عائق):** أكد المالك أن V1 لم تعد منشورة؛ **لا نطلب إعادة تشغيلها أو إثبات HTTP حي لها**. المطلوب فقط تثبيت مصدر الكود وتحديد نطاق البيئة المعزولة التجريبية لـV2، وتقرير عدم المساس بموارد Railway القديمة.
- **G2** التحقق من سبب `gitleaks` الحقيقي ثم إقرار خطة تشغيل CI Quality Gate + Integration على V2 (يُنفّذ تشغيله فعليًا عند بدء التعديلات البرمجية قبل دمجها). `v2/*` يجب أن يحصل على Gate قابل للتكرار.
- **G3 (معدّل):** فحص تصميم V1 الموجود في الكود والأصول والواجهات؛ إن توفرت لقطات قديمة فهي مرجع اختياري، **ولا يشترط استرجاع نشر V1**. يُنفذ الفحص البصري التشغيلي الحاسم للهاتف والديسكتوب على معاينة V2 مع حسابات تجريبية في المراحل P03/P09، ويُوثق بالدليل.
- **G4 (معدّل):** فحص schema/migrations من ملفات المصدر، والتحقق من قدرة إنشاء قاعدة V2 نظيفة في بيئة اختبار قبل البرمجة؛ لا يلزم الوصول إلى بيانات مستخدمي V1 التاريخية ولا نقلها.
- **G5** جرد ملفات الهوية والصور والأصوات كاملة مع قرارات keep/edit/replace ومطابقة استدعاءات المسارات؛ الفهرسة الحالية ليست اختبارًا بصريًا/سمعيًا لكل ملف.
- **G6** تصميم تفصيلي قابل للاختبار لعقد `LessonSession`, `StudentSafePayload`, `MediaProvider`, `Answer/Review` وخطة قاعدة V2 مستقلّة، بناءً على المصدر والبنك وجرد الأصول؛ لا يتوقف على URL قديم.
- **G7 (معدّل):** فحص أو اختبار الوحدات المرشحة لإعادة الاستخدام عند إدخالها في V2 ببيانات اصطناعية؛ لا يُطلب تشغيل موقع V1 كاملًا.

**القرار المرحلي:** `P01 = IN_PROGRESS` وليس `ready_for_review`. إنجاز التوثيق والفحص الثابت لا يغلق البوابة. لا يبدأ P02 أو تغيير كود/بيئة الإنتاج حتى مراجعة الأدلة وتوقيع المرحلة وفق سياسة «تم».

## 8. سياسة البيانات القديمة — تصحيح المالك محفوظ

**لا حاجة لترحيل:** حسابات الطلاب القديمة، تقدمهم ودرجاتهم ومحاولاتهم، تسجيلات قراءاتهم الشخصية، سجلات استخدامهم وجلساتهم. يجوز قاعدة V2 تشغيلية جديدة نظيفة.

**مهم ويُفحص/يُحافظ عليه:** هوية هِمّة وشعاراتها وألوانها وخطوطها، الصور التعليمية والشخصيات والرسوم والصوت التعليمي، المكونات والتصميم والكود السليم. لا تُزال هذه الأصول أثناء تنظيف تاريخ الطلاب. بيانات أشخاص حقيقية لا تُحذف إلا وفق ضوابط الاحتفاظ والخصوصية وبقرار مستقل.

## 9. أثر الخطة

هذه الوثيقة **تكتشف وتفصل السبب الجذري**، أما P02..P10 وأماكن التنفيذ وشروط قبول جميع السيناريوهات فهي في `09_IMPLEMENTATION_ROADMAP_AR.md` و`22_FULL_SYSTEM_COVERAGE_AND_ACCEPTANCE_MATRIX_AR.md`. يمنع تقديم هذه الوثيقة بوصفها اختبارات نجاح فعلية أو تصريحًا بإطلاق V2.


## 10. تحديث قيد التشغيل — توضيح المستخدم 2026-10-18

- **الحقيقة الحالية من المالك:** الإصدار الأول غير منشور الآن. لا يوجد شرط لإعادة نشره أو توفير حساباته القديمة للبدء أو لإغلاق تدقيق P01.
- **مصدر فحص V1:** فرع GitHub `stage/02-content` والملفات التاريخية والأصول؛ لا يُفترض وجود صفحة إنتاج مفتوحة.
- **مصدر التجربة البصرية والتنفيذية اللاحقة:** معاينة V2 مع حسابات وتجارب ووسائط `TEST_ONLY` في بيئة معزولة عندما يحين عمل P03–P09؛ الفحص البصري لكود V1 مرجعي وليس اختبارًا مباشرًا.
- **ما نحتاجه من المالك الآن:** لا ملفات أو صلاحيات إضافية إلزامية لاستكمال التدقيق التخطيطي. لقطات شاشة قديمة اختيارية فقط، وعند طلب إنشاء بيئة مدفوعة أو نشر معاينة يلزم قرار منفصل قبل ذلك.
- **النتيجة:** تغيير معيار G1/G3/G4/G7 بما يمنع تعطيل تطوير V2 على نسخة V1 غير منشورة؛ تبقى مرحلة P01 قيد التنفيذ حتى يكتمل تصميم العقود والجرد والتقييم.
