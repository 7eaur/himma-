# هِمّة V2 — فحص P01-D للدرس والاختبارات والتفاعلات والوسائط

**التاريخ:** 2026-10-19

**الحالة:** `ready_for_review_source_only` — لا تشغيل أو تعديل كود/DB/نشر

**فرع العمل:** `v2/01-learning-foundation-20261007`

**HEAD المفحوص قبل التوثيق:** `e45f1176877ce5f6d69a192cc2fa073fd0bb07f4`

**مرجع V1:** `stage/02-content` عند `4ecb27590f7c19cbe7823804b9919d91000415ef`

## 1. الخلاصة التنفيذية

المشغل الحالي في V1 يحتوي أجزاء قوية يجب الحفاظ عليها: فصل DTO الطالب عن الإجابات، ترتيب خيارات آمن، صور مرتبطة بخيارها بمعرف صريح، صوت واحد قابل للإلغاء، تسجيل قراءة حقيقي، رفع خاص متحقق، idempotency، انتظار مراجعة محايد، وإعادة تسجيل تحفظ التاريخ. لكنه **ليس مشغل درس V2** ولا يدعم بنك V2 كاملًا.

الفجوات الحرجة المؤكدة:

1. لا يوجد `LessonShell` أو مراحل `intro → video → guided_practice → independent_check`، ولا عنصر `<video>` أو MediaProvider للفيديو.
2. بنك V2 ذو 300 بند غير موصول بالـcompiler/publisher الحالي؛ الإصدار الحالي ينشر 125 عنصر V1، ولا توجد إحالة برمجية إلى ملفات `docs/v2/content-bank/*_AUTHORING_BANK_DRAFT.json`.
3. `write_text` غير موجود في أنواع React أو طلبات/API/DB/طابور مراجعة الكتابة؛ البنود الـ21 غير قابلة للتنفيذ.
4. أربعة بنود L1 تحتاج صوتًا مستقلًا داخل كل خيار، بينما عقد asset الحالي يربط `option_id` بالصور فقط ولا يملك AudioOption UI.
5. المحاولتان والتلميح مطبقان على جولات التعلم كلها دون تمثيل `guided_practice` مقابل `independent_check`؛ قد يصل hint/إعادة المحاولة إلى دليل يفترض أنه مستقل.

القرار: **نطور نفس المنصة بمشغل درس وسؤال موحد وعقود موسعة، ونحتفظ بخدمات V1 الصحيحة.** لا ننشئ مشغلًا موازيًا دائمًا، ولا ننسخ منطق النشاط والتقييم الموجود حاليًا في صفحتين.

## 2. ما فُحص فعليًا

- واجهة التعلم: `apps/web/src/app/student/activity/[id]/page.tsx` واختباراتها وCSS.
- واجهة القبلي/البعدي: `apps/web/src/app/student/session/[id]/page.tsx` و`assessment-view`.
- تشغيل API: `assessment.py`, `assessment_view.py`, `activities.py`, `activity_runtime.py`, `learning_experience.py`.
- عرض المحتوى الآمن: `content_student_view.py`, `content_runtime.py`, `schemas.py`.
- الميديا والتسجيل: `media.py`, `storage.py`, `recordings.py`, `useAudioQueue.ts`.
- البيانات: ContentItem/Step/Option/AssetLink، Attempt/Response، ActivityStepResponse، AudioSubmission/Review، ContentRelease.
- compiler/publisher الحالي واختبارات content parity/integrity وPlaywright: `question-experience`, `media-fidelity`, `vertical-slice`, `w6-*`, وvisual QA.
- بنك V2 الأربعة: 300 بند و19 درسًا و12 دعمًا و89 media IDs، مع الفجوات المعتمدة.

**حد الإثبات:** قراءة مصدر ومقارنة Git فقط. لم تُشغّل اختبارات أو Browser QA أو ميكروفون/فيديو فعلي، ولم يُعتمد أي أصل جديد.

## 3. تصحيح ومقارنة V1 مع فرع V2

