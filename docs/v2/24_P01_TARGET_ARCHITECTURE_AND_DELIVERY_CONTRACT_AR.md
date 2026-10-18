# هِمّة V2 — P01: تصميم المعمارية المستهدفة وعقود البناء من الجذور

**التاريخ:** 2026-10-18  
**الحالة:** تصميم معماري وقرارات تحضيرية؛ **لا تنفيذ برمجي/DB/نشر بهذا المستند**.  
**المصادر الحاكمة:** `20_VERIFIED_CONTENT_BASELINE_AND_GAPS_AR.md`، `23_P01_V1_ROOT_CAUSE_AND_V2_TARGET_AUDIT_AR.md`، `09_IMPLEMENTATION_ROADMAP_AR.md`، `22_FULL_SYSTEM_COVERAGE_AND_ACCEPTANCE_MATRIX_AR.md`، وملفات `docs/v2/content-bank/*_DRAFT.json`.

## 1. ما الذي ثبت وما لا نفترضه

- البنك في الفرع يحتوي **19 درسًا، 12 دعمًا، 300 سؤال/بند و13 مهارة**؛ البيانات الحالية مصدر V2 المعتمد هندسيًا، لكنها ما تزال `draft/pending QA` تربويًا/وسائطيًا.
- أنواع التفاعل السبعة: `choose_one=107`، `listen_choose_one=52`، `sequence=45`، `build_word=9`، `choose_image=4`، `read_aloud=62`، `write_text=21`. أربعة بنود من بنك L1-01 تحتاج صوتًا **داخل الخيارات**.
- في كتالوج الوسائط بالملفات الأربعة **89 معرفًا فريدًا**: **47 صوتًا، 23 صورة، 19 فيديو**. مرشح لإعادة استخدام V1 **56 أصلًا** (33 صوتًا +23 صورة)؛ جميع مسارات تلك الملفات الـ56 موجودة في مستودع GitHub وفق جرد مجلدَي المصدر؛ **هذا لا يثبت جودة النطق أو الصورة أو التراخيص**. النواقص `missing_new=33`: **19 فيديو + 14 صوتًا**. لا صور جديدة معنونة missing في كتالوج البنك الحالي؛ أي صورة تحتاج تغييرًا بعد QA تسجل لاحقًا كفجوة مع رقم السؤال. هناك **5 تحذيرات مراجعة أصل** مسجلة في QA (LET-01 وVOC-07).
- لكل درس **4 تدريبات**. اختبار **4** لكل درس ما عدا L3-02 يضم **3**. بنك الدعم حسب `focus_item_map` يقدم تحققًا من بندين حسب الفجوة؛ لا تُعرض جميع بدائل الدعم معًا.
- بحسب توضيح المالك: **V1 غير منشورة**؛ لا إعادة تشغيل لها، ولا نقل حسابات الطلاب وتقدمهم أو تسجيلاتهم القديمة. تُحفظ هويتها وشخصياتها وتصاميمها وأصولها التعليمية النافعة.
- **الاختبارات التشغيلية/CI وQA الوسائط لا تزال مستقبلية**؛ لا نستخدم تقرير الفحص الثابت بديلًا عنها.

## 2. القرار البنيوي الموصى به — minimal clean V2

نحتفظ **بالتقنيات المجربة**: Next.js/React للواجهة، FastAPI للخادم، PostgreSQL لحفظ تقدم V2، ومكتبة صوت/صورة المشروع النافعة. نبني **مسار نطاق تعليمي جديد** بدل مد V1 إلى عشرات الاستثناءات.

```text
Git tracked authored V2 JSON + MEDIA inventory
          ↓ validate, lock version, compile (server/private)
Private ContentRelease / Readonly ContentCatalog
          ↓ student-safe API (allowlist, media refs resolved)
Next.js: StudentJourney + LessonShell + QuestionRenderer + VideoPlayer
          ↑                      ↓
FastAPI V2: JourneyService / LessonSession / Assessment / Evidence
          ↓
       PostgreSQL: new V2 runtime data (student, progress, attempts, review)
          ↓
  Supervisor: Pending Reading/Writing Review + Reporting + Media Readiness
          ↖
    MediaProvider: fixture (STAGING ONLY) | approved real assets (RELEASE)
```

