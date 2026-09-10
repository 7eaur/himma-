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

النتيجة المطلوبة هي **سجل فجوات كامل ومثبت بالأدلة** يغطي Backend وFrontend وUX/UI وقاعدة البيانات والمحتوى والتكيف والصوت والشارات والوسائط والأمان والاختبارات والفروع والاستعداد للنشر. لا تبدأ موجات التحسين والدمج إلا بعد نضج هذا السجل.

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
تثبيت HEAD، فحص default branch وCI، وتفريق فشل Runner عن فشل الكود.

### A01 — Backend والـRuntime والـRoutes
ملكية Routes، طبقات activities التاريخية، الخدمات المشتركة، التقييم/التعلم/التقوية/التقارير/الصوت/التكيف، والتكرار/dead code.

### A02 — قاعدة البيانات والمحتوى والـSeeds/Migrations
canonical publisher، Seed/Repair/Projection التاريخي، Alembic roundtrip/drift/idempotency والتاريخ الدائم.

### A03 — الصوت والتحليل والتكيف
Pending/graded/rerecord، append-only history، ASR/reference-guided pipeline، human review، evidence، promotion/completion gates.

### A04 — Frontend وUX/UI
Design System، Admin shell، Student Details، Settings/Account، mobile/responsive/accessibility/states/RTL.

### A05 — نظام الشارات والمكافآت
Models/Migrations، award semantics، idempotency، API، Student/Admin UI، الأصول، Unit/Integration/E2E.

### A06 — الصور والوسائط
جرد assets واستخدامها، orphans/duplicates، semantic correctness، القصص والصوت والـserving contracts.

### A07 — الأمن، الأداء، الوصولية، المراقبة
Auth/roles/IDOR/rate limits/secrets، performance، WCAG، readiness/logging/health.

### A08 — الاختبارات والرحلة الكاملة
Backend/Frontend/Security/Migrations/Seed/Media/Audio/Integration/E2E والرحلة Pretest→Posttest والتجارب على الهاتف.

### A09 — مراجعة الفروع والتوحيد
تصنيف `already-contained / unique-relevant / obsolete / experimental / archive-candidate` مع استبعاد فرع نموذج الصوت المؤقت وعدم الدمج الأعمى.

### A10 — موجات الصيانة والتحسين
تُبنى فقط بعد اكتمال A00–A09، حسب الخطورة والاعتماديات.

### A11 — Final Release Gate ثم Railway
جميع البوابات خضراء، فرع نهائي موحد، Backup/Rollback، PostgreSQL/Media/Audio/Worker عند الاعتماد، migrations/canonical publication/readiness/smoke/post-deploy E2E.

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

هذه نتائج التشغيل المرجعي عند بداية المراجعة وليست دعوى تشغيل جديدة للمراحل اللاحقة.

---

## 5. سجل الفجوات الجامع حتى إغلاق A04

