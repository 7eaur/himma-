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

## 11. نقطة التوقف السابقة

تم بدء A00 وA01 وA04، واستخراج الفشلين الحقيقيين من Backend CI بدل التخمين. وكانت الخطوة التالية المسجلة قبل استلام الاستمرارية هي استكمال الصوت وبقية التدقيق.

هذه النقطة **SUPERSEDED** بالقسم 12 أدناه بعد اكتمال A03 deep audit على فرع المراجعة.

---

## 12. A03 — Audio / Speech Analysis / Human Review / Adaptation deep audit

**الحالة:** `AUDIT COMPLETE / FINDINGS VERIFIED / NO FIX APPLIED`  
**HEAD الذي بدأ عليه التدقيق:** `91ae00776f52ec01dc0fc2c6006f8376ba44636b`  
**التقرير التفصيلي:** `docs/maintenance/HIMMA_A03_AUDIO_SPEECH_REVIEW_ADAPTATION_AUDIT_2026-09-10_AR.md`

### 12.1 ما ثبت أنه صحيح ويجب الحفاظ عليه

- `audio_review_state.py` هو أقرب مالك حالي للعقد الحديث: latest submission + pending neutral + deferred rerecord + graded-only evidence.
- `activity_runtime.py` يواصل نفس المستوى مع pending audio، ويحجز العنصر السابق، ويفتح rerecord صراحة، ويضيف submission جديدًا في مسار Core.
- `adaptation_runtime.py` يحجز فقط promotion/L3 completion عند unresolved audio، ولا يمنع same-level support.
- Speech queue/worker/alignment/models موجودة فعليًا؛ لا Fake production provider، ولا provider call داخل HTTP request path.
- word-level C/D/I/S reference alignment موجود، بينما haraka/phoneme scoring غير مدعى وغير معتمد بعد.
- لا يوجد Production ASR Provider معتمد حتى الآن؛ هذا Blocker قرار لا يجوز ترقيعه بمزود وهمي.

### 12.2 سجل فجوات A03

| ID | المجال | Severity | Status | Symptom / Evidence المختصر | Root Cause | Correct Owner | Root Fix لاحقًا | History/Migration Risk | Required Tests | Release Risk | Wave |
|---|---|---:|---|---|---|---|---|---|---|---|---|
| AUD-A03-001 | Assessment rerecord/history | P0 | VERIFIED | `assessment.py` يستبدل بيانات نفس `AudioSubmission` عند rerecord بدل إنشاء صف جديد؛ اختبار تاريخي يثبت count=1 بعد الإعادة. | state machine assessment أقدم من canonical audio lifecycle. | shared audio-review lifecycle | append-only rerecord بعد explicit open؛ old immutable. | HIGH؛ لا يمكن اختلاق recording سبق طمسه. | old retained + new latest + explicit open + score/display latest | Academic/audit integrity | A10-W1 |
| AUD-A03-002 | Assessment latest semantics | P1 | VERIFIED | assessment/profile/completion تستخدم `first()` أو تفحص كل submissions؛ old rerecord قد يبقى حاجبًا بعد append-only. | helper الحديث لم يصبح owner لكل assessment surfaces. | canonical latest-submission service | latest-only navigation/progress/display/completion/scoring. | MEDIUM | old rerecord + new uploaded/graded عبر كل APIs | High | A10-W1 |
| AUD-A03-003 | Human review/rerecord | P1 | VERIFIED | invalid review يعيد `Attempt` إلى in_progress ويمسح completed_at فورًا؛ Admin copy يقول “سيُعاد فتح”. | review endpoint يحمل reopen semantics قديمة. | unified review lifecycle | mark rerecord_required فقط؛ actionability عند learner explicit open. | MEDIUM | invalid alone non-actionable; explicit open actionable | High | A10-W1 |
| AUD-A03-004 | Machine/human adjudication | P1 | VERIFIED | Admin review لا يرى SpeechAnalysis؛ لا direct adjudication link؛ human grading قد يسبق worker discovery. | speech pipeline وhuman review مساران متوازيان. | unified review/adjudication service | machine evidence advisory + linked audited human decision. | LOW/MEDIUM | provider absent path + fixture analysis + human override | High before ASR release | A10-W2 |
| AUD-A03-005 | Calibration governance | P1 | VERIFIED | threshold + arbitrary calibration-version env يمكن أن ينتج machine `auto_accepted`؛ لا approved registry/checksum. لا score mutation اليوم. | config string مساوية داخل subsystem لمفهوم approval. | speech policy/governance | attested provider/model/calibration registry؛ machine remains advisory until approved. | LOW | arbitrary env cannot become academic authority | Release-gate risk | A10-W2 |
| AUD-A03-006 | Queue concurrency/idempotency | P1 | VERIFIED | plain claim select دون lease/`SKIP LOCKED`; عاملان يمكنهما استدعاء provider لنفس job؛ enqueue check-then-insert. | atomic claim protocol ناقص. | speech queue/worker | PostgreSQL atomic claim + lease + idempotent result write. | LOW | 2 workers/1 job; crash recovery; concurrent enqueue | Cost/reliability | A10-W2 |
| AUD-A03-007 | Retry/operator recovery | P2 | VERIFIED | manual retry لا يعيد attempt budget؛ blocked_provider لا يعود claimable تلقائيًا؛ unexpected errors لا تُصنف durable بوضوح. | operator recovery contract غير مكتمل. | speech queue/worker | explicit requeue/reset policy + durable unexpected-error state. | LOW | dead-letter retry + provider recovery + unexpected error | Medium | A10-W2 |
| AUD-A03-008 | Production ASR | P1 | BLOCKED | لا Production Adapter ولا representative calibration ولا phoneme/haraka authority. | OI-02 provider/privacy/cost/data-transfer/calibration غير مغلق. | Product + Privacy + Academic + Speech | اعتماد مزود وعقد ومعايرة؛ أو إبقاء human path authoritative. | N/A | provider/privacy/calibration/human override | يمنع ادعاء Automated ASR readiness | A10/A11 |
| AUD-A03-009 | Adaptation academic evidence | P0 | VERIFIED | `review.py` يحول `rubric_score > 0` إلى `response.is_correct=True`، ثم `_attempt_signal()` يحوله إلى full boolean correctness؛ 0.10 و1.00 قد يصبحان 100% على خطوة صوتية أحادية. | boolean response contract أقدم من C/D/I/S rubric. | canonical adaptation evidence builder | graded audio evidence من latest `AudioReview.rubric_score` أو policy أكاديمية صريحة، لا `>0`. | HIGH؛ لا تعاد كتابة decisions تاريخية بصمت. | rubric 1.0/0.5/0.1 differentiated; latest-only; promotion regression | Academic correctness P0 | A10-W1 |
| AUD-A03-010 | Storage/security/observability | P2 | CARRY_TO_A07 | `recordings.py` يكرر boto config؛ `stream-by-key` يثق بأي `audio/` key للمشرف؛ لا queue lag/worker health واضح. | storage/ops hardening خارج owner واحد. | A07 Security/Observability | يحدد بعد تدقيق A07. | TBD | authorization/metrics/readiness tests | TBD | A07/A10 |

