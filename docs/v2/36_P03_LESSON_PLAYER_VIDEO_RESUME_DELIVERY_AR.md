# هِمّة V2 — تسليم P03: مشغّل الدرس والفيديو والاستئناف

**التاريخ:** 2026-10-21؛ إغلاق الأدلة 2026-10-22
**الحالة:** `approved` — اعتمد المالك بعبارة «تم» في 2026-10-23؛ لا تفعيل محتوى ولا نشر
**المرجع:** اعتمد المالك P02 بعبارة «تم»؛ P03 تطوّر مشغل التعلم داخل منصة FastAPI/Next/SQLAlchemy نفسها.

## 1. النتيجة

أُنجز أساس P03 القابل لإعادة الاستخدام دون إدخال منطق أسئلة P04:

- خريطة 19 درسًا من الإصدار المرشح نفسه، 6/6/7، مع حالات `current/locked/done` ومعاينات تشغيلية للدروس `L1-01` و`L2-01` و`L3-03`.
- قالب رحلة واحد: `intro → teaching_video → guided_practice → independent_check → outcome`. قاعدة البيانات تحافظ مؤقتًا على اسم `video` الداخلي من migration 0015 ويحوّله عقد API إلى `teaching_video`؛ لا ترحيل مكسّر لمجرد تغيير الاسم.
- `VideoPlayer` واحد يدعم controls الأصلية للتشغيل/الإيقاف/seek/الصوت/captions، والاستئناف، replay، والتحميل/buffering/stalled/autoplay-blocked/error/ended، مع RTL والهاتف و`prefers-reduced-motion`.
- تقدم خادمي مثبت بإصدار المحتوى: المقدمة، موضع/مدة الفيديو، اكتمال المشاهدة، المرحلة، النسخة، وسجل أحداث محدود idempotent. لا تستخدم `localStorage` كمصدر حقيقة.
- فيديو MP4 قابل للتشغيل وترجمة VTT موسومان `TEST ONLY`؛ يقدمان Range، ويُمنع وصول الطلاب إلى المعاينة كلها في `trial/production`، ولا يغيران حالة الأصل من missing/pending إلى approved.
- صفحة مشرف قراءة فقط تعرض أصل الحقيقة: `0 ready / 56 pending / 33 missing`، مع فصل `89 test_only` في بيئة المعاينة عن اعتماد الوسائط.
- حد صريح عند `guided_practice`: لا زر تجاوز، لا درجة، ولا اعتبار الفيديو إتقانًا. الأنواع السبعة والتصحيح تبدأ فقط في P04 بعد الموافقة.
- أُغلق فحص المتصفح بوسيط MP4 حقيقي ولقطات 390/1440، وكشف الفحص سباقًا فعليًا عند جاهزية metadata من cache ثم صُحح واختُبر؛ لم يُستبدل ذلك بتوقيت أو mock لحدث الاستئناف.

## 2. السبب الجذري والمعالجة