**اختيار تصميم مهم:** لمجموعة بنك صغيرة وثابتة نسبيًا (300 سؤال)، الأفضل كبداية **تحويل ملفات JSON إلى release immutable وبناء فهرس سري في Backend** بدل نسخ جميع الأسئلة/الإجابات إلى عدة جداول SQL وتكرارها؛ SQL يحفظ الطلاب وحالة الجلسات والمحاولات والأدلة ونتائج المراجعة ومراجع إصدارات المحتوى. يُختبر هذا الاختيار عند تنفيذ P02، وإن ثبتت حاجة تحرير محتوى من واجهة مشرف مستقبلًا فله قرار جديد، **ولا نبني CMS الآن**.

المصدر الوحيد لبيانات السؤال الكاملة هو **الـrelease الخاص بالخادم**؛ student API ليس ملف JSON الخام ولا يُعيد `private_answer` أو `rubric` أو `reading_reference` أو `origin_v1`.

## 3. نطاقات البرمجة والمسؤوليات — منع التكرار

| المسؤولية | وحدة V2 المقترحة | ملاحظات على V1 |
|---|---|---|
| استقبال بنك التأليف | `content/validate.py`, `content/compile.py`, `content/repository.py` (أسماء تصميمية لا ملفات منفذة) | إعادة استخدام مبادئ checksums وidempotency مع **عدم فرض قاعدة 10 جولات أو تحويل كل تفاعل إلى multiple_choice** |
| فهرس المحتوى الآمن | `student_content_projection` | اعتماد allowlist واختبارات تسريب تشمل نص الوسائط والتسمية المخفية |
| جلسة الطالب التعليمية | `lesson_service`, `journey_service` | مشغل الدرس **ليس** مجرد `AssessmentSession(core)` القديم؛ يخزن المرحلة الحالية |
| التصحيح والدليل | `answer_service`, `evidence_service` | فصل guided عن check وعن pending review؛ idempotency مرة واحدة |
| التكيف والدعم | `adaptation_service`, `support_service` | قواعد تُراجع لـ19 درسًا و13 مهارة، لا `10 core/level` |
| الفيديوهات والأصول | `media_manifest`, `media_provider` | يدعم تحويل fixture إلى approved asset دون تغيير الواجهة |
| مراجعة القراءات والكتابة | `review_service` | الاستفادة من منطق الفصل بين pending/graded في V1، لا تحويل AI غير متاح إلى حكم نهائي |
| المشرف/التقارير | `supervisor_service`, `reports_service` | الصلاحيات والملخصات نعيد بنائها على V2 |
| الواجهة | `StudentJourney`, `LessonShell`, `QuestionRenderer`, `VideoPlayer`, `ReadingRecorder`, `WritingAnswer` | مكونات واحدة لكل أدوار الأسئلة؛ تجنب نسخ التسجيل والتصحيح داخل صفحتي activity/session |

هذه **حدود نطاقات**، وليست دعوة لإنشاء عشرات الخدمات والشبكات أو تقسيم المشروع إلى Microservices. تبقى API واحدة وتطبيق React واحدًا، بتقسيم ملفات داخلي نظيف.

## 4. عقد قاعدة بيانات V2 النظيفة المقترح

**الخطوة P02:** تحديد schema حقيقي ثم اختباره بمهاجرات Alembic على قاعدة تجريبية جديدة؛ لا حاجة لترحيل تاريخ الطلاب.

**كيانات الحد الأدنى المنطقية** (عدد الجداول النهائي يحدده التصميم الفعلي وفق الحاجة، وليست قائمة فرضية ملزمة):
- `content_releases`: `id/version/checksum/status/created_at/approved_at` مع بيانات الإصدار المرجعية؛ immutable بعد النشر.
- `students`: حسابات V2 الجديدة ودخول آمن وأدوار/صلاحيات المشرف.
- `student_journeys`: `student_id/release_id/current_level/current_lesson_id/placement_state/status`، مع قيد يمنع تقدمًا متناقضًا.
- `lesson_sessions`: `student_id/lesson_id/release_id/stage/step_index/status/updated_at/video_seen`، مع uniqueness للجلسة النشطة حسب السياسة.
- `question_responses`: `attempt_id/question_id/role/answer_json/submit_key/status/scored_at`، والملف الشخصي للصوت **مرجع تخزين آمن فقط**.
- `skill_evidence`: `student_id/skill/evidence_type/question_id/correctness/review_status/error_focus/version`، لا تستخدم أدلة تدريب hinted كإتقان.
- `support_assignments`: `focus/support_group/source_lesson/status/return_to` كي لا تضيع نقطة عودة الطالب.
- `assessment_runs`: `pre/post/release/status/assigned_level/completed_at` وربط نتائج المراجعة.
- `review_tasks`: `kind=reading|writing/response_id/status/decision/reviewer/timestamps` وصلاحيات ومراجعة.
- `audit_events`: أحداث أمنية/تقييمية لازمة فقط، مع عدم تسريب محتوى خاص بالطفل أو الإجابات.

