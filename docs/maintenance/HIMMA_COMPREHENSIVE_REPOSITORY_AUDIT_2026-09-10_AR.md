# منصة همة — المراجعة الشاملة للمستودع والمنصة

**التاريخ:** 2026-09-10  
**الحالة:** AUDIT IN PROGRESS — لا دمج ولا نشر  
**مستودع الحقيقة:** `7eaur/himma-`  
**فرع الأساس التنفيذي:** `integration/canonical-content-2026-09-08`  
**HEAD الأساس عند بدء المراجعة:** `7cb2192b0c31bc85dcf98a470023e9cc6f1598e0`  
**فرع سجل المراجعة:** `audit/comprehensive-repository-review-2026-09-10`

---

## 1. الهدف

هذه مراجعة شاملة تسبق الإغلاق النهائي والدمج والنشر. الهدف ليس جمع أخطاء سطحية ولا حذف ملفات قديمة لمجرد أن أسماءها تبدو كترقيعات؛ بل فهم البنية الحالية، وتتبع سبب كل طبقة تاريخية أو Repair/Overlay/Recovery، وتحديد مالك الحقيقة الحالي، ثم بناء خطة صيانة جذرية تحافظ على السلوك الصحيح والتاريخ الأكاديمي.

النتيجة المطلوبة من هذه المرحلة هي **سجل فجوات كامل ومثبت بالأدلة** يغطي Backend وFrontend وUX/UI وقاعدة البيانات والمحتوى والتكيف والصوت والشارات والوسائط والأمان والاختبارات والفروع والاستعداد للنشر. لا تبدأ موجات التحسين والدمج إلا بعد نضج هذا السجل.

---

## 2. قواعد المراجعة غير القابلة للتجاوز

1. Git الحالي هو الحقيقة التنفيذية إذا كان أحدث من ملفات التسليم السابقة.
2. لا Docker في أي مرحلة.
3. لا Repair/Overlay Runtime جديد لحل مشكلة حالية.
4. أي ترقيع/طبقة قديمة تُفهم أولًا: لماذا أضيفت؟ ما الذي ما زال يعتمد عليها؟ وما البديل الجذري؟ ثم فقط تُدمج أو تُزال.
5. لا حذف للتاريخ الأكاديمي أو معرفات الإجابات القديمة بهدف التنظيف.
6. لا Merge ولا Deploy أثناء المراجعة.
7. فرع نموذج الصوت/الذكاء الاصطناعي المؤقت مستبعد من الدمج حتى اعتماد مستقل.
8. لا استبدال صورة بصورة «مشابهة» فقط لتقليل التكرار؛ يجب أن يكون التطابق الدلالي صحيحًا ومعتمدًا.
9. Railway هو هدف النشر النهائي بعد اكتمال الصيانة والدمج والاختبارات، وليس أثناء مرحلة التدقيق.
10. كل نتيجة مهمة تُسجل هنا قبل التحسين، مع حالة واضحة: `OPEN / VERIFIED / PLANNED / FIXED / ACCEPTED`.

---

## 3. مراحل المراجعة

### A00 — خط الأساس والحوكمة وCI
- تثبيت HEAD المرجعي.
- فحص default branch وحالة الحماية ومسارات CI.
- توثيق ما نجح فعليًا وما فشل فعليًا.
- منع الخلط بين فشل Runner وفشل الكود.

### A01 — Backend والـRuntime والـRoutes
- مالك كل Route فعلي.
- طبقات `activities.py` / `activities_v4.py` / `activity_runtime.py`.
- Services التي أصبحت Compatibility Layers.
- مسارات التقييم، التعلم، التقوية، التقارير، المراجعة الصوتية، التكيف.
- تكرار المنطق، circular ownership، dead/reachable code.

### A02 — قاعدة البيانات والمحتوى والـSeeds/Migrations
- canonical publisher الحالي.
- كل Seed/Repair/Projection تاريخي.
- تصنيف كل ملف: Runtime / Migration input / Test-only / Dead candidate.
- Alembic roundtrip، drift، idempotency، التاريخ الدائم.