- نواة API التالية متطابقة بين V1 وHEAD المفحوص: `assessment.py`, `activity_runtime.py`, `content_student_view.py`, `content_runtime.py`, `media.py`, `storage.py`, `db/models.py`, `db/activity_models.py`, `useAudioQueue.ts`.
- تغيرت صفحة النشاط لإظهار `rerecord_available` بدل تصنيفه إكمالًا، وتغيرت صفحة التقييم لعرض stimulus مرجعي بعد refresh. أضاف `assessment_view.py` حل النص المرجعي المعتمد. أضيفت فلاتر `status=approved` إلى مسار الأنشطة في `activities.py`.
- `useAudioRecorder.ts` حُذف، لكن سجل التنظيف يثبت أنه كان غير مستدعى، والصفحتان تنفذان MediaRecorder داخليًا. الحذف ليس فقد وظيفة مثبتًا؛ **المشكلة الحالية هي ازدواج التنفيذ الحي** ويجب توحيده بعد اختبارات parity، لا استعادة ملف ميت.
- `vertical-slice.spec.ts` تغير فقط لقبول حالتي تعليق التكيف. لا يوجد دليل تشغيل حديث لـHEAD.

## 4. القدرات التي نحافظ عليها

| ID | القدرة الحالية | القرار | الدليل |
|---|---|---|---|
| LD-K01 | DTO الطالب لا يعرض `is_correct/private answer/source_text` | `KEEP` | `content_student_view.py`, `test_content_surface_parity.py` |
| LD-K02 | ترتيب عرض الخيارات منفصل عن ترتيب التصحيح، وربط الصور بـ`option_id` | `KEEP/GENERALIZE` | `presented_options`, `_align_choice_assets` |
| LD-K03 | صوت تشغيل واحد مع pause/resume وإلغاء stale promises | `KEEP` | `useAudioQueue.ts`, اختباراته |
| LD-K04 | تسلسل وبناء كلمة واختيار صورة/نص واستماع وقراءة | `KEEP/ADAPT` إلى الأنواع السبعة فقط مع سياسات V2 | صفحتا activity/session وscorers |
| LD-K05 | Media gap يمنع العرض/الإرسال ولا يصبح نجاحًا | `KEEP FAIL-CLOSED` | UI notices، رفض `declared_media_gap_skip` في route المالك |
| LD-K06 | تسجيل حقيقي ومعاينة وإعادة تسجيل قبل الإرسال | `KEEP/UNIFY` | MediaRecorder في الصفحتين |
| LD-K07 | تخزين خاص، prefix خاص بالطالب، تحقق الحجم/MIME، 10MB | `KEEP/HARDEN` | `storage.py`, assessment/activity upload |
| LD-K08 | idempotency للإجابة والرفع، وقيد عدم تكرار الاستجابة | `KEEP/EXTEND` | OperationIdempotency وunique constraints |
| LD-K09 | pending audio محايد ومراجعة بشرية وتاريخ rerecord append-only | `KEEP` | audio review state وAudioSubmission/Review |
| LD-K10 | القبلي/البعدي 30/30، تقدم، حفظ وخروج واستئناف | `KEEP/EVOLVE` لبنك V2 وإصداره | assessment routes/session page |
| LD-K11 | نص مرجعي لفهم المقروء يبقى بعد refresh | `KEEP` | `_reference_stimulus_text` في `assessment_view.py` |
| LD-K12 | سياق قصة صوتية يجب سماعها قبل الأسئلة | `KEEP/EVOLVE` وحفظه خادميًا ضمن الدرس | `context_intro`, اختبار activity page |
| LD-K13 | Preview المشرف يقرأ نفس عرض الطالب مع إجابة منفصلة readonly | `KEEP` | `content_preview.py`, parity tests |
| LD-K14 | هوية هِمّة والشخصية والنص العربي وRTL وحالات loading/error | `KEEP/REFINE` | الصفحتان وCSS والأصول |

لا يوجد قرار `RETIRE_APPROVED` لأي قدرة. التفاعلات التاريخية الإضافية (`choose_many`, `memory_sequence`, `timed_read_aloud`...) تُراجع كقدرات داخلية أو تحول آمن، ولا تُحذف قبل التأكد من عدم احتياج بنك/تقارير V1 لها.

## 5. تغطية أنواع بنك V2 الحالية

