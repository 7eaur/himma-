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

## 5. سجل الفجوات الجامع حتى إغلاق A05

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
| AUD-BADGE-001 | Student badges | P1 | VERIFIED | Backend/API يملكان BadgeEvent لكن Student home لا يعرض الشارات بصريًا. |
| AUD-BADGE-002 | Admin badge visual | P2 | VERIFIED | Student Detail يعرض label/chip فقط دون asset canonical. |
| AUD-BADGE-003 | Badge assets | P1 | VERIFIED | الحزمة المعتمدة للشارات/المستويات غير مدمجة في `apps/web/public` كـreward catalog. |
| AUD-BADGE-004 | L3 badge naming | P1 | VERIFIED | Backend `قارئ متميز` مقابل BDG-06 المعتمد `نجم الفهم`. |
| AUD-BADGE-005 | Completion semantics | P1 | VERIFIED | early promotion في L1/L2 يثبت completion عند 6–9 Core بينما badge logic لا يمنح إلا عند 10؛ lifecycle الحالي يترك المستوى completed بلا badge. |
| AUD-BADGE-006 | Badge E2E | P1 | OPEN | لا E2E يغلق award→asset→Student/Admin→refresh/idempotency كاملًا. |
| AUD-BADGE-007 | Student reward state | P2 | VERIFIED | فشل `/api/rewards` في Student Home يبقي rewards فارغة فيظهر رصيد 0 بدل حالة unavailable صريحة. |
| AUD-BADGE-008 | Reward presentation contract | P1 | VERIFIED | Reward API لا يحمل catalog/asset identity/version مستقرة، ما يجبر UI على mapping موازٍ إن أضيفت الصور مباشرة. |
| AUD-BADGE-009 | Reward history FK | P2 | CARRY_TO_A10_A07 | star RewardEvent يرتبط بـAttempt مع `ON DELETE CASCADE`; لا delete path طبيعي مثبت الآن، لكنه schema risk يجب حمايته قبل أي cleanup/reset. |
| AUD-MEDIA-001 | Images | P2 | IN PROGRESS | referenced/unreferenced/repeated inventory موجود مبدئيًا ويحتاج إغلاق semantic/dependency classification في A06 قبل الاستبدال. |
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
**التقرير المشترك:** `docs/maintenance/HIMMA_A04_A05_ADMIN_BADGES_AUDIT_2026-09-10_AR.md`

### 8.1 ملكية الواجهة
`components/admin/AdminUI` موجود ويُستخدم فعليًا في `/admin`, `/admin/students`, `/admin/students/new` وصفحات أخرى. لكن Student Details وSettings يعيدان بناء primitives محلية، و`/admin/account` يحتفظ بطبقة legacy إضافية. الاتجاه الجذري في A10 هو:

`global tokens → AdminUI primitives → page-specific composition`

### 8.2 Student Details لا يجوز أن يحول error إلى empty
الصفحة تجمع ثلاث APIs. إذا نجح student وفشل history أو rewards، تحول الفشل إلى `[]`. عندها تعرض “لا يوجد سجل” أو 0 نجوم/شارات. هذا تضليل للـevidence ويجب أن يصبح partial-source state صريحًا أو view-model endpoint موحدًا.

### 8.3 Journey completion ليس `current_level`
الواجهة الحالية تعتبر كل مستوى أقل من `current_level` مكتملًا. manual override يستطيع تغيير المستوى؛ لذلك يجب أن يأتي per-level completion من Journey/completion owner canonical، لا من رقم المستوى.

### 8.4 `/admin/account`
تم فحصه قبل أي حذف. هو route حي read-only profile/logout، غير موجود في sidebar، يستخدم legacy CSS/inline styles، ويتداخل مع Settings. الحكم: `LEGACY DUPLICATE / ARCHIVE-CANDIDATE` فقط؛ لا حذف حتى dependency scan/redirect proof في A10.

### 8.5 Responsive evidence
الاختبارات الحالية تغطي أجزاء من Admin/responsive، لكنها لا تغلق Student Details عند 320/360/390/430/768/Desktop بfixture deterministic وoverflow/tabs/forms/actions/keyboard assertions.

### 8.6 قرار A04
A04 مغلق كتدقيق. لا Production code، لا Merge، لا Deploy.

---

## 9. A05 — Rewards / Badges

**الحالة:** `STATIC/SOURCE AUDIT COMPLETE / FINDINGS VERIFIED / NO PRODUCTION FIX APPLIED`  
**التقرير التفصيلي:** `docs/maintenance/HIMMA_A04_A05_ADMIN_BADGES_AUDIT_2026-09-10_AR.md`