| ID | المجال | الشدة | الحالة | الملخص |
|---|---|---:|---|---|
| AUD-CI-001 | CI | P1 | OPEN | Backend فيه فشلان من 825، ولذلك Integration/E2E لم يعمل على HEAD المرجعي. |
| AUD-BE-001 | Runtime | P2 | VERIFIED | `activity_runtime` يعتمد على `activities_v4` و`activities`؛ Router العام واحد لكن ملكية الخدمة موزعة تاريخيًا. |
| AUD-BE-002 | Seeds | P2 | VERIFIED | `seed_all` canonical، لكن Seed/Projection/Correction تاريخية كثيرة ما زالت تحتاج dependency classification. |
| AUD-BE-003 | Audio view | P1 | VERIFIED | `pending_audio_reviews` قد يرجع 0 مع جولة صوت Pending إذا وجدت خطوة أخرى actionable في نفس المحاولة. |
| AUD-BE-004 | Legacy test path | P2 | VERIFIED | Recovery لـPRE-Q05 يبني baseline 105 عبر `seed.run_seed()` بدل canonical 125 فيرى 3 صور بدل 4. |
| AUD-A03-001 | Assessment rerecord/history | P0 | VERIFIED | assessment rerecord يستبدل نفس `AudioSubmission` بدل append-only submission جديد. |
| AUD-A03-002 | Assessment latest semantics | P1 | VERIFIED | assessment/profile/completion لا تعتمد latest-submission semantics بشكل موحد. |
| AUD-A03-003 | Human review/rerecord | P1 | VERIFIED | invalid review يعيد Attempt إلى in_progress فورًا بدل deferred explicit rerecord contract. |
| AUD-A03-004 | Machine/human adjudication | P1 | VERIFIED | SpeechAnalysis غير مربوط بقرار human review كمسار adjudication واحد. |
| AUD-A03-005 | Calibration governance | P1 | VERIFIED | calibration env/version لا يساوي approved attestation registry. |
| AUD-A03-006 | Queue concurrency | P1 | VERIFIED | worker claim غير ذري، ويمكن ازدواج provider call/enqueue race. |
| AUD-A03-007 | Retry/operator recovery | P2 | VERIFIED | retry/dead-letter/provider recovery contract غير مكتمل. |
| AUD-A03-008 | Production ASR | P1 | BLOCKED | لا Production ASR Provider معتمد ولا معايرة/خصوصية/تكلفة مغلقة. |
| AUD-A03-009 | Adaptation evidence | P0 | VERIFIED | `rubric_score > 0` يتحول إلى boolean correct؛ 0.10 و1.00 قد يصبحان full-correct evidence. |
| AUD-A03-010 | Storage/security/observability | P2 | CARRY_TO_A07 | storage authorization/config وqueue observability تحتاج A07. |
| AUD-A04-001 | Admin UI ownership | P1 | VERIFIED | Student Details + Settings + legacy Account تمثل ثلاث طبقات presentation موازية رغم وجود AdminUI. |
| AUD-A04-002 | Student Detail evidence states | P1 | VERIFIED | فشل history/rewards يتحول إلى `[]` ويظهر للمشرف كـ0/empty حقيقي. |
| AUD-A04-003 | Journey truth | P1 | VERIFIED | UI يساوي `level < current_level` بـ“مكتمل”؛ manual override يمكن أن يقفز مستويات دون completion evidence لكل مستوى أدنى. |
| AUD-A04-004 | Legacy account | P2 | VERIFIED | `/admin/account` موجود، غير موجود في shell nav، ويتداخل مع Settings ويستخدم legacy styling. |
| AUD-A04-005 | Student Detail mobile gate | P1 | VERIFIED | detail يغطي 390/768 فقط وبشكل شرطي؛ لا gate مباشر كامل 320/360/390/430/768/Desktop. |
| AUD-A04-006 | Mobile dialog keyboard | P2 | VERIFIED | shell dialog لا يملك focus-trap/Escape/return-focus contract صريحًا، والاختبار الحالي لا يغطيه. |
| AUD-A04-007 | Settings accessibility/style drift | P2 | VERIFIED | tabs/styles مستقلة عن AdminUI وبدون selected-state ARIA pattern واضح. |
| AUD-A04-008 | Student recording context | P2 | VERIFIED | Student Detail يرسل المشرف إلى audio-review العامة دون filter/deep-link خاص بالطالب. |
| AUD-BADGE-001 | Student badges | P1 | VERIFIED INITIAL | Backend/API يملكان BadgeEvent لكن Student home لا يعرض الشارات بصريًا. |
| AUD-BADGE-002 | Admin badge visual | P2 | VERIFIED INITIAL | Student Detail يعرض label/chip فقط دون asset canonical. |
| AUD-BADGE-003 | Badge assets | P1 | VERIFIED INITIAL | الحزمة المعتمدة للشارات/المستويات غير مدمجة حاليًا في `apps/web/public` كـreward catalog. |
| AUD-BADGE-004 | L3 badge naming | P1 | VERIFIED INITIAL | Backend `قارئ متميز` مقابل BDG-06 المعتمد `نجم الفهم`. |
| AUD-BADGE-005 | Completion semantics | P1 | VERIFIED INITIAL | early promotion يمكن أن يجعل المستوى completed بينما badge logic ما زال يشترط 10 core. |
| AUD-BADGE-006 | Badge E2E | P1 | OPEN | لا E2E يغلق award→asset→Student/Admin→refresh/idempotency كاملًا. |
| AUD-MEDIA-001 | Images | P2 | IN PROGRESS | يلزم referenced/unreferenced/repeated inventory ومقارنة دلالية قبل الاستبدال. |
| AUD-GIT-001 | Branch governance | P1 | VERIFIED | default branch ليس فرع التكامل الحديث؛ يحسم بعد A09 وقبل الإصدار. |
| AUD-GIT-002 | Branches | P1 | IN PROGRESS | فروع stage/integration/codex/feature كثيرة تحتاج تصنيفًا كاملًا. |
| AUD-REL-001 | Release | P0 | OPEN | لا نشر أو استبدال Railway قبل اكتمال التدقيق والتحسين والتوحيد والبوابات. |

