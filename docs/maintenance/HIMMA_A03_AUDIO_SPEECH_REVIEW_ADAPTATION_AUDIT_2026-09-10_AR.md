# منصة هِمّة — A03 تدقيق الصوت والتحليل والمراجعة البشرية والتكيّف

**التاريخ:** 2026-09-10  
**الحالة:** A03 AUDIT COMPLETE — FINDINGS VERIFIED / NO FIX APPLIED  
**المستودع:** `7eaur/himma-`  
**فرع المراجعة:** `audit/comprehensive-repository-review-2026-09-10`  
**HEAD الذي دُقق قبل كتابة التقرير:** `91ae00776f52ec01dc0fc2c6006f8376ba44636b`

> هذا تقرير تدقيق فقط. لم يتم فيه تعديل كود الإنتاج، ولم يتم Merge أو Deploy أو Railway setup، ولم يُعتمد أي Production ASR Provider.

---

## 1. العقد الأحدث الذي يجب الحفاظ عليه

العقد التشغيلي/الأكاديمي الحالي هو:

- `uploaded/pending` محايد أكاديميًا.
- لا يمنع التنقل العادي داخل المستوى.
- لا يمنع same-level support/reinforcement.
- يمنع فقط القرار غير القابل للعكس: promotion أو L3 completion.
- `rerecord_required` مهمة مؤجلة لا تصبح actionable حتى يفتحها الطالب صراحة.
- إعادة التسجيل تنشئ `AudioSubmission` جديدًا وتحافظ على القديم كتاريخ غير قابل للطمس.
- `graded` فقط يدخل evidence الأكاديمي.
- أحدث `AudioSubmission` هو الحالة الفعالة.
- لا عودة إلى Overlay blocking القديم.
- Machine confidence ليس Academic Truth قبل مزود/معايرة/اعتماد واضح.

---

## 2. مسار الصوت الذي تم تتبعه فعليًا

تم تتبع المسار عبر:

`student upload -> storage verification -> AudioSubmission -> speech discovery/enqueue -> DB queue -> worker -> provider boundary -> reference-guided alignment C/D/I/S -> SpeechAnalysis -> supervisor manual review -> graded/rerecord_required -> latest submission -> adaptation evidence -> promotion/L3 boundaries`

وشمل الفحص:

- `services/api/speech_provider.py`
- `services/api/speech_pipeline.py`
- `services/api/speech_alignment.py`
- `services/api/speech_worker.py`
- `services/api/speech_analysis.py`
- `services/api/db/speech_models.py`
- `services/api/recordings.py`
- `services/api/review.py`
- `services/api/audio_review_state.py`
- `services/api/activity_runtime.py`
- `services/api/assessment.py`
- `services/api/assessment_completion.py`
- `services/api/protected.py`
- `services/api/adaptation.py`
- `services/api/adaptation_runtime.py`
- `apps/web/src/app/admin/(dashboard)/audio-review/page.tsx`
- `apps/web/src/components/StudentRerecordTasks.tsx`
- صفحات الطالب للتقييم والأنشطة، واختبارات regression المرتبطة.

---

## 3. ما هو صحيح وموجود ولا يجب كسره

### 3.1 Core learning audio contract

`audio_review_state.py` هو أقرب مالك حالي للعقد الحديث: يفصل navigation عن academic evidence، ويستخدم أحدث submission، ويعامل pending/rerecord/graded حسب العقد الحالي.

`activity_runtime.py` يطبق السلوك الحديث في مسار التعلم:

- العنصر الذي لديه pending audio يبقى محجوزًا ولا يعاد اختياره.
- يمكن اختيار نشاط Core آخر في المستوى نفسه.
- `rerecord_required` لا يعيد الطالب تلقائيًا.
- الطالب يفتح مهمة rerecord صراحة.
- إعادة التسجيل تضيف `AudioSubmission` جديدًا بدل استبدال القديم.

### 3.2 Adaptation boundary

`adaptation_runtime.py` لا يستدعي unresolved-audio hold إلا عند promotion/L3 completion، وليس عند same-level support.

`adaptation.py` يستبعد pending/uploaded/rerecord من evidence باستخدام latest submission.

### 3.3 Speech pipeline الحقيقي

الموجود فعليًا:

- DB-backed durable queue.
- worker منفصل عن HTTP request path.
- retry/backoff/dead-letter.
- immutable machine `SpeechAnalysis` per submission.
- word-level reference-guided C/D/I/S alignment.
- provider absence لا يولد Fake score.
- injected fake provider موجود للاختبارات فقط، وليس fallback إنتاجيًا.