### 9.1 ما هو موجود ويجب الحفاظ عليه
- `RewardEvent` persistent وقيد `UNIQUE(student_id, reward_key)`.
- `ensure_rewards()` يمنح نجومًا من evidence صالح فقط ويستبعد media-gap/unresolved audio.
- النجوم تستخدم stable key per Attempt وتوجد حماية idempotency منطقية + DB.
- Student `/rewards` وResearcher student rewards APIs موجودة.
- `test_adaptation_runtime.py` يثبت stars once/idempotency واستبعاد evidence غير الصالح.

### 9.2 split-brain في milestone completion
`decide_transition()` يسمح L1/L2 early promotion من 6 Core بعد استيفاء mastery/critical-skill/gates. `ensure_rewards()` يعمل قبل transition ويشترط `_completed_core_count >= 10` للشارة. `journey.py` لاحقًا يقرأ persisted transition evidence ويعتبر المستوى completed حتى لو كان 6–9 Core. `test_m09_full_single_candidate_journey.py` يثبت أن L1/L2 يترقيان فعليًا تحت 10 Core.

النتيجة: completion milestone وbadge milestone لهما مالكان مختلفان، ويجب توحيدهما في A10 دون إعادة early-promotion إلى legacy 10/10.

### 9.3 Visual/catalog contract غير مكتمل
حزمة BDG الرسمية تحتوي ست مكافآت وSVGs مع BDG-04/05/06 للمستويات، لكنها غير مدمجة في `apps/web/public`. Student لا يعرض badges، Admin يعرض text chip فقط، والـAPI لا يملك catalog/asset identity مستقرة. L3 backend label `قارئ متميز` بينما BDG-06 `نجم الفهم`.

الحل الجذري: Reward Catalog canonical واحد يملك `catalog_id/key/type/level/label/asset/version` ويغذي API وStudent/Admin، مع إبقاء تاريخ RewardEvent محفوظًا وعدم إعادة كتابة labels القديمة صامتًا.

### 9.4 حالات الخطأ والاختبارات
Student Home يحول rewards fetch failure عمليًا إلى قائمة فارغة/totalStars=0، فيخلط unavailable مع true zero. كما أن `student/page.test.tsx` لا يختبر badge rendering. لا يوجد E2E كامل award→asset→Student/Admin→refresh.

### 9.5 مخاطرة history schema
`reward_events.attempt_id` عليه `ON DELETE CASCADE`. لا يوجد delete path طبيعي مثبت في هذه الجولة، وretake contract يحافظ على history؛ لذا لا نصنفه data-loss defect حاليًا، لكن يمنع أي cleanup مستقبلًا قبل حسم سياسة Reward history/FK.

### 9.6 قرار A05
A05 مغلق كتدقيق static/source. التنفيذ مؤجل إلى A10، والـBadge E2E إلى A08 بعد الإصلاح. نقطة الاستكمال انتقلت إلى **A06 — Images / Media**.

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
12. Early promotion المعتمد في L1/L2 لا يكسر أثناء توحيد rewards/completion.

---

## 11. سياسة الصور أثناء المراجعة

A06 ينتج/يثبت:
`asset_id | file | semantic label | usages | use_count | current locations | orphan? | duplicate semantics? | candidate replacement?`

التكرار المقبول يُحكم دلاليًا. لا تستبدل صورة لمجرد التنوع. الصورة غير المستخدمة تصبح مرشحًا فقط إذا طابقت المعنى بدقة، ولا حذف لأي asset قبل dependency proof.

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

A03 وA04 وA05 مغلقة كـaudit-only. لم يبدأ A10 ولم يحدث Merge/Deploy.

**نقطة الاستكمال الآن: A06 — Images / Media.**

الأولوية الفورية:
1. إعادة قراءة تقرير A06 الحالي والجرد A02/A06 بدل إعادة الجرد من الصفر.
2. مطابقة canonical image IDs مع الملفات الفعلية والـsemantic maps والـruntime/public serving.
3. فصل: referenced، unused-approved، duplicate-by-bytes، repeated-use، semantic-conflict، orphan/dead-candidate.
4. مراجعة الـ23 original-approved unused assets و18 multi-semantic repeated assets يدويًا من حيث الدلالة، لا العدد فقط.
5. عدم حذف/استبدال أي أصل أثناء التدقيق؛ تسجيل owner/root fix/test requirements ثم الانتقال إلى A07.