**مبادئ ضرورية:** JSON غير قابلة للكشف للعامة للإجابات، constraints/foreign keys/transaction boundaries، عدم تكرار النتائج بسبب replay، مؤشر وحيد لحالة تعلم نشطة، migrations مفحوصة، وتاريخ محتوى لكل جلسة. لا نقل recordings V1 ولا حسابات قديمة تلقائيًا.

## 5. عقود الطلبات والردود قبل الكود

### فتح المسار والدرس
- `GET /api/v2/journey`: role/level/current_lesson/status/progress/support flags مع صلاحية الطالب.
- `POST /api/v2/lessons/{lessonId}/start`: idempotent، يعيد `sessionId` و`releaseVersion` ولا يبدأ درسًا غير مصرح أو غير مكتمل الوسائط في الإنتاج.
- `GET /api/v2/lessons/sessions/{sessionId}`: `stage` + `currentStep` + `resume` وحالة الـvideo والميديا؛ لا private answer.
- `POST .../video-progress`: `idempotencyKey` + حدث مشاهدة، ولا يغير درجة المهارة.
- `POST .../answers`: `questionId`, `role`, `answer`, `idempotencyKey`; النتيجة `guided_feedback` أو `pending_review` أو `submitted`؛ لا تصحيح مستقل كاشف داخل الاختبار.
- `POST .../advance`: Server-validated state transition وليس زر Frontend حرًّا يخرق المرحلة.
- `GET /api/v2/media/{assetId}`: عقد metadata وحالة الوسيط، وURL آمن حسب السياسات.

**المسارات المذكورة نموذج عقد مقترح** يمكن تنقيح أسمائها أثناء P02. لا تُنشأ Alias للحفاظ على V1 بلا حاجة. لا يمر `private_answer` في الرد حتى لو أرسل المتصفح query parameter غير معروف.

### تكوين سؤال الطالب (مسموح فقط)
```json
{
  "questionId": "L1-01-IC-A01",
  "interaction": "listen_choose_one",
  "prompt": "اختر الصوت المناسب.",
  "stimulus": { "text": null, "media": [] },
  "options": [
    { "id": "a", "text": null, "media": [{ "assetId": "LET-01", "kind": "audio" }] }
  ],
  "presentation": { "layout": "adaptive_cards" }
}
```
**النموذج أعلاه تمثيلي لا يمثل خيارات سؤال مكتمل**؛ الغرض إثبات أن صوت الخيار ليس اسمه المكتوب، وأن دور السؤال/الإجابة السرية مستتران في الخلفية.

## 6. آلة حالات الطالب والفيديو

```text
NEW_STUDENT → PRETEST → PLACED → LESSON_INTRO → VIDEO
                                               ↓ [completed per approved policy]
                                      GUIDED_PRACTICE (3–4)
                                               ↓
                                      INDEPENDENT_CHECK (3–4)
                                               ↓
                          ┌── SUCCESS → NEXT LESSON / NEXT LEVEL
                          ├── INCONCLUSIVE → SHORT VERIFICATION
                          ├── FOCUS GAP → SUPPORT INTRO→TEACH→PRACTICE→CHECK(2–3)→RESUME
                          └── NEEDS HUMAN REVIEW → PENDING (no fake grade)
LAST LEVEL → POSTTEST → SUMMARY/REPORT
```

