# هِمّة V2 — تسليم P02: المحتوى والإصدارات والميديا وأساس الجلسة

**التاريخ:** 2026-10-20  
**الحالة:** `ready_for_review` — لا تفعيل محتوى، لا نشر، ولا بدء P03  
**المرجع:** P01 معتمدة كتدقيق مصدر؛ التنفيذ هنا يحدّث المنصة نفسها ولا ينشئ Backend أو CMS موازيًا.

## 1. النتيجة

أُغلق نطاق P02 برمجيًا على أساس واحد داخل FastAPI/Next/SQLAlchemy الحالي:

- Compiler حتمي يقرأ ملفات البنك الأربعة الخاصة ويمنع البناء ما لم تكن النتيجة بالضبط **300 سؤالًا، 19 درسًا، 12 دعمًا، 89 وسيطًا، 13 مهارة** مع التوزيعات والروابط الصحيحة.
- إصدار خاص immutable مرشح فقط: `himma-v2-authoring-0.3-draft+b78f8b01cdf0` وSHA-256 كامل `b78f8b01cdf00b9b0c9e311fb424d24c1bb286a0066fefb48fb6639235c2b085`.
- إسقاط Student API بقائمة سماح، لا يعيد `private_answer/correct_option_ids/rubric/reading_reference/origin_v1`، والتلميح مقتصر على `guided_practice`.
- Importer واحد idempotent يسجل metadata/media manifest فقط، لا ينسخ 300 سؤال إلى SQL، ولا ينشط الإصدار ولا يوافق عليه.
- `MediaProvider` واحد بحالات `ready/pending/missing`؛ fixtures موسومة `test_only=true` وممنوعة fail-closed في production ومن بوابة النشر.
- مخطط additive لـ`StudentJourney/LessonSession/LessonQuestionResponse` مع release pin، استئناف stage/step، جلسة نشطة واحدة، وsubmit key لمنع التكرار. أضيف pin اختياري لجلسات التقييم القديمة دون كسرها.

## 2. قرارات المحافظة وعدم الازدواج

| المجال | قرار P02 | ما بقي من V1 |
|---|---|---|
| التطبيق | وحدات داخل `services/api` وBFF الحالي | FastAPI/Next/Cookie/RBAC الحالي؛ لا خدمة موازية |
| المحتوى | release خاص compiled؛ SQL لحالة التشغيل والمراجع | جداول V1 باقية للتوافق، ولا حذف للمحتوى أو وظائف المشرف |
| التقييم | `/assessment/start` يملكه `assessment_retake`، و`finish` يملكه `assessment_completion` | retake/history/official attempt محفوظة مع إزالة الاعتماد على ترتيب mount |
| الوسائط | manifest/provider قابل للاستبدال | S3 والتسجيلات والمراجعة البشرية باقية؛ fixture ليست أصلًا نهائيًا |
| الهوية والصفحات | لا تغيير مرئي في P02 | جميع الأصول والصفحات والوظائف المسجلة في 25/26 محفوظة |

لا يوجد `RETIRE_APPROVED` جديد، ولا ترحيل أو حذف بيانات طلاب.

## 3. الملفات والعقود

- `services/api/v2_content/`: `contracts/compiler/projection/repository/importer/media`.
- `services/api/v2_content_api.py`: preview مصادق عليه للـcandidate؛ الطالب محجوب في trial/production حتى الاعتماد.
- `services/api/db/learning_models.py` وmigration `0015_v2_learning_foundation`.
- `services/api/register_v2_candidate.py`: dry-run افتراضي، و`--write` صريح للتسجيل الخامل فقط.
- `apps/web/src/app/api/proxySecurity.ts`: same-origin، 12MB، 30s، 413/503، request ID وبث response.
- `requirements.in` + `requirements.txt` المقفلة على Python 3.12، وتفعيل workflows على `v2/*`.

## 4. الأمن وحدود النشر

1. المصدر الكامل لا يُخدم كملف عام؛ endpoints تعيد DTO محددًا فقط.
2. الطالب لا يصل إلى candidate في `trial/production`، والمشرف لا يحصل عبر هذه endpoints على answer key.
3. `CORS_ORIGINS` إلزامية وصريحة في البيئات المحمية؛ production يقبل HTTPS فقط، وlocalhost HTTP مسموح في trial المحلي.
4. mutating requests ذات Origin مخالف/`cross-site` تُرفض في BFF وFastAPI.
5. BFF لا يحمل response كاملًا في الذاكرة، ويحفظ range/content/retry headers ويحوّل الانقطاع إلى 503.
6. fixture media لا تُقبل للنشر، والإصدار المرشح `is_active=false/status=candidate_not_approved`.

## 5. الاختبارات المنفذة

| البوابة | النتيجة |
|---|---|
| Compiler/dry-run | PASS؛ الأعداد والتوزيعات والـchecksum حتمية |
| اختبارات P02 المركزة | PASS: 24/24 بعد توحيد route ownership |
| Backend suite على SQLite معزولة | PASS: 928/928؛ التحذيرات deprecation فقط |
| Frontend TypeScript | PASS |
| Frontend Jest | PASS: 11 suites / 44 tests |
| Frontend ESLint | PASS |
| Python `pip-audit` / npm production audit | PASS؛ لا ثغرات معروفة |
| GitHub CI — Quality Gate | PASS على implementation SHA `5af288cb03b9817b11656d8b658874e189682ced`؛ backend/security/frontend/integration كلها ناجحة، run `39362979612` |
| GitHub M04 — Responsive Visual Gate | PASS على SHA نفسه، run `39362979618` |
| GitHub M09 — Release Readiness Gate | PASS على SHA نفسه؛ Browser regression واستعادة PostgreSQL وprivate object storage وعدم بقاء artifacts كلها ناجحة، run `39362979616` |

تحقق GitHub فعليًا من PostgreSQL عبر upgrade/downgrade/upgrade و`alembic check` وseed idempotency، ثم شغّل التكامل على PostgreSQL/Redis/MinIO. لم تعد نتيجة SQLite هي الدليل الوحيد.

أثناء الإغلاق كشف M09 خللًا في **عقد اختبار** الرحلة القديمة: كان يخلط بين فجوة ربط التقوية التي لها إجراء إسناد، وتصعيد فشل التحقق المحدود الذي له إشراف مختلف. فُصل المساران في `vertical-slice.spec.ts`، ثم قُيد محدد رسالة التصعيد لأن Next.js يضيف route-announcer آخر بدور `alert`. لم يتغير منطق المنتج أو بياناته بسبب هذا التصحيح، ونجحت الجولات الثلاث اللاحقة كاملة.

## 6. ما لم يُنجز عمدًا

- لا Lesson Player أو VideoPlayer أو واجهة جديدة؛ هذا P03 بعد الاعتماد.
- لا نشر/تفعيل release، ولا تحميل وسائط نهائية، ولا تغيير قاعدة منشورة.
- لا توقيع تربوي/مرئي/سمعي للبنك؛ حالة `draft/candidate_not_approved` محفوظة.
- لا ادعاء نجاح Browser visual/audio أو رحلات P03–P10.

## 7. قرار المراجعة

`P02=ready_for_review`. عند قول المالك «تم» فقط تصبح `approved` ويجوز بدء P03. إن لم تعتمد، يبقى المرشح خاملًا ولا يغيّر رحلة الطالب الحالية.