| الفجوة المثبتة | موضع V1/P02 | السبب الجذري | معالجة P03 | ما يجب اختباره لاحقًا |
|---|---|---|---|---|
| نشاط V1 بلا مراحل درس أو فيديو | `student/activity/[id]` و`activity_runtime.py` | نموذج item/step لا يمثل intro/video/GP/IC | `v2_lesson_runtime.py` + LessonShell واحد، مع إبقاء مشغل V1 العامل | تكامل تفاعلات V1 داخل القالب في P04، لا حذفها |
| `LessonSession` لا يحفظ موضع الفيديو | `db/learning_models.py` / migration 0015 | P02 أنشأت pin/stage فقط | migration 0016 additive: intro/video position/duration/completion/events | PostgreSQL migration/drift/concurrency على SHA النهائي |
| URL fixture موجود بالعقد دون resource قابل للتشغيل | `v2_content/media.py` | P02 ثبت provider ولم ينفذ P03 player | MP4+VTT حقيقيان ومسار مصادق عليه وRange ووسم Test Only | slow 3G/expired/source reload في Browser gate |
| خلط جاهزية runtime باعتماد الأصل | MediaProvider candidate | fixture يجعل العرض ممكنًا لكنه ليس اعتمادًا | Inventory يفصل `source state` عن `runtime_state/test_only` | تبديل أصل إنتاج معتمد في P07/P10 |
| خطر مسار موازٍ للطالب | صفحات V1 الحالية | بناء player منفصل قد يكرر المنصة | رابط مرحلي داخل Dashboard الحالي، نفس auth/BFF/API/DB والهوية؛ candidate محجوب في البيئات المحمية | دمج CurrentAction النهائي تدريجيًا بعد P04–P06 |
| video ended قد يتحول إلى نجاح أكاديمي | لا عقد سابق | مشاهدة الفيديو ليست evidence | ended ينقل إلى GP فقط، ويتطلب ≥90% من المدة، ولا يكمل الدرس | mastery/support في P04/P05 |
| موضع محفوظ لا يُستعاد عند media cache السريع | `VideoPlayer.tsx` في تنفيذ P03 الأول | الاعتماد على handler React لـ`loadedmetadata` فقط يسمح بفوات الحدث قبل ربطه | listener أصلي داخل effect مع فحص `readyState` فوري، واختبار وحدة لحالة metadata الجاهزة | refresh/cache/device وتبديل المصدر في P09 |
| M09 يطلب Fixture محجوبًا عمدًا في `trial`، ثم seek غير ثابت لملف route-fulfilled | `v2-lesson-runtime.spec.ts` مع سياسة MediaProvider | اختبار UI الموجّه كان يمرر API mock لكنه ترك ملف الفيديو يعتمد على بيئة الخادم؛ وبعد عزله لم يضمن Chromium seekable range في fixture | تقديم MP4/VTT من Playwright route فقط، وتثبيت الزمن المرصود عند إرسال حدث checkpoint؛ بقي reload هو الذي يختبر الاستئناف الحقيقي، وبقي اختبار الخادم يثبت 503 في `trial/production` | إبقاء اختبار المنع وUI والاستئناف الحقيقي مفصولة في كل بوابة |

## 3. المحافظة على V1 والهوية

- لم تُحذف أو تُستبدل صفحات `/student/activity/[id]` أو `/student/session/[id]` أو التقارير والتسجيلات والتقوية والمكافآت.
- استخدمت شعارات هِمّة وشخصية الطالبة والخطوط والألوان والـRTL الموجودة؛ لا هوية أو تطبيق مستقل.
- بقيت Cookie/RBAC/BFF/Origin وحارس الطالب الحالي، وبقي المشرف داخل الـDashboard نفسه.
- بقيت حالات الصوت pending/rerecord والمكافآت ورحلة الطالب القديمة كما هي؛ طلب catalog الإضافي اختياري ويفشل دون تحويل البيانات الثانوية إلى صفر.
- لا `RETIRE_APPROVED` ولا حذف بيانات ولا تغيير بيئة نشر.

## 4. العقود والملفات

- Backend: `services/api/v2_lesson_runtime.py`، `db/learning_models.py`، migration `0016_v2_lesson_runtime.py`.
- Media: `services/api/test_fixtures/himma-v2-video-test-only.mp4` و`.vtt`؛ `MediaProvider` يعيد مسار P03 الصحيح.
- Student: `/student/learning-v2` و`/student/learning-v2/[sessionId]`، و`components/learning/VideoPlayer.tsx`.
- Admin: `/admin/v2-media` داخل تنقل لوحة المشرف الحالية.
- Tests: `test_v2_lesson_runtime.py`، `VideoPlayer.test.tsx`، `v2-lesson-runtime.spec.ts`، وتسجيله في CI/M09 و`TEST_OWNERSHIP.md`.

## 5. الأمن واتساق الحالة