- كل انتقال يراجعه الخادم، ويحفظ آخر مرحلة قبل الـrefresh؛ `video ended` ليس تلقائيًا دليل قراءة أو إتقان.
- في Staging فيديو تعليمي **Fixture TEST_ONLY واضح** لا يختلط مع وسيط معتمد؛ في الإنتاج تُحظر الدروس ذات الوسائط المطلوبة غير المعتمدة قبل فتح الجلسة.
- Player واحد مع `idle/loading/buffering/playing/paused/ended/error`، وأزرار replay/pause/volume/captions، وتحمل انقطاع الشبكة وتدوير الهاتف وسجلات مشاهدة خفيفة.
- إذا فشل الفيديو الحقيقي: `retry` مع رسالة لطيفة وقناة دعم؛ **لا نتجاوز الدرس ولا نسجل إكمالًا زائفًا**.
- الصوت في الخيارات مستقل عن `selectedOption`؛ زر تشغيل لا يُعتبر اختيارًا. لا تنشر transcript لجواب الاستماع أو label للصورة يكشف الإجابة.
- لا حبس الطالب إلى الأبد بسبب pending review: **السياسة الأكاديمية** تحدد ما يمكن متابعته مع إبقاء evidence غير مكتمل، وتكون نقطة قرار المشرف واضحة.
- عند إغلاق الدعم يُستأنف الدرس الذي أوقفه، مع حماية من حلقات الدعم اللانهائية.

## 7. سياسة التكيف والتقييم الواجب معايرتها

- نبقي **13 مهارة و12 دعمًا** وعلاقة `focus_item_map` من البنك. يحدد الفرق بين أداء تدريب بمساعدة وقياس مستقل غير مساعد.
- لا ننقل عتبات V1 `50/80` للتسكين ولا `70/80` للانتقال ولا قواعد `10 core activities` مباشرة. نطلب معايرة تربوية وتحديد `policyVersion`، مع اختبارات أن الخطأ الفردي لا يرسل فورًا للدعم.
- `read_aloud` و`write_text` إذا كانا بحاجة مراجعة مشرف فحالتهما `pending`، لا `true/false` قبل المراجعة؛ الاستجابة الفورية في التدريب تكون مساعدة عامة لا ادعاء فهم صوت الطالب.
- القبلي والبعدي **30/30** موزعان على المهارات الـ13، ويُعاد اختبار تكافؤ الصعوبة ومصداقية التقارير لا نكتفي بتساوي التوزيع.
- مكافآت V1 إن استُخدمت تُربط بحدث واحد مستقر محمي ضد التكرار.

## 8. خريطة الاحتفاظ بالأصول والهوية

**الموجود فعليًا في فرع V2:**
- `apps/web/public/brand/`: أربعة شعارات SVG (`logo-flat`, `logo-gradient`, `logo-navy`, `logo-white`) — **مرشحة KEEP**.
- `apps/web/public/characters/boy/` و`girl/`: **10 ملفات شخصية** مرحب/شرح/تشجيع/نجاح/إعادة — **KEEP مع تدقيق بصري وحجم**.
- `apps/web/public/audio/`: **4 أصوات Feedback** (`fb-correct/wrong/encourage/complete`) — **KEEP إن كانت مناسبة**.
- `apps/web/src/app/globals.css` يحوي tokens ألوان هِمّة (`#347FD9`, `#51B985`, `#FFC857`, `#20364D`) وخط Tajawal للطالب وIBM Plex Sans Arabic للمشرف؛ `layout.tsx` يجلب الخطوط عبر `next/font/google` وهناك كذلك `@import Google Fonts` في `globals.css`. **نراجع التكرار والتحميل وCSS قبل الأداء**.
- CSS متراكم بملفات `ux-corrections.css` و`ux-student-surfaces.css` و`student-dashboard-corrections.css` و`globals.css` (الحجم التقريبي للأخير ~50KB). **المطلوب تصميم System tokens/components نظيف بعد مقارنة العرض** بدل إضافة ملف ترقيع خامس.
- **أصول V1 التعليمية المختارة**: 33 MP3 +23 WebP مساراتها مثبتة في مستودع GitHub، وفي بنك V2 `selected_from_v1_pending_owner_review` حتى يسمع/يشاهدها المختص. لا تخلطها مع تسجيلات أداء الطلاب الموجودة في التخزين الخاص.