### A03 — الصوت والتحليل والتكيف
- Pending/graded/rerecord lifecycle.
- عدم احتساب الصوت غير المراجع أكاديميًا.
- إعادة التسجيل والتاريخ غير القابل للطمس.
- ASR/reference-guided pipeline وحدود الثقة البشرية.
- promotion/completion gates.

### A04 — Frontend وUX/UI
- Design System الفعلي.
- توحيد لوحة الإدارة.
- فحص كل صفحة Admin على الهاتف والتابلت والديسكتوب.
- صفحة تفاصيل الطالب خصوصًا.
- صفحة الطالب والاختبارات والأنشطة والتقوية والتقارير.
- accessibility، states، empty/loading/error، RTL.

### A05 — نظام الشارات والمكافآت
- Models/Migrations.
- قواعد منح الشارة والمكافأة.
- idempotency وعدم التكرار.
- API.
- Student UI وAdmin visibility.
- ربط الحزمة البصرية المعتمدة.
- Unit/Integration/E2E.

### A06 — الصور والوسائط
- جرد كل Asset موجود.
- جرد كل Asset مستخدم فعليًا.
- Orphans / unused / repeated.
- التكرار الصحيح دلاليًا مقابل التكرار المشكوك فيه.
- استخدام صورة غير مستخدمة بدل صورة مكررة فقط إذا كان المعنى مطابقًا.
- الصور المولدة، القصص، audio manifests، serving contracts.

### A07 — الأمن، الأداء، الوصولية، المراقبة
- Auth/roles/IDOR/rate limits/secret handling.
- dependency/security gates.
- performance N+1 / payload / cache / bundle / images.
- WCAG/keyboard/focus/contrast/reduced motion.
- readiness/logging/health/operational diagnostics.

### A08 — الاختبارات والرحلة الكاملة
- Backend / Frontend / Security.
- Migration roundtrip.
- Seed twice.
- Media/audio.
- Integration/E2E.
- Pretest → Placement → Learning → Reinforcement → Posttest → Reports.
- Mobile flows.

### A09 — مراجعة الفروع والتوحيد
- مقارنة جميع الفروع مع الفرع النهائي المرشح.
- `already-contained` / `unique-relevant` / `obsolete` / `experimental` / `archive-candidate`.
- استبعاد فرع نموذج الصوت الاصطناعي المؤقت.
- لا دمج أعمى؛ كل فرق يفهم قبل الدمج.

### A10 — موجات الصيانة والتحسين
تُبنى بعد اكتمال A00–A09، وتنفذ حسب الخطورة والاعتماديات، وليس حسب أسماء الملفات.

### A11 — Final Release Gate ثم Railway
- جميع البوابات خضراء فعليًا.
- توحيد الفرع النهائي.
- Backup/rollback plan.
- إعداد Railway production.
- migrations + canonical seed/readiness.
- smoke/E2E بعد النشر.
- التحويل من نسخة التطوير الحالية إلى النسخة النهائية فقط بعد الإثبات.

---

## 4. الحالة المثبتة عند بداية المراجعة

### 4.1 CI الحقيقي للـHEAD `7cb2192...`
Run: `34419490966`

- Security: **PASS**.
- Frontend: **PASS** — install/typecheck/ESLint/unit/build.
- PostgreSQL native startup: **PASS**، بدون Docker.
- canonical catalog/release validation: **PASS**.
- Alembic upgrade → downgrade base → upgrade: **PASS**.
- `alembic check`: **PASS**.
- canonical seed twice/idempotency على PostgreSQL: **PASS**.
- Backend pytest: **FAIL** — `823 passed, 2 failed`.
- Integration/E2E: **لم يبدأ** لأن Backend فشل.

الفشلان الحاليان مسجلان أدناه كفجوتين منفصلتين، ولا يعنيان أن المنظومة الأساسية كلها فاشلة.

---

## 5. سجل الفجوات الأولي