### 3.4 Production ASR غير مكتمل عمدًا

`build_provider()` لا يحتوي أي Production Provider معتمد. عند غياب الإعداد يعيد `UnconfiguredSpeechProvider`، وعند وضع اسم provider غير معتمد يرفض التشغيل عبر `ProviderNotConfigured`.

كما أن lexical alignment يتجاهل الحركات لأغراض مطابقة الكلمات، ولا يدّعي أنه phoneme/haraka scoring.

---

## 4. الفجوات المثبتة في A03

### AUD-A03-001 — P0 — VERIFIED

**المجال:** Assessment rerecord / History integrity  
**العَرَض:** مسار الاختبار القبلي/البعدي يعيد استخدام صف `AudioSubmission` نفسه عند إعادة التسجيل، ويستبدل `storage_key/file_size/mime_type/duration/submitted_at` ثم يعيده إلى `uploaded`.  
**السبب الجذري:** مسار `assessment.py` ما زال يملك state machine تاريخية مستقلة عن canonical audio lifecycle الحديث.  
**الطبقة التاريخية:** نموذج “invalid review -> reopen attempt -> replace recording”. يوجد regression test قديم يثبت صراحة أن عدد submissions يبقى `1` بعد rerecord.  
**الاعتماديات:** `assessment.py`, `review.py`, `assessment_completion.py`, `protected.py`, assessment frontend.  
**مالك الحقيقة الصحيح:** shared canonical audio-review lifecycle، وليس route assessment منفردًا.  
**Root Fix لاحقًا:** append-only rerecord بعد explicit open؛ القديم immutable؛ كل consumer يستخدم latest submission.  
**Migration/History Risk:** HIGH. لا يمكن اختلاق تسجيلات تاريخية سبق أن طُمست؛ يجب الحفاظ على البيانات الحالية كما هي ومنع طمس جديد.  
**Required Tests:** invalid -> deferred task -> explicit open -> new submission -> old retained -> latest drives review/score/display.  
**Release Risk:** P0 لأن السلوك الحالي قادر على طمس سجل صوتي أكاديمي.  
**Execution Wave:** A10 Wave 1.

### AUD-A03-002 — P1 — VERIFIED

**المجال:** Assessment latest-submission semantics  
**العَرَض:** عدة أسطح في assessment/profile/completion تعتمد `first()` أو تفحص جميع submissions التاريخية بدل أحدث submission فقط. عند تطبيق append-only بشكل صحيح، قد يبقى old `rerecord_required` حاجبًا للأكمال أو العرض، أو قد يقرأ scorer صفًا قديمًا.  
**السبب الجذري:** `audio_review_state.latest_audio_submission()` لم يصبح بعد مالكًا مشتركًا لكل مسارات assessment.  
**الطبقة التاريخية:** core runtime انتقل للعقد الحديث بينما assessment/protected/completion بقيت على queries تاريخية مستقلة.  
**الاعتماديات:** AUD-A03-001.  
**Root Fix لاحقًا:** توحيد latest-submission selector وsession summary لكل assessment navigation/progress/display/completion/scoring.  
**Migration/History Risk:** متوسط؛ تعديل القراءة/الاشتقاق فقط يجب ألا يحذف أي صف.  
**Required Tests:** old rerecord + new uploaded + new graded، وإثبات أن كل API/UI/scoring يرى الأحدث فقط.  
**Execution Wave:** A10 Wave 1.

### AUD-A03-003 — P1 — VERIFIED

**المجال:** Human review -> rerecord lifecycle  
**العَرَض:** `review.py` عند invalid review يضع `attempt.status = in_progress` ويمسح `completed_at` فورًا، والـAdmin UI يقول إن المحاولة “سيُعاد فتحها”. هذا يطابق العقد القديم لا العقد الحالي deferred explicit rerecord.  
**السبب الجذري:** endpoint المراجعة اليدوية لم يُنقل كاملًا إلى state machine الجديدة.  
**الطبقة التاريخية:** reopen-at-review behavior.  
**الاعتماديات:** AUD-A03-001/002.  
**Root Fix لاحقًا:** invalid review يغير latest submission إلى `rerecord_required` ويحفظ audit فقط؛ actionability تبدأ عند explicit learner open وفق contract موحد.  
**Required Tests:** invalid review وحده لا يفتح المهمة تلقائيًا؛ explicit open هو الذي يجعلها actionable.  
**Execution Wave:** A10 Wave 1.