---

## 6. تفاصيل Backend/Seeds المبكرة

### AUD-BE-001 — سلسلة Runtime تاريخية للأنشطة
`main.py` يركب Router الأنشطة من `activity_runtime.py`، لكن `activity_runtime.py` ما زال يستورد خدمات من `activities.py` وhelpers من `activities_v4.py`، والأخير يعتمد على `activities.py`. هذه أجيال تنفيذية متداخلة وليست ثلاثة Routers عامة متعارضة. الإزالة لا تبدأ قبل dependency map/parity tests ونقل primitives إلى owners وظيفيين.

### AUD-BE-002 — Seed/Projection تاريخي بعد التوحيد
`seed_all.py` ينشر 125 عنصرًا عبر canonical publisher ولا يشغل repair chain بعد النشر. بقاء ملفات correction/projection لا يعني حذفها؛ يجب تصنيفها migration input/test/tool/dead candidate أولًا.

### AUD-BE-003 — Pending Audio summary
`navigation_target()` يخلط اختيار next action مع session pending summary، فيمكن أن يرجع actionable step قبل احتساب pending review. الإصلاح الجذري هو فصل navigation resolver عن latest-submission review summary.

### AUD-BE-004 — Recovery يبني عالمًا قديمًا
Recovery helper لـPRE-Q05 يشغل `seed.run_seed()` التاريخي 105 بدل canonical publication؛ لذلك يرى VOC-01/02/03 فقط بينما canonical الحالي أربع صور. يجب فصل migration-compatibility tests عن runtime-current tests.

---

## 7. A03 — Audio / Speech Analysis / Human Review / Adaptation

**الحالة:** `AUDIT COMPLETE / FINDINGS VERIFIED / NO FIX APPLIED`  
**التقرير التفصيلي:** `docs/maintenance/HIMMA_A03_AUDIO_SPEECH_REVIEW_ADAPTATION_AUDIT_2026-09-10_AR.md`

### ما يجب الحفاظ عليه
- `audio_review_state.py` هو أقرب مالك للعقد الحديث: latest submission + pending neutral + deferred rerecord + graded-only evidence.
- Core الحديث يواصل same-level مع pending audio، يفتح rerecord صراحة، ويضيف submission جديدًا.
- `adaptation_runtime.py` يحجز فقط promotion/L3 completion عند unresolved audio ولا يمنع same-level support.
- Speech queue/worker/alignment/models حقيقية، ولا Fake production provider ولا provider call داخل HTTP path.
- word-level C/D/I/S alignment موجود؛ phoneme/haraka authority غير معتمد.
- لا Production ASR Provider معتمد.

### الفجوات الجذرية
- Assessment pre/post ما زال على lifecycle أقدم: replace same submission، non-latest reads، وreopen semantics.
- Admin review وSpeechAnalysis مساران غير موحدين.
- worker claim/retry/calibration governance تحتاج عقد production قبل ASR.
- أخطر فجوة أكاديمية: graded rubric يتحول حاليًا إلى boolean `is_correct` عبر `>0` ثم adaptation يراه full correctness.