| ID | المجال | الشدة | الحالة | الملخص |
|---|---|---:|---|---|
| AUD-CI-001 | CI | P1 | OPEN | Backend فيه فشلان من 825، ولذلك Integration/E2E لم يعمل على هذا HEAD. |
| AUD-BE-001 | Runtime | P2 | VERIFIED | ثلاث طبقات Activities ما زالت مترابطة: `activity_runtime` يعتمد على `activities_v4` و`activities`؛ Router العام الحالي واحد فقط لكن ملكية الخدمة موزعة تاريخيًا. |
| AUD-BE-002 | Seeds | P2 | VERIFIED | المسار الحالي `seed_all` canonical ونظيف، لكن ملفات Seed/Projection/Correction تاريخية كثيرة ما زالت موجودة ويجب تصنيف اعتمادياتها قبل الإزالة. |
| AUD-BE-003 | Audio view | P1 | VERIFIED | عداد `pending_audio_reviews` في learning-experience يمكن أن يرجع 0 مع وجود جولة صوت Pending إذا كانت محاولة العنصر نفسه تحتوي جولة أخرى قابلة للتنفيذ. |
| AUD-BE-004 | Legacy test path | P2 | VERIFIED | اختبار Recovery لـPRE-Q05 يستخدم `seed.run_seed()` القديم 105 بدل canonical publication؛ لذلك يرى 3 صور بينما العقد الحالي المعتمد يحتوي 4. هذا يكشف بقاء مسار اختبار/Seed تاريخي، وليس نقصًا في canonical release الحالي. |
| AUD-FE-001 | Admin UI | P2 | VERIFIED | Design System إداري مشترك موجود ومستخدم جيدًا في عدة صفحات، لكن صفحة تفاصيل الطالب تبني معظم البطاقات/header/stats/layout بنفسها خارج `AdminUI`. |
| AUD-FE-002 | Mobile | P1 | VERIFIED | صفحة تفاصيل الطالب تستخدم `minmax(320px, 1fr)` مع قواعد هاتف محدودة؛ تحتاج مراجعة 320/360/390/430px خاصة للصفوف والأزرار والبطاقات وعدم overflow. |
| AUD-FE-003 | Admin UI | P2 | IN PROGRESS | يلزم Matrix لكل Route إداري لتحديد مستوى استخدام AdminUI والتكرار والـresponsive states. |
| AUD-BADGE-001 | Badges | P1 | IN PROGRESS | يجب إثبات نظام الشارات end-to-end: schema → award rules → API → UI → assets → tests. لا نحكم بأنه ناقص قبل إكمال الجرد. |
| AUD-MEDIA-001 | Images | P2 | IN PROGRESS | يلزم جرد referenced/unreferenced/repeated assets ومقارنة التكرار دلاليًا قبل أي استبدال. |
| AUD-GIT-001 | Branch governance | P1 | VERIFIED | `default_branch` الحالي ليس فرع التكامل الحديث؛ يحتاج حسم بعد مراجعة الفروع وقبل الإصدار النهائي، لا تغيير الآن. |
| AUD-GIT-002 | Branches | P1 | IN PROGRESS | المستودع يحتوي عددًا كبيرًا من فروع stage/integration/codex/feature؛ يلزم تصنيف كامل قبل الدمج والتنظيف. |
| AUD-REL-001 | Release | P0 | OPEN | لا نشر ولا استبدال نسخة Railway الحالية قبل إكمال التدقيق والتحسين والتوحيد والبوابات النهائية. |

---

## 6. تفاصيل الفجوات المثبتة حتى الآن

### AUD-BE-001 — سلسلة Runtime تاريخية للأنشطة

`main.py` يركب Router الأنشطة من `activity_runtime.py`، وهذا يمنع امتلاك Route عام مزدوج. لكن `activity_runtime.py` ما زال يستورد خدمات من `activities.py`، ويستورد helpers من `activities_v4.py`، والأخير بدوره يعتمد على `activities.py`.