### AUD-A03-004 — P1 — VERIFIED

**المجال:** Machine analysis / Human adjudication integration  
**العَرَض:** `SpeechAnalysis` والـqueue يعملان كمسار موازٍ، لكن قائمة المراجعة اليدوية لا تعرض transcript/alignment/confidence/decision، و`AudioReview` لا يرتبط مباشرة بنتيجة machine analysis التي شاهدها المراجع. كذلك يستطيع المشرف مراجعة submission قبل أن يكتشفه worker؛ إذا أصبح status `graded` فلن يكتشفه `discover_jobs()` لاحقًا لأنه يبحث عن `uploaded` فقط.  
**السبب الجذري:** P07 speech pipeline بُني كsubsystem مساعد قبل توحيد review/adjudication owner.  
**الطبقة التاريخية:** human-only review موجود قبل speech pipeline.  
**مالك الحقيقة الصحيح:** unified review/adjudication service؛ machine analysis advisory evidence فقط حتى اعتماد مستقل.  
**Root Fix لاحقًا:** إظهار evidence الآلي immutable للمشرف، ربط adjudication بما عُرض، حفظ provider/model/calibration metadata، واستمرار human authority حتى قرار اعتماد واضح.  
**Required Tests:** human-only path يعمل بدون provider؛ machine fixture يظهر للمراجع؛ human override محفوظ ومدقق؛ لا auto-grade.  
**Execution Wave:** A10 Wave 2.

### AUD-A03-005 — P1 — VERIFIED / RELEASE-GATE RISK

**المجال:** Calibration governance  
**العَرَض:** `_calibrated_decision()` يعتبر وجود `HIMMA_ASR_CONFIDENCE_THRESHOLD` و`HIMMA_ASR_CALIBRATION_VERSION` كافيًا لإنتاج `auto_accepted` داخل machine analysis، دون registry/checksum يثبت أن هذه المعايرة معتمدة فعليًا.  
**مهم:** هذا لا يغير الدرجة الأكاديمية اليوم؛ `speech_pipeline` لا يكتب score الطالب و`AudioSubmission` يبقى في human-review lifecycle. الخطر هو أن اسم القرار قد يُستهلك لاحقًا كسلطة أكاديمية بالخطأ.  
**السبب الجذري:** configuration string مساوية حاليًا لمفهوم governance approval داخل machine subsystem.  
**Root Fix لاحقًا:** approved provider/model/calibration registry أو artifact attestation؛ وإبقاء machine decision advisory حتى يثبت الاعتماد.  
**Required Tests:** env عشوائي لا يمنح academic acceptance؛ calibration معتمدة فقط يمكن أن تغير machine advisory state؛ human authority منفصلة.  
**Execution Wave:** A10 Wave 2.

### AUD-A03-006 — P1 — VERIFIED

**المجال:** Speech queue concurrency/idempotency  
**العَرَض:** `claimable_job_ids()` يعمل select عاديًا ثم `process_job()` يغير الحالة في خطوة لاحقة؛ لا `FOR UPDATE SKIP LOCKED` ولا lease/claim token. أكثر من worker يمكنه التقاط job نفسه، استدعاء provider مرتين، ثم التنافس على unique `SpeechAnalysis`. كما أن `enqueue_submission()` check-then-insert يعتمد على unique constraint دون recovery واضح لـ`IntegrityError` المتزامن.  
**السبب الجذري:** durable persistence موجودة لكن atomic claim protocol غير مكتمل.  
**مالك الحقيقة الصحيح:** speech queue/worker.  
**Root Fix لاحقًا:** atomic PostgreSQL claim + lease/recovery، وidempotent result write.  
**Required Tests:** عاملان على job واحد -> provider call واحدة/result واحدة؛ crash/lease recovery؛ concurrent enqueue لا يفشل بصورة غير مضبوطة.  
**Execution Wave:** A10 Wave 2.

### AUD-A03-007 — P2 — VERIFIED

**المجال:** Speech retry/operator recovery  
**العَرَض:** manual retry يعيد status إلى `queued` لكنه لا يعيد attempt budget؛ `blocked_provider` لا يعود claimable تلقائيًا إذا تم اعتماد provider لاحقًا؛ والأخطاء غير المصنفة خارج exceptions المعروفة تعتمد على rollback الخارجي ولا تُسجل كحالة queue دائمة واضحة.  
**السبب الجذري:** operator recovery contract لم يكتمل.  
**Root Fix لاحقًا:** requeue policy صريحة، reset/renew attempt budget بقرار مدقق، provider-configuration recovery، وحالة durable للأخطاء غير المتوقعة.  
**Required Tests:** dead-letter manual retry، blocked-provider recovery، unexpected exception audit state.  
**Execution Wave:** A10 Wave 2.

