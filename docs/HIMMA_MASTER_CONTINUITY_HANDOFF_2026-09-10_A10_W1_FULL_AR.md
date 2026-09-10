# منصة هِمّة — Master Continuity Handoff الكامل

**التاريخ:** 2026-09-10  
**المستودع:** `7eaur/himma-`  
**فرع العمل:** `audit/comprehensive-repository-review-2026-09-10`  
**الحالة:** `A00–A09 CLOSED — A10/W1 IN PROGRESS — NO MERGE — NO DEPLOY`  
**آخر code-bearing checkpoint قبل commits التوثيق:** `ead44bf492cdbea35b65dc9ddce54fe7de4a20ef`  

> عند بدء محادثة جديدة: لا تفترض أن SHA أعلاه هو HEAD الحالي لأن commits توثيقية قد تكون أضيفت بعده. ابدأ دائمًا بجلب HEAD للفرع الحالي، ثم اعتبر Git الحالي الحقيقة التنفيذية. لا تعِد A00–A09.

---

## 1) ما هي منصة هِمّة؟

منصة تعليمية عربية موجهة لطلاب الصف الثالث ممن لديهم صعوبات في القراءة. المسار الأساسي:

`دخول بكود → اختبار قبلي → تصنيف → تعلم المستوى → تقوية موجهة حسب الضعف → ترقية/استكمال → اختبار بعدي → تقارير المشرف`

العقد الأكاديمي الحالي:

- الاختبار القبلي: 30 سؤالًا.
- الاختبار البعدي: 30 سؤالًا.
- 3 مستويات.
- لكل مستوى 10 Core أساسية + 5 Reinforcement.
- canonical/runtime total الحالي = **125 عنصرًا**.
- Learning runtime total = 65.
- Reinforcement total = 35.
- Skills = 44.
- Projection contract = `structured_db_runtime_v1`.

التصنيف بعد الاختبار القبلي:

- `<50%` → L1.
- `50..<80%` → L2.
- `80..100%` → L3.

Learning/Adaptation V4:

- Activity `>=80` نجاح.
- `70..<80` إعادة موجهة.
- `<70` تقوية موجهة.
- L1/L2 early promotion معتمد عند >=6 Core + mastery >=85 + critical coverage + critical floor >=70 + عدم وجود unresolved reinforcement/supervisor blocker/unresolved audio عند boundary.
- الترقية مستوى واحد فقط.
- لا automatic demotion.
- L3 لا يكتمل إلا بعد 10 Core ولا يوجد L4.
- أحدث 3 evidences صالحة من الجلسة النشطة تدخل mastery بأوزان 50/30/20.

---

## 2) الحقيقة المعمارية الحالية

المسار المعتمد:

`approved/versioned source → deterministic structured projection → PostgreSQL runtime → structured API → deterministic renderer`

Canonical compiler/publisher موجود ويجب أن يبقى owner للمحتوى. لا تبنِ repair chains أو projection overlays جديدة فوقه.

لا تعُد إلى عالم 105 عنصرًا القديم. بعض recovery tests التاريخية ما زالت تفترضه، وهذه مشكلة test ownership وليست سببًا للرجوع عن canonical 125.

---

## 3) عقود الصوت الثابتة وصوت الطالب

Static approved audio:

- Approved IDs = 54.
- WAV = 54.
- MP3 = 54.
- Required static audio gaps = 0.

عقد صوت الطالب:

- `uploaded/pending` = أكاديميًا neutral.
- pending لا يمنع same-level learning/navigation/support.
- unresolved audio يمنع فقط irreversible promotion أو L3 completion، بينما الاختبارات القبلي/البعدي يجوز لها انتظار المراجعة قبل الانتقال للسؤال التالي وفق العقد الحالي.
- `rerecord_required` = مهمة مؤجلة، لا تصبح actionable إلا بعد أن يفتحها الطالب صراحة.
- إعادة التسجيل يجب أن تكون append-only: تسجيل جديد = `AudioSubmission` جديد، ولا يتم استبدال التسجيل السابق.
- latest `AudioSubmission` هو الحالة الفعالة.
- التاريخ السابق لا يُحذف ولا يغير حالة التسجيل الأحدث.
- `graded` فقط يمكن أن يدخل evidence الأكاديمي.
- Human supervisor review هو السلطة الأكاديمية الحالية.
- يوجد speech pipeline حقيقي وتجريبي، لكن لا يوجد Production ASR Provider معتمد.
- machine confidence ليس academic truth.
- ممنوع دمج أي Speech Lab/provider تجريبي واعتباره production قبل provider + calibration + privacy + cost + governance approval.