| النوع | العدد | حالة Runtime الحالية | القرار |
|---|---:|---|---|
| `choose_one` | 107 | مدعوم نصيًا | إعادة استخدام renderer/scorer مع role/evidence V2 |
| `listen_choose_one` | 52 | صوت prompt واحد/طابور مدعوم | الحفاظ وإضافة حالات buffer/expired/option audio |
| `sequence` | 45 | مدعوم بالنقر والترتيب، نص/صور | الحفاظ؛ اختبار عدم كشف ترتيب الحل والوصول |
| `build_word` | 9 | مدعوم كترتيب عناصر | الحفاظ؛ عدم إظهار الهدف النهائي قبل الإجابة |
| `choose_image` | 4 | مدعوم بربط صورة→option صريح | الحفاظ؛ alt/aria لا يكشف التصحيح |
| `read_aloud` | 62 | تسجيل/رفع/مراجعة موجودة | توحيد recorder وربطه بـLesson/Evidence V2 |
| `write_text` | 21 | **غير مدعوم** في UI/API/DB/review | بناء input عربي + draft + submission + human review/rubric |

**صوت الخيار:** البنود `L1-01-GP-02`, `L1-01-GP-04`, `L1-01-IC-A01`, `L1-01-IC-A02` تحمل Audio media داخل الخيارات. العقد الحالي يضيف `option_id` للصورة فقط؛ لذلك لا يمكنه عرض زر تشغيل مستقل لكل خيار. ويظل `AUD-L1-L` أصلًا ناقصًا ضمن هذه المجموعة.

## 6. سجل الفجوات والأسباب الجذرية