### حدود التاريخ
لا تُعاد كتابة AudioSubmission/AdaptationDecision التاريخية بصمت. أي migration لاحق يجب أن يحافظ على السجل ويغيّر ownership للأحداث الجديدة مع compatibility واضحة.

**لم تُشغّل Test Suite جديدة أثناء A03.**

---

## 8. A04 — Admin UI / Student Details / Mobile

**الحالة:** `AUDIT COMPLETE / FINDINGS VERIFIED / NO PRODUCTION FIX APPLIED`  
**التقرير التفصيلي:** `docs/maintenance/HIMMA_A04_ADMIN_MOBILE_DEEP_AUDIT_2026-09-10_AR.md`  
**التقرير التمهيدي المشترك:** `docs/maintenance/HIMMA_A04_A05_ADMIN_BADGES_AUDIT_2026-09-10_AR.md`

### 8.1 ملكية الواجهة
`components/admin/AdminUI` موجود ويُستخدم فعليًا في `/admin`, `/admin/students`, `/admin/students/new` وصفحات أخرى. لكن Student Details وSettings يعيدان بناء primitives محلية، و`/admin/account` يحتفظ بطبقة legacy إضافية. الاتجاه الجذري في A10 هو:

`global tokens → AdminUI primitives → page-specific composition`

لا يعني ذلك جعل الصفحات متطابقة، بل جعل spacing/forms/buttons/panels/mobile behavior ذات owner واحد.

### 8.2 Student Details لا يجوز أن يحول error إلى empty
الصفحة تجمع ثلاث APIs. إذا نجح student وفشل history أو rewards، تحول الفشل إلى `[]`. عندها تعرض “لا يوجد سجل” أو 0 نجوم/شارات. هذا تضليل للـevidence ويجب أن يصبح partial-source state صريحًا أو view-model endpoint موحدًا.

### 8.3 Journey completion ليس `current_level`
الواجهة الحالية تعتبر كل مستوى أقل من `current_level` مكتملًا. في المقابل manual override يسمح بتغيير level 1/2/3 ويمكن أن يغلق core session وينشئ التالية دون اشتراط completion evidence لكل مستوى أدنى. لذلك يجب أن يأتي per-level completion من Journey/completion owner canonical، لا من رقم المستوى.

### 8.4 `/admin/account`
تم فحصه قبل أي حذف. هو read-only profile/logout، غير موجود في sidebar، يستخدم legacy CSS/inline styles، ويتداخل مع Settings. `/api/me` للمشرف يعيد `full_name` مساويًا لـusername. الحكم: `LEGACY DUPLICATE / ARCHIVE-CANDIDATE` فقط؛ لا حذف حتى dependency scan/redirect proof في A10.

### 8.5 Responsive evidence
- `admin-responsive.spec.ts`: 390 و768 للـAdmin؛ Student Details مشروط بوجود طالب.
- `responsive-smoke.spec.ts`: 360/390/768/1024/1440 لكن للـlanding/login فقط.
- `p03-screenshots.spec.ts`: Admin 390/768/1440 لكنه لا يشمل Student Details.
- `accessibility-integration.spec.ts`: dashboard/focus/RTL، menu 390، 720 zoom-equivalent؛ لا focus trap/Escape/return-focus للdialog.

إذًا بوابة Student Details المطلوبة ما زالت تنفيذية لاحقًا: 320/360/390/430/768/desktop بfixture deterministic وoverflow/tabs/forms/actions/keyboard assertions.

### 8.6 قرار A04
A04 مغلق كتدقيق. لا Production code، لا Merge، لا Deploy. نقطة الاستكمال أصبحت **A05 — Rewards/Badges end-to-end**.

---

## 9. A05 — الحالة الأولية قبل التعميق