---

## 4) ما تم إنجازه في التدقيق A00–A09

A00–A09 مغلقة كتدقيق. لا تُعاد من البداية.

المخرجات الأساسية:

- `docs/maintenance/HIMMA_COMPREHENSIVE_REPOSITORY_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A03_AUDIO_SPEECH_REVIEW_ADAPTATION_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A04_ADMIN_MOBILE_DEEP_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A04_A05_ADMIN_BADGES_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A06_IMAGE_MEDIA_DEEP_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A07_SECURITY_PERFORMANCE_ACCESSIBILITY_OBSERVABILITY_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A08_FULL_JOURNEY_INTEGRATION_E2E_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A09_BRANCH_CLASSIFICATION_2026-09-10_AR.md`

Baseline CI المرجعي أثبت 823/825 backend مع فشلين قبل Integration؛ لذلك لا يوجد claim بأن current A10 HEAD green.

A09 راجع 20 فرعًا. النتيجة:

- الفروع الأساسية/القديمة B01/B02/B03 وStage/recovery/integration contained بالنسبة لفرع المراجعة، فلا Merge أعمى.
- Speech/Pronunciation Labs = research only / EXCLUDE FROM MERGE.
- deployment/platform-sandbox = reference only؛ يحتوي Docker/Temporary Audio Skip وافتراضات نشر قديمة، فلا Merge.
- لا يوجد فرع تاريخي مطلوب دمجه الآن.

---

## 5) Master Gap Register وموجات A10

W1 — Academic / History Integrity:

`AUD-A03-001/002/003/009`, `AUD-BE-003`, `AUD-A04-003`, `AUD-BADGE-005`.

W2 — Security / Speech boundaries.

W3 — Admin / Student UX / Accessibility / Web reliability.

W4 — Rewards / Badges / Media semantics.

W5 — Historical cleanup / Performance / Test ownership.

W6 — Final exact-SHA Quality Gates.

A11 Railway يبدأ فقط بعد W6 Green.

---

## 6) A10/W1 — ما تم تنفيذه فعليًا حتى الآن

### Commit 1

`8f5e3aa6d736faee579924f7a813d0e033879cac`

`fix(audio): centralize latest submission and review state`

تم توسيع `services/api/audio_review_state.py` ليكون owner مشتركًا لحالة latest submission، ويتضمن helpers لـ:

- `latest_audio_submission`
- `latest_audio_review`
- `session_latest_audio_submissions`
- `session_attempt_ids_with_latest_audio_status`
- session review summary
- explicit rerecord open audit state

الهدف: منع أي consumer من استخدام `first()` تاريخي أو كل submissions بدون latest semantics.

### Commit 2

`6a877335bf51f575450f199767321fdced3fdd14`

`fix(audio): preserve rerecord history during human review`

في `services/api/review.py`:

- pending review queue تعرض latest uploaded فقط.
- محاولة grade لتسجيل تاريخي بعد وجود newer submission ترجع 409.
- invalid review يغير latest submission إلى `rerecord_required` فقط.
- لا يعيد فتح Attempt تلقائيًا.
- `AttemptResponse.is_correct` يبقى compatibility field؛ numeric consumers يجب أن تعتمد `AudioReview.rubric_score`.

### Commit 3

`b114d8618b94db01cff0bcd99303fe3de4449619`

`fix(audio): score assessments from latest submission state`

في `services/api/assessment_completion.py`:

- preflight يعتمد latest submission فقط.
- `uploaded/pending/rerecord_required` على latest هي الحالات الحاجزة.
- graded evidence تستخدم latest AudioReview.
- التسجيلات القديمة لا تعيد فتح block ولا تعيد كتابة score.

### Commit 4

`00926e115840799c689375008e8f66744fa2b41d`

`fix(audio): make assessment rerecord append-only and explicit`

في `services/api/assessment.py`:

- assessment audio reads أصبحت latest-only.
- أضيفت assessment rerecord task listing/start endpoints.
- الطالب يجب أن يفتح rerecord task صراحة قبل إعادة التسجيل.
- rerecord يضيف `AudioSubmission` جديدًا بدل تعديل القديم.
- التسجيل القديم يبقى immutable history.
- assessment progress يحسب latest state فقط.
- opened rerecord يعود كالسؤال القابل للتنفيذ.
- assessment pending audio يبقي انتظار المراجعة حسب العقد الحالي.

### Commit 5

`ead44bf492cdbea35b65dc9ddce54fe7de4a20ef`

`refactor(learning): add canonical level completion evidence owner`

أضيف `services/api/level_completion.py`.

قواعده:

- `current_level` pointer وليس إثباتًا لاكتمال كل مستوى أدنى.
- 10/10 Core في completed Core session = complete.
- L1/L2 يمكن أن يكونا complete عبر persisted automatic early-promotion transition الصحيح.
- L3 لا يستخدم early promotion.
- manual override لا يصنع completion evidence.

هذا owner موجود الآن لكنه **لم يُربط بعد بكل consumers**.

---

## 7) W1 — ما بقي بالضبط، وهذا هو مكان الاستكمال

لا تبدأ W2 قبل إغلاق W1 واختبار حدوده.

الترتيب التنفيذي التالي:

1. ربط `level_completion.py` فعليًا مع `journey.py` وRewards logic في `adaptation.py` ومع أي posttest/admin completion consumer يحتاج الحقيقة نفسها. لا تجعل Reward badge يمتلك قاعدة 10/10 منفصلة عن Journey.
2. إصلاح `AUD-A03-009`: adaptation evidence للصوت يجب أن يحافظ على `AudioReview.rubric_score` الرقمي. لا يجوز أن تصبح 0.10 و1.00 متساويتين بسبب `bool(response.is_correct)`.
3. إصلاح `AUD-BE-003`: فصل `pending_audio_reviews` aggregate عن navigation target؛ وجود sibling actionable لا يجوز أن يجعل pending count = 0.
4. تحديث `protected.py` / profile assessment display وأي assessment consumer قد يقرأ جميع AudioSubmissions بدل latest-only.
5. تحديث واجهة assessment في Next/React لتتعامل مع `rerecord_required` كـdeferred task: تعرض المهمة، تفتحها صراحة، ثم تعيد التسجيل، بدون الرجوع للـold blocking overlay.
6. Regression tests مطلوبة قبل إغلاق W1:
   - invalid assessment audio → rerecord task appears → navigation policy صحيح → explicit open → new AudioSubmission → old remains immutable.
   - historical submission لا يدخل pending queue ولا يوقف completion بعد newer graded.
   - latest uploaded/rerecord/graded semantics عبر assessment/profile/completion.
   - numeric rubric evidence: أمثلة 0.0 / 0.1 / 0.7 / 1.0 لا تتساوى boolean-wise، وتؤثر في mastery وفق العقد المتفق عليه.
   - pending learning audio + actionable sibling يبقي `pending_audio_reviews` صحيحًا مع استمرار navigation.
   - L1/L2 early promotion عند 6–9 Core يظهر Journey complete ويمنح completion-dependent reward بدون فرض 10/10.
   - manual override لا يصنع completion/badge evidence.
   - L3 يحتاج 10/10.
7. شغّل targeted tests أولًا ثم backend relevant/full gate حسب الإمكان. لا تدّع PASS إلا بنتيجة فعلية على SHA محدد.
8. بعد W1 فقط انتقل W2.

---

## 8) فجوات لاحقة يجب عدم نسيانها

### W2

- auth rate limiting.
- JWT/session invalidation عند access-code/password rotation.
- production security mode/readiness.
- legacy `/recordings/init` max upload أو retirement بعد dependency proof.
- structured request/error logging + correlation IDs.
- speech worker atomic claim/retry إذا استمر المسار، لكن Production ASR يبقى HOLD.

### W3

- AdminUI ownership وتوحيد Student Details/Settings.
- partial API failures لا تتحول إلى empty/0.
- full mobile matrix 320/360/390/430/768/Desktop.
- focus trap/Escape/return-focus.
- Settings tab ARIA.
- route-aware media caching.
- reduced-motion implementation.
- accessible semantic colors بدل استعمال brand colors كنص عادي غير مطابق.
- progressbar semantics.