| ID/أولوية | مكان V1 ووظيفته | القصور/السبب الجذري | هدف V2 والحفاظ | اختبار الإغلاق |
|---|---|---|---|---|
| LD01 `P0` | activity يشغل ContentItem/steps | لا Lesson entity/stages؛ بنية V1 نشاط من جولات | `LessonShell` واحد ومراحل خادمية وإصدار مثبت، مع إدماج renderer الحالي | استئناف كل مرحلة و19 درسًا كاملًا |
| LD02 `P0` | لا `<video>`؛ `media.py` audio/image فقط | لا Player ولا video contract/provider | VideoPlayer reusable وMediaProvider و`video_media_id`/manifest/TEST_ONLY guard | loading/play/pause/seek/captions/stall/expired/resume/ended |
| LD03 `P0` | publisher الحالي ينشر 125 عنصر V1 | بنك V2 الأربعة غير مستورد برمجيًا؛ لا parser/schema له | compiler/importer واحد للـ300 و19/12، immutable release + dry-run | 300 بلا فقد/تكرار/checksum والإطلاق يرفض draft |
| LD04 `P0` | Interaction unions/requests/models | `write_text` غائب بالكامل | TextResponse/Review model وtextarea عربي، مسودة، rubric سري، pending/graded/rewrite | 21 بندًا، refresh/device، review history، no auto-grade |
| LD05 `P0` | `step_assets` يربط option للصور فقط | لا هوية صوت لكل خيار ولا AudioOption component | media slot عام `option_id` للصوت/الصورة وزر تشغيل منفصل عن زر الاختيار | البنود الأربعة، تبديل سريع، missing/buffer، لا transcript كاشف |
| LD06 `P0` | `MAX_STEP_ATTEMPTS=2` على كل core step | لا role لـguided practice/independent check؛ hint عام | Question policy حسب role: تدريب بتلميح/feedback، check بلا hint؛ evidence يفصل الاثنين | نفس السؤال في GP/IC، لا hint/evidence contamination |
| LD07 `P1` | أول خطأ يظهر hint؛ ثاني خطأ ينتقل | لا correct-model/fresh guided retry كما في بنك V2، ولا feedback state واضح | Outcome/feedback policy خادمية لا تكشف check answer، وتطبق نموذج التدريب المعتمد | خطأ أول/ثان/صحيح ولقطات وحفظ attempts |
| LD08 `P1` | activity وsession يكرران renderer/MediaRecorder/media mapping | نمو تاريخي لصفحتين كاملتين | Shell منفصل للسياسة، ومكونات مشتركة `QuestionRenderer/Recorder/MediaSlot`; إزالة النسخ بعد parity | component contract + assessment/lesson E2E |
| LD09 `P1` | context intro seen في `sessionStorage` | الحفظ محلي للتبويب وليس تقدمًا خادميًا | LessonProgress server event idempotent؛ local UI cache فقط | refresh/tab/device وعودة بعد logout |
| LD10 `P1` | ContentRelease منفصل، item يحمل version نصيًا، session بلا release_id | لا pinning علائقي؛ assessment queries لا تقيد status/release | release FK/pin على Lesson/AssessmentSession وكل selection من active approved release | release N→N+1 أثناء جلسة، draft/stale exclusion |
| LD11 `P1` | assessment `get_next/progress` يرشح kind فقط | قد يعد/يختار row draft أو قديم إذا وجد؛ activity أصلح `status=approved` | query من release pinned + approved؛ fail closed عند نقص 30 | حقن draft/old version ولا يظهر أو يدخل العدد |
| LD12 `P1` | رفع ثم submit بمفتاحين محفوظين في sessionStorage | بعد نجاح الرفع وفشل submit قد يبقى object؛ إعادة تسجيل بمفتاح upload نفسه تصطدم بمحتوى مختلف | UploadIntent/Submission transaction أو token idempotent مع cleanup/expiry ومفتاح جديد عند إعادة التسجيل المقصودة | 503/timeout بين المرحلتين، retry نفس الملف/ملف جديد، orphan cleanup |
| LD13 `P1` | MediaRecorder inline بلا مدة قصوى/UI format matrix | تسجيل طويل قد يتجاوز 10MB؛ اختلاف codecs/browser غير مفسر | recorder موحد بحد زمن/حجم، format negotiation، permission/device/error recovery | deny/revoke/no device/Safari-Chrome/oversize/background |
| LD14 `P1` | 62 قراءة لها AudioReview؛ 21 كتابة بلا queue | نموذج المراجعة خاص بالصوت | ReviewTask عام أو WritingReview متكامل مع المشرف والتنبيهات والتقارير | pending/approve/rewrite/audit/concurrent reviewers |
| LD15 `P1` | `media.py` يبني index من ملفات repo عند import | ليس versioned provider ولا video/signed URL/status lifecycle | MediaManifest DB/release + provider fixture/real، metadata وhealth/cache policy | missing/pending/ready/failed، restart/storage outage |
| LD16 `P1` | V1 feedback assets موجودة؛ effects يصدر click/listen tones فقط | feedback التعليمي الصحيح/الخطأ غير موصول، وقد يخلط الحكم بالمكافأة إن أضيف عشوائيًا | Feedback policy للتدريب فقط، preference صوت/حركة، لا حكم مبكر للصوت/الكتابة/check | correct/wrong/pending، mute/reduced motion، no overlapping audio |
| LD17 `P1` | assessment/session نتيجة واحدة للقبلي والبعدي | نص “المسار الأنسب/مستواك” يعاد للبعدي | Outcome مميز حسب session_type، يحافظ على النتائج ولا يعيد تسكين الطالب | pre/post copy + score/placement rules |
| LD18 `P1` | API errors غالبًا نصوص 409 وUI يعرض detail | لا error taxonomy لميديا/محتوى/جلسة/مراجعة | Problem codes آمنة مع Retry/Back/Resume؛ request-id | 404/409/422/500/503 وoffline/expired media |
| LD19 `P2` | progress track يحمل aria-label فقط وصور eager كثيرة | semantics/perf لكل الحالات غير مثبتة | progressbar values، focus/live، lazy/priority حسب LCP، touch/zoom | axe/keyboard/200%/slow 3G و360–desktop |
| LD20 `P1` | E2E قوي تاريخيًا لـV1 125 عنصرًا | لا suite للـ300/Video/write_text/option audio/فصل GP-IC، ولا run على HEAD | matrix حديثة من بنك V2 وfixtures مع exact SHA | D-T01–D-T24 أدناه |

## 7. قرار المكونات والمسؤوليات المستهدف

```text
Student Route Shell
  └─ LessonShell / AssessmentShell (سياسة وتقدم فقط)
      ├─ StageRenderer (intro | video | practice | check)
      ├─ QuestionRenderer (الأنواع السبعة)
      │   ├─ MediaSlot / OptionMedia
      │   ├─ ReadingRecorder
      │   └─ WritingInput
      └─ Outcome / PendingReview / RecoverableError

Server
  ContentRelease → Lesson/Question/MediaManifest
  LessonSession/AssessmentSession (release pinned)
  Response/Evidence → ReviewTask → Adaptation
```

- `QuestionRenderer` يعرض فقط؛ التصحيح والسياسة والانتقالات في الخادم.
- AssessmentShell يمنع hint/feedback الكاشف، بينما LessonShell يطبق policy التدريب.
- نفس MediaSlot وRecorder وWritingInput يخدم الدرس والقبلي/البعدي والدعم؛ لا نسخ كود.
- لا تغيير أسماء دوال V1 السليمة دون ضرورة؛ تنقل المسؤولية تدريجيًا مع adapters مؤقتة واختبارات parity، ثم يزال المسار المكرر.