### AUD-A03-008 — P1 — BLOCKED BY PRODUCT/PRIVACY/ACADEMIC DECISION

**المجال:** Production ASR  
**العَرَض:** لا يوجد Production ASR Adapter معتمد، ولا calibration representative معتمدة، ولا phoneme/haraka scoring معتمد.  
**السبب:** هذا ليس bug يجب ترقيعه؛ القرار OI-02 لم يُغلق: provider/contract/privacy/cost/recording transfer/retention/calibration.  
**مالك الحقيقة الصحيح:** Product + Privacy + Academic + Speech integration.  
**Root Fix لاحقًا:** قرار مزود موثق ثم adapter واختبارات privacy/integration/calibration. إذا لم يعتمد مزود، يبقى المسار اليدوي authoritative ولا يدعى اكتمال ASR.  
**Required Tests:** provider contract, representative Arabic calibration, failure/privacy/retention, human override.  
**Release Risk:** يمنع ادعاء automated ASR production readiness، لكنه لا يمنع تشغيل المسار اليدوي إذا كان ذلك قرار الإصدار المعتمد.  
**Execution Wave:** A10/A11 حسب القرار.

### AUD-A03-009 — P0 — VERIFIED

**المجال:** Academic adaptation evidence from graded audio  
**العَرَض:** المراجعة البشرية تحسب `rubric_score = 1 - errors/target_units`، لكنها تكتب `AttemptResponse.is_correct = rubric_score > 0`. بعد ذلك `_attempt_signal()` في `adaptation.py` لا يقرأ `AudioReview.rubric_score`؛ بل يحول `response.is_correct` إلى boolean score. النتيجة: قراءة حصلت على `0.10` وقراءة حصلت على `1.00` يمكن أن تدخلا كأن كلتيهما `100%` على خطوة صوتية أحادية بعد أن تصبح `graded`.  
**الأثر:** evidence التكيفي قد يتضخم ويؤثر في mastery/support/promotion decisions.  
**السبب الجذري:** generic boolean AttemptResponse بقي بوابة التكيف بعد إضافة rubric audio review، ولم يُعرّف canonical graded-audio evidence owner.  
**الطبقة التاريخية:** boolean correctness contract أقدم من C/D/I/S rubric.  
**مالك الحقيقة الصحيح:** canonical adaptation evidence builder الذي يقرأ latest graded `AudioReview.rubric_score` أو policy أكاديمية صريحة معتمدة، لا `> 0`.  
**Root Fix لاحقًا:** توحيد evidence value للصوت؛ لا تحويل أي positive rubric إلى full correctness. أي threshold بديل يحتاج قرارًا أكاديميًا موثقًا.  
**Migration/History Risk:** HIGH؛ قد توجد AdaptationDecision تاريخية بُنيت على evidence متضخم. لا تُعاد كتابتها بصمت. يجب أولًا تحديد هل توجد بيانات دراسة فعلية، ثم versioned recalculation/migration فقط بقرار موثق إن لزم.  
**Required Tests:** 1.0/0.5/0.1 rubric تعطي evidence متمايزًا؛ pending مستبعد؛ latest graded فقط؛ promotion tests تستخدم القيمة الصحيحة.  
**Release Risk:** P0 academic correctness.  
**Execution Wave:** A10 Wave 1.

### AUD-A03-010 — P2 — CARRY TO A07

**المجال:** Storage/security/observability  
**العَرَض:** `recordings.py` يكرر إعداد boto3 بدل shared storage abstraction، و`stream-by-key` يسمح للمشرف بطلب أي key يبدأ بـ`audio/` دون ربطه بصف DB محدد، كما أن speech queue لا تملك metrics/lag/worker health واضحة.  
**القرار:** لا إصلاح هنا؛ تُحمل هذه النقاط إلى A07 Security/Performance/Observability لتحديد severity النهائية وسياق Railway.

---

## 5. ملاحظة مهمة: الاختبار والتعلم ليسا state machine واحدة حاليًا

أهم نتيجة معمارية في A03 هي وجود مسارين:

1. **Core learning — حديث نسبيًا**: latest submission + append-only rerecord + explicit open + same-level continuation.
2. **Pre/Post assessment — legacy**: pending blocks السؤال التالي، invalid review يعيد فتح Attempt، rerecord يستبدل صف AudioSubmission نفسه، وبعض الـdisplay/completion queries لا تستخدم latest semantics.