**الاستنتاج:** هذه ليست ثلاثة Routers فعالة متعارضة الآن، لكنها ثلاث أجيال تنفيذية متداخلة. حذف القديم مباشرة خطر لأنه ما زال dependency حقيقيًا.

**خطة المعالجة لاحقًا:**
1. Dependency map لكل helper.
2. فصل service primitives المستقرة إلى modules ذات أسماء وظيفية واضحة.
3. إبقاء Router واحد.
4. نقل الاختبارات إلى المالك الجديد.
5. إزالة router declarations/compatibility modules التي تثبت عدم حاجتها فقط بعد parity tests.

### AUD-BE-002 — Seed/Projection تاريخي موجود بعد التوحيد

`seed_all.py` الحالي ينشر الـ125 عنصرًا عبر canonical publisher ولا يشغل repair/correction projection chain بعد النشر. هذه نقطة إيجابية.

مع ذلك ما زالت ملفات مثل `seed_student_choice_corrections.py` و`seed_student_experience_v2.py` و`seed_learning_posttest_projection_runtime.py` وغيرها في الشجرة.

**لا تُحذف الآن.** يجب أولًا معرفة هل كل واحد:
- مصدر migration تاريخي لا يزال compiler يعتمد معناه بشكل غير مباشر،
- Test fixture/reference،
- Tool إداري قديم،
- أو dead code فعلي.

### AUD-BE-003 — عداد Pending Audio غير شامل

الفشل الحقيقي:
`TestLearningAudioRuntime.test_uploaded_audio_stays_academically_pending_but_student_can_continue`

المتوقع: `pending_audio_reviews == 1`، الفعلي: `0`.

السبب المرئي في التصميم الحالي: `navigation_target()` يجمع `pending_review_count` فقط عندما لا يجد خطوة actionable في المحاولة، لكنه قد يرجع خطوة أخرى من نفس العنصر قبل إضافة حالة الـpending إلى العداد. بالتالي اختيار «ما هي الخطوة التالية؟» أصبح أيضًا مصدر عداد الجلسة، وهما مسؤوليتان مختلفتان.

**اتجاه الحل الجذري لاحقًا:** فصل session review summary عن navigation resolver؛ الـnavigation يختار الهدف فقط، والعداد يأتي من summary شامل لأحدث AudioSubmission لكل response.

### AUD-BE-004 — Recovery test ما زال يبني عالمًا قديمًا

الفشل الحقيقي:
`test_listen_choose_image_restores_audio_and_clickable_image_mapping`

العقد canonical الحالي لـPRE-Q05 يثبت أربع صور، لكن helper الاختبار `_seed_session_with_pending_item` يشغل `seed.run_seed()` التاريخي الذي ينشئ baseline 105 قبل canonical publication؛ لذلك يظهر `VOC-01/02/03` فقط.

**الاستنتاج:** هذه إشارة مهمة للتنظيف: بعض اختبارات Recovery لا تختبر runtime الحالي أصلًا. يجب إعادة تصنيفها إلى migration compatibility أو تحديثها لتنشئ canonical state، ثم إزالة اعتمادها على seed قديم إذا لم يعد له مسار إنتاجي مشروع.

### AUD-FE-001 / AUD-FE-002 — صفحة تفاصيل الطالب

المسارات:
- `apps/web/src/app/admin/(dashboard)/students/[id]/page.tsx`
- `student-detail.module.css`

بينما صفحات مثل قائمة الطلاب والتقارير تستخدم `AdminPage/AdminPageHeader/AdminPanel/AdminResponsiveTable/AdminMobileCard/AdminAction`، صفحة التفاصيل تستخدم فقط جزءًا صغيرًا من النظام المشترك ثم تعيد بناء Header/Cards/Stats/Rows/Modal/Layout محليًا.

المشكلة ليست مجرد «شكل مختلف»؛ بل خطر drift في spacing/radius/states/mobile behavior عند أي تحديث لاحق.