## 8. مصفوفة الاختبارات المطلوبة

| ID | السيناريو | النوع | الحالة |
|---|---|---|---|
| D-T01 | استيراد 300 و19 درسًا و12 دعمًا والأعداد السبعة | compiler/contract | `NOT_VERIFIED` |
| D-T02 | لا private answer/rubric/reference صوتي سري في Student DTO | security contract | V1 جزئي؛ V2 `NOT_VERIFIED` |
| D-T03 | intro/video/practice/check resume من الخادم | integration/E2E | غير منفذ |
| D-T04 | فيديو: play/pause/replay/seek/volume/captions/ended | component/E2E | غير منفذ |
| D-T05 | فيديو: autoplay blocked/stall/404/expired/slow 3G/rotation | E2E/network | غير منفذ |
| D-T06 | fixture `TEST_ONLY` يعمل في staging ويمنع production | release/security | غير منفذ |
| D-T07 | choose_one نصي | unit/API/E2E | V1 موجود؛ V2 `NOT_VERIFIED` |
| D-T08 | listen_choose_one prompt | unit/E2E/audio | V1 جزئي؛ V2 `NOT_VERIFIED` |
| D-T09 | أربعة option-audio cards | component/API/E2E | غير منفذ |
| D-T10 | sequence نص/صور دون كشف الترتيب | unit/E2E/axe | V1 جزئي |
| D-T11 | build_word دون إظهار الهدف | unit/E2E | V1 جزئي |
| D-T12 | choose_image semantic mapping وalt آمن | contract/visual/AT | V1 جزئي |
| D-T13 | read_aloud permission/record/preview/upload/retry | browser/API | V1 جزئي؛ لا run حديث |
| D-T14 | write_text عربي/draft/submit/pending/review/rewrite | full-stack E2E | غير منفذ |
| D-T15 | GP hint بعد الخطأ وسياسة ثاني خطأ | policy/E2E | V1 behavior جزئي، عقد V2 غير منفذ |
| D-T16 | IC/pre/post بلا hint ولا answer feedback | security/E2E | assessment V1 جزئي؛ lesson check غير منفذ |
| D-T17 | pending reading/writing لا يحسب إتقانًا | API/adaptation/report | audio V1 جزئي؛ writing غير منفذ |
| D-T18 | media gap لا يتجاوز ولا يحتسب، مع recovery بعد الربط | API/E2E | V1 جزئي؛ V2 غير منفذ |
| D-T19 | إصدار N يبقى مثبتًا عند نشر N+1 | DB/integration | غير منفذ |
| D-T20 | draft/old content لا يدخل assessment count/selection | API/security | غير مغطى كفاية |
| D-T21 | upload نجح ثم submit فشل، retry/cleanup بلا تضارب | integration | غير مغطى كفاية |
| D-T22 | الهاتف/اللوحي/الديسكتوب والنص الطويل/keyboard/zoom | visual+axe | حالات V1 جزئية فقط |
| D-T23 | pretest/posttest 30/30 وreference refresh ونتيجتان مختلفتان | E2E | V1 جزئي؛ V2 `NOT_VERIFIED` |
| D-T24 | لا ازدواج renderer/recorder، وparity لجميع وظائف V1 | architecture+regression | غير منفذ |

## 9. ما لم يُعتبر منجزًا

- لا Player ولا فيديو fixture حقيقي ولا subtitles.
- لا import أو publish لبنك V2.
- لا `write_text` ولا مراجعة كتابة.
- لا option audio renderer.
- لا فصل تنفيذي بين GP وIC.
- لا تشغيل اختبارات أو screenshots أو فحص ميكروفون/صوت/فيديو.
- لا اعتماد جودة الأصول الـ56 المرشحة، ولا توفير الـ33 الناقصة.

## 10. حالة التسليم

- `P01-C = approved_source_audit` باعتماد المالك «تم» في 2026-10-19؛ اختبارات C المؤجلة لم تصبح ناجحة بهذا الاعتماد.
- `P01-D = ready_for_review_source_only` مع الفجوات `LD01–LD20`.
- `P01` الكلية ما تزال `in_progress`.
- **P01-E وP02 لم تبدأا**، ولا يبدأ أي منهما قبل اعتماد مستقل «تم».