### W4

- Reward Catalog واحد.
- استيراد badge assets الرسمية BDG-01..06.
- Student badge visual UI.
- Admin shared reward presentation.
- L3 label mismatch: backend `قارئ متميز` مقابل official `نجم الفهم`؛ لا تعِد كتابة history عشوائيًا.
- reward API stable catalog/asset identity/version.
- full badge lifecycle E2E.
- `L2-CORE-09` lexical image semantics يحتاج Academic Review قبل تغيير asset/content.

### W5

- classify historical seeds/runtime layers.
- no delete until dependency proof.
- legacy `/admin/account` archive/redirect only after proof.
- N+1 admin projection.
- notification GET mutation.
- stale/legacy test ownership.

### W6

Final exact-SHA gates: Backend + Frontend + Security + Alembic + Drift + Seed twice + Media + Audio + Integration + E2E + Mobile + Badges + Full Student Journey.

بعدها فقط A11 Railway.

---

## 9) قواعد غير قابلة للتجاوز

- لا Docker.
- لا Merge الآن.
- لا Deploy الآن.
- لا Railway الآن.
- لا حذف تسجيلات تاريخية أو Assessment/Reward evidence.
- لا تغيير canonical content 125 أو الرجوع عن اعتماد 2026-09-08 بدون قرار موثق.
- لا Temporary Audio Skip.
- لا mock ASR واعتباره production.
- لا machine-confidence academic truth.
- لا repair/overlay layer جديد بدل root fix.
- لا تغيير أسماء الدوال بلا سبب إذا أمكن حل الملكية دون كسر callers.
- افحص الكود الحقيقي ولا تعتمد على أسماء الملفات فقط.
- Git الحالي أعلى من تقرير أقدم إذا تعارضت الحالة التنفيذية، لكن القرارات الأكاديمية الموثقة لا تُلغى بصمت.
- لا تدّع أن اختبارًا مر إلا إذا شُغّل فعلًا.
- لا توقف التنفيذ بسبب خطوة توثيقية عادية؛ وثّق checkpoint ثم أكمل. توقف فقط عند dependency حقيقي، قرار أكاديمي/خارجي، أو Gate يتطلب موافقة المالك.

---

## 10) الملفات التي يجب أن تقرأها المحادثة الجديدة أولًا

اقرأ بالترتيب:

1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-10_A10_W1_FULL_AR.md` — هذا الملف.
2. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`.
3. `docs/maintenance/HIMMA_COMPREHENSIVE_REPOSITORY_AUDIT_2026-09-10_AR.md`.
4. `docs/maintenance/HIMMA_A03_AUDIO_SPEECH_REVIEW_ADAPTATION_AUDIT_2026-09-10_AR.md`.
5. `docs/maintenance/HIMMA_A08_FULL_JOURNEY_INTEGRATION_E2E_AUDIT_2026-09-10_AR.md`.
6. `docs/maintenance/HIMMA_A09_BRANCH_CLASSIFICATION_2026-09-10_AR.md`.
7. `docs/specs/SOURCE_OF_TRUTH.md`.
8. `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`.
9. `docs/maintenance/CANONICAL_CONTENT_EXECUTION_UPDATE_2026-09-10_AR.md`.
10. `AGENTS.md`, `.agents/rules/00-himma-core.md`, `.agents/rules/10-delivery-protocol.md`, `.agents/rules/20-security-quality.md`.

ثم افحص Git HEAD والملفات المعدلة في W1 مباشرة قبل أي تعديل جديد.

---

## 11) نقطة الاستكمال الدقيقة جدًا

**أنت داخل A10/W1، بعد إنشاء canonical latest-audio helpers، إصلاح human-review history، إصلاح assessment completion latest semantics، جعل assessment rerecord append-only/explicit، وإنشاء `level_completion.py`.**

**ابدأ من ربط Level Completion owner إلى Journey/Rewards، ثم numeric rubric evidence، ثم BE-003/profile/frontend rerecord، ثم regression tests.**

لا تعِد التدقيق من البداية، ولا تنتقل W2 قبل إغلاق W1 بدليل اختبارات حقيقي.