كون الاختبار قد يختار انتظار review قبل الاستمرار قد يكون قرارًا بحثيًا مشروعًا، لكن **طمس التسجيل السابق وغياب latest-submission semantics ليسا قرارًا مقبولًا** وفق العقد الأحدث.

---

## 6. Frontend findings

### Admin audio review

الإيجابي:
- يستخدم AdminUI shell.
- يعرض النص المرجعي والصوت.
- يسمح بإدخال C/D/I/S وملاحظات النطق والطلاقة.

الفجوات:
- لا يعرض machine transcript/alignment/confidence/analysis metadata.
- copy إعادة التسجيل ما زال يقول إن المحاولة “سيُعاد فتحها”.

### Student rerecord

`StudentRerecordTasks` يطبق explicit/deferred contract لكنه يعمل فقط عندما `active_session.session_type === core` ويستدعي `/activities/.../rerecord-*`.

بالتالي لا يوجد في هذا المكون مسار assessment rerecord حديث يعادل core contract، وهذا يتفق مع وجود legacy assessment state machine المثبتة أعلاه.

### Legacy overlay

`StudentAudioReviewOverlay.tsx` ما زال موجودًا في الشجرة، لكن layout الطالب الحالي لا يركبه. لذلك يصنف **legacy/dead-code candidate فقط**، ولا نسجل أنه blocking فعال دون dependency proof في A04/A09.

---

## 7. الاختبارات الموجودة مقابل العقد

توجد regression coverage جيدة للمسار الحديث في Core:

- pending neutral + continue.
- deferred rerecord + explicit open.
- new AudioSubmission مع الاحتفاظ بالقديم.
- graded-only adaptation evidence.
- unresolved audio holds promotion ولا يمنع same-level support.

لكن مسار Assessment لديه اختبار تاريخي يثبت السلوك القديم “reopen + replace same submission”، لذلك وجود الاختبار ليس دليل صحة؛ هو دليل أن العقد القديم ما زال encoded في test suite.

اختبارات speech pipeline تستخدم injected fixture provider وتثبت absence/retry/calibration behavior، لكنها لا تمثل Production Provider معتمدًا.

**لم يتم في جلسة هذا التدقيق تشغيل Test Suite جديدة.** النتائج المذكورة هنا Static/contract audit مبنية على الكود والاختبارات الموجودة، ولا تُكتب كـPASS تشغيل جديد.

---

## 8. Owner-of-truth map المقترح قبل الإصلاح

| المسؤولية | المالك الحالي الأقرب للصحة | المشكلة الحالية |
|---|---|---|
| Effective audio state | `audio_review_state.py` | غير مستخدم في كل assessment surfaces |
| Learning rerecord lifecycle | `activity_runtime.py` + shared helper | صحيح نسبيًا، لا يُنسخ إلى assessment يدويًا |
| Human review | `review.py` | ما زال يحمل reopen semantics ولا يرى machine evidence |
| Assessment audio lifecycle | `assessment.py` | legacy owner يجب تفكيك ازدواجه لاحقًا |
| Assessment completion/scoring | `assessment_completion.py` | يحتاج latest-only semantics |
| Machine analysis | `speech_pipeline.py`/worker/models | حقيقي لكن advisory وغير موحد مع human review |
| Adaptation audio evidence | `adaptation.py` | P0: يختزل rubric إلى bool عبر response |
| Irreversible boundary | `adaptation_runtime.py` | السلوك الحالي صحيح ويجب الحفاظ عليه |

---

## 9. قرار A03

**A03 deep audit مكتمل من ناحية الفهم والتوثيق المطلوبين قبل الإصلاح.**

لم تُطبق أي صيانة. لا يزال A03 يحتوي P0/P1 يجب أن تدخل Master Gap Register وموجات A10، وعلى رأسها:

1. منع طمس تسجيل assessment عند rerecord.
2. إصلاح academic evidence للصوت graded في adaptation.
3. توحيد latest-submission semantics في assessment/profile/completion.
4. نقل rerecord إلى deferred explicit lifecycle موحد.
5. ربط machine evidence بالمراجعة البشرية دون منحه سلطة أكاديمية غير معتمدة.
6. hardening للـqueue قبل أي worker إنتاجي متعدد النسخ.

**نقطة الاستكمال بعد هذا التقرير: A04 — Admin / Frontend / Mobile detailed audit، وليس A10.**