### 12.3 أهم استنتاج معماري

يوجد حاليًا **مساران صوتيان مختلفان**:

1. **Core learning الحديث نسبيًا**: latest submission، append-only rerecord، explicit open، same-level continuation.
2. **Pre/Post assessment التاريخي**: pending review يحجز الاختبار، invalid review يعيد Attempt، وrerecord يستبدل نفس AudioSubmission، وبعض display/completion queries لا تستخدم latest semantics.

يمكن أن يكون انتظار review داخل الاختبار قرارًا بحثيًا مشروعًا، لكن **طمس التسجيل السابق وازدواج تعريف active audio state ليسا مقبولين** وفق العقد الأحدث.

### 12.4 فجوة P0 إضافية في evidence

المراجعة البشرية تحفظ rubric مستمرًا من C/D/I/S، لكن adaptation الحالي لا يقرأ rubric للصوت graded؛ يعتمد على `AttemptResponse.is_correct` الذي يساوي فقط `rubric_score > 0`. هذا يجعل أي أداء موجب تقريبًا قابلًا للتحول إلى full-correct evidence، وقد يرفع mastery بصورة غير صحيحة. لا يصلح بتغيير threshold سريع؛ يحتاج owner واحد لتعريف graded-audio evidence مع قرار أكاديمي واختبارات حدود.

### 12.5 Frontend / review contract

- Admin audio review يعرض التسجيل والنص المرجعي وحقول C/D/I/S، لكنه لا يعرض machine transcript/alignment/confidence.
- copy المراجعة ما زال يستخدم “إعادة فتح المحاولة”.
- `StudentRerecordTasks` يطبق deferred explicit task لمسار `core` فقط؛ لا يغطي assessment.
- `StudentAudioReviewOverlay.tsx` موجود في الشجرة لكنه غير مركب في student layout الحالي؛ يصنف legacy/dead-code candidate فقط حتى dependency proof، ولا نعتبره blocking فعالًا.

### 12.6 الاختبارات

يوجد regression coverage جيد للعقد الحديث في Core ولحدود adaptation مع pending/graded، لكن يوجد أيضًا اختبار Assessment تاريخي يثبت السلوك القديم `reopen + replace same submission`. لذلك الاختبار التاريخي نفسه جزء من migration المطلوبة، وليس دليلًا على أن السلوك الحالي صحيح.

**لم تُشغل Test Suite جديدة أثناء A03 في جلسة التدقيق هذه.** لا توجد دعوى PASS جديدة.

### 12.7 قرار A03 ونقطة الاستكمال الجديدة

A03 مكتمل من ناحية **الفهم والتوثيق قبل الإصلاح**. لم نبدأ A10 ولم نغير Production code.

نقطة الاستكمال الجديدة:

1. **A04 — Admin / Frontend / Mobile detailed audit**.
2. ثم A05 end-to-end badges.
3. ثم A06 manual media semantic review.
4. ثم A07/A08/A09.
5. بعدها فقط Master Gap Register الكامل ثم A10.

**ممنوع القفز من هذه النتائج إلى Patch سريع؛ P0/P1 أعلاه تُحل كموجة جذرية بعد اكتمال A00–A09.**