**قرار:** الحفاظ على هوية هِمّة وملامحها المفيدة؛ تحسين الأداء/التنسيق لا يبرر حذف شخصية أو صورة مستخدمة. وفي الوقت نفسه لا نقلد كل Layout من V1 إذا لم يخدم قالب الدرس الجديد.

## 9. قائمة التطوير المرتبة وفق الاعتماد

**عند اعتماد P01، ابدأ P02 فقط:**
1. إعداد CI لـ`v2/*` بحيث يعمل Frontend + Backend + Security + Integration كاملًا، وتحديد سبب الفشل السابق لفحص gitleaks بدون نشر أسرار أو تعطيل الفحص.
2. إنشاء contracts typed لتوحيد `lesson/support/question/media/assessment` من المصدر، وتنفيذ validator يصل للـ300 بنود وفحص الصور/الصوت/الفيديو والحالات.
3. بناء compiler `authoring → immutable private release` وإصدار student DTO آمن واختبارات عدم التسريب.
4. تصميم DB runtime V2 نظيفة، migration متوافق مع نطاق جديد، واختبارات uniqueness/idempotency.
5. بناء MediaManifest/MediaProvider واختبار asset IDs واستبدال fixture دون تغيير صفحات.
6. تجهيز بيئة اختبار **غير إنتاجية** وبيانات طالب ومشرف اصطناعية؛ لا حاجة لتشغيل V1 أو أي بيانات شخصية من الإصدار القديم.
7. منع imports أو نشر Release ينتج سؤالًا يتطلب صوتًا/صورة/فيديو غير موجود بالبيئة المحددة؛ Staging يسمح Fixture مع وسم مرئي وحارس نشر.
8. كتابة Unit/Integration/Contract tests لفشل كل API وردود 401/403/409 وللتزامن وإعادة الإرسال، وارتباط كل سؤال بالمالك والمهارة الصحيحة.

**P03 لاحقًا:** بناء الشاشة والمشغل والتنقل، وليس في P02. **P04:** التفاعلات السبعة. **P05–P10:** التكيف والقبلي/البعدي والمشرف والصوت وE2E ثم الأصول الحقيقية، كما في خطة 09.

## 10. مخاطر معروفة لا يجوز إعلان إغلاقها في P01

| ID | الخطر | حالة الإثبات الحالية | الإغلاق في |
|---|---|---|---|
| K01 | فشل فحص Security في Quality Gate لـV1 | واجهة Actions تؤكد خطوة فشل، **لا تؤكد وجود سر مكشوف أو سبب محدد** | P02 قبل كود الإصدار |
| K02 | `v2/*` ليست ضمن workflow push triggers المعاينة | مؤكدة من `.github/workflows/ci.yml` | P02 |
| K03 | لا تجربة بصرية فعلية لتدفقات V2 | مؤكدة؛ V1 غير منشورة | P03/P09 |
| K04 | 56 أصل V1 مرشح يحتاج QA لغوي/بصري | موجودة كمواقع ملفات فقط؛ **ليس فحص محتوى الوسيط** | P07/P10 |
| K05 | 19 فيديو و14 صوتًا جديدًا غير متاح | `missing_new` في البنك | P10 |
| K06 | معايير `write_text` و`read_aloud` تحتاج تجارب مشرف | عقود مسودة لا تشغيل | P04/P08 |
| K07 | سياسة mastery/placement الجديدة لم تُعاير بعد | قواعد V1 مرتبطة بالمحتوى القديم | P05/P06 |
| K08 | قاعدة V2 وبيئة Staging لم تُنشآ | P01 تحليل فقط | P02 |
| K09 | إيقاف V1 لا يلغي التزامات حفظ بيانات أشخاص قديمة | حسب المالك لا يلزم ترحيلها | قبل أي حذف، مع مالك البيانات |

## 11. قرار بوابة P01

**يمكن قبول تصميم P01 إذا راجع المالك**: عقد البنك الآمن، سياسة DB جديدة للطلاب، مراحل Player/الدرس/التكيف، خطة الأصول والـCI، وفصل اختبار staging عن النشر الحقيقي.  
**قبول التصميم لا يعني نجاح CI أو E2E**؛ هذه مخرجات تنفيذ إلزامية في P02–P10. وأي تغيير في قرار architecture خلال التنفيذ يوثق بADR محدد ويُراجع قبل إضافة استثناءات.