التقرير المشترك أثبت مسبقًا:
- `RewardEvent` persistent مع `UNIQUE(student_id, reward_key)`.
- stars/badge events وAPIs موجودة وليست نظامًا مفقودًا من Backend.
- Student home يجلب rewards لكنه لا يعرض badge assets.
- Admin Student Detail يعرض badge labels/chips فقط.
- حزمة BDG-01..06 الرسمية غير مربوطة بـpublic/reward contract.
- L3 label مختلف بين Backend (`قارئ متميز`) والحزمة (`نجم الفهم`).
- Journey يمكن أن يعتبر early-promotion level completed بينما badge logic ما زال legacy `>=10 core`.
- Badge E2E الكامل غير مغلق.

A05 الحالي يجب أن يحسم owner-of-truth لـlevel completion وreward catalog والعلاقة بين التاريخ الحالي والـasset/display contract قبل أي تعديل.

---

## 10. ما تم التحقق منه إيجابيًا ولا يجب كسره

1. Router الأنشطة العام الحالي له مالك واحد في `main.py`.
2. canonical content release = 125 عنصرًا.
3. canonical seed مرتين على PostgreSQL أعطى نفس release/projection بلا churn في الدورة الثانية.
4. snapshot المرجعي: 44 مهارة، 824 خيارًا، 265 asset links.
5. migrations roundtrip وdrift gate نجحا في التشغيل المرجعي.
6. Frontend typecheck/lint/unit/build خضراء في التشغيل المرجعي.
7. Security gates خضراء في التشغيل المرجعي.
8. Core audio/adaptation الحديثة تحافظ على pending-neutral وsame-level continuation.
9. media canonical guard/generated sequence tests موجودة ونجحت في التشغيل المرجعي.
10. AdminUI/responsive table/mobile-card pattern موجود ولا حاجة لإنشاء Design System جديد.
11. التاريخ الأكاديمي والصوتي والمكافآت الحالية لا يحذف لمجرد التوحيد.

---

## 11. سياسة الصور أثناء المراجعة

A06 سينتج:
`asset_id | file | semantic label | usages | use_count | current locations | orphan? | duplicate semantics? | candidate replacement?`

التكرار المقبول يُحكم دلاليًا. لا تستبدل صورة لمجرد التنوع. الصورة غير المستخدمة تصبح مرشحًا فقط إذا طابقت المعنى بدقة.

---

## 12. سياسة مراجعة الفروع

لكل فرع:
`branch | head | merge-base | ahead/behind | unique files/commits | category | action`

التصنيفات: `ALREADY_CONTAINED`, `UNIQUE_RELEVANT`, `OBSOLETE_SUPERSEDED`, `EXPERIMENTAL`, `ARCHIVE_CANDIDATE`, `EXCLUDED_AI_VOICE_MODEL`.

فرع نموذج الصوت الاصطناعي المؤقت خارج الدمج حتى قرار منفصل.

---

## 13. بوابة Railway النهائية

لا يتم لمس الإنتاج الحالي أثناء التدقيق. قبل الاستبدال يجب توفر: branch نهائي موحد، Backend/Frontend/Security green، migration roundtrip، seed-twice، media/audio، Integration/E2E، mobile Admin+Student journeys، badge E2E، readiness 200، backup/rollback، ثم smoke/post-deploy E2E.

---

## 14. نقطة الاستكمال الحالية

A03 وA04 مغلقان كـaudit-only. لم يبدأ A10 ولم يحدث Merge/Deploy.

**نقطة الاستكمال الآن: A05 — Rewards / Badges.**

الأولوية الفورية:
1. تتبع `_core_flow_complete` و`ensure_rewards` مقابل Journey/early-promotion completion.
2. إثبات كل reward consumer في Student/Admin.
3. تثبيت catalog/asset ownership من الحزمة المعتمدة دون إعادة رسم أو إعادة تسمية اعتباطية.
4. فحص tests الخاصة بالمكافآت والشارات وidempotency وإثبات missing E2E بدقة.
5. تسجيل القرار في تقرير A05/هذا السجل ثم الانتقال إلى A06 دون تنفيذ ترقيعات Production.