1. كل endpoint طالب يتحقق من الطالب وملكية `student_id`؛ المشرف لا يستطيع تشغيل catalog الطالب، والطالب لا يستطيع فتح inventory.
2. `trial/production` يعيدان 503 للـcandidate؛ fixture لا يفتح ثغرة مستقلة عن هذا الحارس.
3. start/resume يثبت `content_release_id` ويرفض رحلة مثبتة على إصدار مختلف، ويمنع جلستين نشطتين.
4. الأحداث لها `(lesson_session_id,event_key)` فريد؛ ترتيب intro ثم video مفروض خادميًا.
5. `video_ended` لا يقبل موضعًا مبكرًا، ولا يغيّر `completed/mastery`، بل ينتقل إلى `guided_practice` فقط.
6. MP4/VTT خاصان بالمعاينة مع `private, no-store` و`X-Himma-Test-Only`، وبوابة P02 ما زالت ترفض fixture عند النشر.

## 6. الاختبارات

| البوابة | النتيجة الحالية |
|---|---|
| P03 Backend + P02 regression | PASS محلي: 20/20 |
| Frontend Jest | PASS: 12 suites / 47 tests |
| TypeScript / ESLint | PASS |
| Next production build | PASS؛ المسارات الجديدة مبنية |
| Backend full PostgreSQL + Alembic/drift | PASS على implementation SHA النهائي ضمن CI وM09؛ شمل migration/drift/seed واختبارات Backend |
| Playwright P03 | PASS في CI وM09: catalog 390، MP4 حقيقي مع Range، checkpoint ثم reload/resume، error/retry، وحد GP على 1440 |
| QA بصري لوسيط الاختبار | روجعت لقطات CI: catalog الهاتف، الاستئناف عند `0:05 / 0:06`، رسالة الخطأ وإعادة المحاولة، وحد GP على الديسكتوب؛ لا overflow أو قطع ظاهر في النطاق المصوّر |
| QA سمعي/تربوي للأصول النهائية | `NOT_VERIFIED` ومؤجل إلى P10؛ فيديو TEST_ONLY لا يعتمد صوتًا أو محتوى نهائيًا |

نجاح فيديو TEST_ONLY لا يصرّح بالنشر ولا يعتمد المحتوى تربويًا.

### 6.1 دليل الإغلاق على SHA التنفيذ

- implementation SHA: `35848eb99fba832563f853dbcfa3ab682deb6074`.
- M04 Responsive Gate: run `39716552940` — `success`.
- CI Quality Gate: run `39716552917` — `success`؛ Security/Backend/Frontend/Integration كلها ناجحة.
- M09 Release Readiness: run `39716552932` — `success`؛ شمل browser regression وPostgreSQL/object-storage backup/restore.
- الإخفاقات السابقة لم تُخفَ: run `39683069718` كشف تعارض بيئة `trial` مع Fixture، والدورات اللاحقة كشفت غياب Range الحتمي وخلل quick-audit الخارجي مع شجرة غير مبنية. عولجت الأسباب في الاختبار والـworkflow دون تعطيل fail-closed أو `npm audit`.
- Commit التوثيق الذي يلي هذا الدليل لا يغيّر Runtime؛ SHA أعلاه هو SHA التنفيذ الذي اجتاز البوابات.

## 7. المتبقي المقصود

- P04: Renderer للأنواع السبعة، GP hints/feedback، IC بلا كشف إجابة، الكتابة/القراءة والتسجيل، والتصحيح/المراجعة.
- P05: evidence/mastery/support والعودة إلى موضع الدرس.
- P06 وما بعدها: CurrentAction الكامل، التقارير/الإدارة المتكاملة، الأصول النهائية والـQA الشامل.
- P10: استبدال fixtures بفيديوهات الدروس الـ19 والأصوات/الصور النهائية بعد الاعتماد وإعادة جميع الاختبارات.

## 8. قرار المراجعة

`P03=approved` بقول المالك «تم» في 2026-10-23. بدأ P04 بعد ذلك واعتمد على هذا الأساس؛ لا نشر، ولا تفعيل للإصدار المرشح، ولا تعديل لبيانات إنتاج.
