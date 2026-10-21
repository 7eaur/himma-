# هِمّة V2 — تسليم P03: مشغّل الدرس والفيديو والاستئناف

**التاريخ:** 2026-10-21  
**الحالة:** `ready_for_review` — لا بدء P04، لا تفعيل محتوى، ولا نشر  
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

## 2. السبب الجذري والمعالجة

| الفجوة المثبتة | موضع V1/P02 | السبب الجذري | معالجة P03 | ما يجب اختباره لاحقًا |
|---|---|---|---|---|
| نشاط V1 بلا مراحل درس أو فيديو | `student/activity/[id]` و`activity_runtime.py` | نموذج item/step لا يمثل intro/video/GP/IC | `v2_lesson_runtime.py` + LessonShell واحد، مع إبقاء مشغل V1 العامل | تكامل تفاعلات V1 داخل القالب في P04، لا حذفها |
| `LessonSession` لا يحفظ موضع الفيديو | `db/learning_models.py` / migration 0015 | P02 أنشأت pin/stage فقط | migration 0016 additive: intro/video position/duration/completion/events | PostgreSQL migration/drift/concurrency على SHA النهائي |
| URL fixture موجود بالعقد دون resource قابل للتشغيل | `v2_content/media.py` | P02 ثبت provider ولم ينفذ P03 player | MP4+VTT حقيقيان ومسار مصادق عليه وRange ووسم Test Only | slow 3G/expired/source reload في Browser gate |
| خلط جاهزية runtime باعتماد الأصل | MediaProvider candidate | fixture يجعل العرض ممكنًا لكنه ليس اعتمادًا | Inventory يفصل `source state` عن `runtime_state/test_only` | تبديل أصل إنتاج معتمد في P07/P10 |
| خطر مسار موازٍ للطالب | صفحات V1 الحالية | بناء player منفصل قد يكرر المنصة | رابط مرحلي داخل Dashboard الحالي، نفس auth/BFF/API/DB والهوية؛ candidate محجوب في البيئات المحمية | دمج CurrentAction النهائي تدريجيًا بعد P04–P06 |
| video ended قد يتحول إلى نجاح أكاديمي | لا عقد سابق | مشاهدة الفيديو ليست evidence | ended ينقل إلى GP فقط، ويتطلب ≥90% من المدة، ولا يكمل الدرس | mastery/support في P04/P05 |

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
| Backend full PostgreSQL + Alembic/drift | ينتظر GitHub exact-SHA؛ اختبار SQLite للترحيل غير صالح تاريخيًا بسبب migration PostgreSQL قديمة تستخدم `ALTER TYPE` |
| Playwright P03 | الاختبار الحتمي مكتوب ومضاف للبوابتين؛ التشغيل المحلي تعذر لأن بيئة العمل منعت تنزيل Chromium (ملف 0MiB)، وليس نجاحًا مسجلًا |
| QA بصري/سمعي يدوي | `NOT_VERIFIED` حتى يتوفر Browser run/مراجعة بشرية؛ لا يُستنتج من Build |

تُحدّث هذه الفقرة بعد GitHub Actions على commit التنفيذ. نجاح فيديو TEST_ONLY لا يصرّح بالنشر ولا يعتمد المحتوى تربويًا.

## 7. المتبقي المقصود

- P04: Renderer للأنواع السبعة، GP hints/feedback، IC بلا كشف إجابة، الكتابة/القراءة والتسجيل، والتصحيح/المراجعة.
- P05: evidence/mastery/support والعودة إلى موضع الدرس.
- P06 وما بعدها: CurrentAction الكامل، التقارير/الإدارة المتكاملة، الأصول النهائية والـQA الشامل.
- P10: استبدال fixtures بفيديوهات الدروس الـ19 والأصوات/الصور النهائية بعد الاعتماد وإعادة جميع الاختبارات.

## 8. قرار المراجعة

`P03=ready_for_review`. لا تبدأ P04 قبل قول المالك «تم». لا نشر، ولا تفعيل للإصدار المرشح، ولا تعديل لبيانات إنتاج.