كما أن `.twoCol` يعتمد حدًا أدنى 320px لكل عمود، وتحتاج الصفحة اختبارًا حقيقيًا عند 320/360/390/430px؛ ويجب فحص صفوف المشاركين/الجلسات/actions/modals حتى لا تبقى مرونة الصفحة محصورة في تعديل الـheader فقط.

---

## 7. ما تم التحقق منه إيجابيًا ولا يجب كسره

1. Router الأنشطة العام الحالي له مالك واحد في `main.py`.
2. canonical content release الحالي = 125 عنصرًا.
3. canonical seed مرتين على PostgreSQL أعطى نفس release/projection والدورة الثانية بلا churn.
4. 44 مهارة و824 خيارًا و265 asset links في snapshot الحالي.
5. migrations roundtrip وdrift gate نجحا.
6. Frontend typecheck/lint/unit/build خضراء في التشغيل الحالي.
7. Security gates خضراء.
8. اختبارات حدود التكيف مع الصوت pending/promotion والـgraded evidence نجحت.
9. media canonical guard والـgenerated sequence asset tests نجحت.
10. صفحات Admin مثل students list وreports لديها بالفعل responsive table/mobile-card pattern قابل للتعميم بدل اختراع نظام جديد.

---

## 8. سياسة الصور أثناء المراجعة

عند اكتمال A06 سيُنتج جدول لكل Asset:

`asset_id | file | semantic label | usages | use_count | current locations | orphan? | duplicate semantics? | candidate replacement?`

القواعد:
- إذا كانت الصورة المكررة تمثل نفس الشيء دلاليًا، التكرار قد يكون صحيحًا.
- إذا كانت الصورة الواحدة تستخدم لمعنيين مختلفين، تُرفع كفجوة.
- إذا توجد صورة غير مستخدمة تطابق المعنى المطلوب بدقة، تصبح مرشحًا للاستبدال.
- لا نغيّر الصور فقط لتحقيق تنوع بصري إذا أضعف ذلك المعنى التعليمي.

---

## 9. سياسة مراجعة الفروع

مراجعة الفروع تأتي بعد فهم المنصة الحالية حتى لا نعيد إدخال ترقيعات قديمة.

لكل فرع سنسجل:
`branch | head | merge-base | ahead/behind | unique files/commits | category | action`

التصنيفات:
- `ALREADY_CONTAINED`
- `UNIQUE_RELEVANT`
- `OBSOLETE_SUPERSEDED`
- `EXPERIMENTAL`
- `ARCHIVE_CANDIDATE`
- `EXCLUDED_AI_VOICE_MODEL`

فرع نموذج الصوت الاصطناعي المؤقت يبقى خارج الدمج حتى قرار منفصل.

---

## 10. بوابة Railway النهائية

لا يتم لمس الإنتاج الحالي الآن. قبل الاستبدال يجب توفر:

- Branch نهائي موحد.
- Backend 100% green.
- Frontend 100% green.
- Security green.
- migrations roundtrip green.
- seed-twice green.
- media/audio green.
- integration/E2E green.
- mobile admin + student journeys verified.
- badge E2E verified.
- readiness 200 بعد النشر.
- خطة rollback ونسخة احتياطية لقاعدة البيانات.

عندها فقط يتم نشر النسخة الكاملة على Railway بدل نسخة التطوير الحالية، ثم smoke tests وبعدها التحويل النهائي.

---

## 11. نقطة التوقف الحالية

تم بدء A00 وA01 وA04، واستخراج الفشلين الحقيقيين من Backend CI بدل التخمين. الخطوة التالية في المراجعة هي استكمال:

1. Matrix كامل لصفحات Admin وmobile behavior.
2. Badge subsystem end-to-end.
3. Legacy seed/runtime dependency map.
4. Asset usage/orphan/repetition matrix.
5. باقي Backend/Data/Security/Audio/Reports/Operational audit.
6. بعدها branch reconciliation inventory.

**لا تحسينات واسعة ولا Merge ولا Railway Deploy قبل أن تكتمل خريطة الفجوات.**
