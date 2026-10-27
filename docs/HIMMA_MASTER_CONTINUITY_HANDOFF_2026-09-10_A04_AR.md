# منصة هِمّة — Master Continuity Handoff بعد إغلاق A03

**التاريخ:** 2026-09-10  
**الحالة:** AUDIT IN PROGRESS — A03 COMPLETE, NEXT A04  
**المستودع:** `7eaur/himma-`  
**فرع المراجعة:** `audit/comprehensive-repository-review-2026-09-10`  
**HEAD قبل إنشاء هذا الملف:** `6511d16c6656e2fbbcf547749523cfe318802dbb`

> إذا أصبح Git HEAD أحدث من القيمة أعلاه فـGit الحالي هو الحقيقة التنفيذية، مع بقاء القرارات الأكاديمية/المنتجية الأحدث حاكمة على الملفات التاريخية الأقدم.

---

## 1. قواعد الاستمرارية غير القابلة للتفاوض

- لا Docker.
- لا Merge أثناء A00–A09.
- لا Deploy ولا Railway أثناء التدقيق.
- لا حذف تاريخ أكاديمي أو تسجيلات قديمة.
- لا تغيير content contract الكانوني بلا سبب موثق.
- لا Fake ASR Provider.
- لا PASS دون تشغيل فعلي.
- لا حذف ملف/فرع لأن اسمه يبدو قديمًا؛ افهم dependency/history أولًا.
- فرع نموذج الصوت الاصطناعي المؤقت مستبعد من الدمج.
- لا Repair/Overlay Runtime جديد.

---

## 2. الحقيقة الحالية التي لا تعاد من الصفر

- Canonical Content الحالي بعد اعتماد 2026-09-08 = **125 عنصرًا**.
- تم تنفيذ Canonical compiler/publisher، media mapping، POST-Q14، القصص/sequences، audio navigation، rerecord، adaptation/promotion boundaries، frontend، dependencies وCI بدون Docker.
- `seed_all.py` هو canonical entrypoint الحالي؛ ملفات seed/repair القديمة لا تحذف قبل تصنيفها.
- AdminUI موجود ويجب البناء فوقه لاحقًا، لا إنشاء Design System ثالث.
- Railway هدف A11 فقط بعد البوابات النهائية.

---

## 3. حالة المراحل

| المرحلة | الحالة الحالية |
|---|---|
| A00 Baseline / Governance / CI | مفحوصة مبدئيًا |
| A01 Backend ownership / routes | جزئي / يحتاج consolidation plan بعد اكتمال التدقيق |
| A02 Seeds / Migrations / Canonical | جرد متقدم، import graph موجود، لا إصلاح بعد |
| A03 Audio / Speech / Review / Adaptation | **AUDIT COMPLETE — findings verified, no fix applied** |
| A04 Admin / Frontend / Mobile | **NEXT / IN PROGRESS** |
| A05 Rewards / Badges | جرد أولي موجود، end-to-end audit مطلوب |
| A06 Media / Images | جرد canonical أولي موجود، manual semantic review مطلوب |
| A07 Security / Performance / Accessibility / Observability | لم يكتمل |
| A08 Full Journey / Integration / E2E | لم يكتمل |
| A09 Branch-by-branch review | لم يبدأ بالكامل |
| A10 Corrective Maintenance | ممنوع البدء قبل Master Gap Register |
| A11 Final Release / Railway | ممنوع الآن |

---

## 4. عقد الصوت الأحدث الذي يجب الحفاظ عليه

- uploaded/pending محايد أكاديميًا.
- لا يمنع التنقل داخل المستوى ولا same-level support/reinforcement.
- unresolved audio يمنع فقط promotion أو L3 completion.
- rerecord_required مهمة مؤجلة؛ الطالب يفتحها صراحة.
- rerecord ينشئ AudioSubmission جديدًا ويحفظ القديم.
- graded فقط يدخل evidence الأكاديمي.
- latest AudioSubmission هو الحالة الفعالة.
- لا عودة إلى Overlay blocking القديم.
- machine confidence لا يصبح academic truth قبل اعتماد provider/calibration/governance واضح.

---

## 5. A03 — ما ثبت إيجابيًا

- `audio_review_state.py` يمثل العقد الحديث ويحتوي latest-submission helpers.
- Core `activity_runtime.py` يواصل same-level work مع pending audio، ويطبق deferred explicit rerecord، ويضيف submission جديدًا.
- `adaptation_runtime.py` يحجز فقط promotion/L3 completion عند unresolved audio.
- Speech DB queue/worker/retry/dead-letter/alignment/SpeechAnalysis موجودة فعليًا.
- C/D/I/S reference-guided word alignment موجود.
- لا Production ASR Adapter معتمد؛ `build_provider()` يفشل مغلقًا ولا يخترع نتيجة.
- phoneme/haraka scoring غير معتمد ولا يُستنتج من lexical alignment.

التقرير الكامل:
`docs/maintenance/HIMMA_A03_AUDIO_SPEECH_REVIEW_ADAPTATION_AUDIT_2026-09-10_AR.md`

والفجوات مسجلة أيضًا في:
`docs/maintenance/HIMMA_COMPREHENSIVE_REPOSITORY_AUDIT_2026-09-10_AR.md`

---

## 6. A03 — الفجوات الحرجة التي لا تصلح بPatch سريع

### AUD-A03-001 — P0
Assessment rerecord يستبدل نفس AudioSubmission ويطمس بيانات التسجيل السابق. العقد الصحيح append-only.

### AUD-A03-009 — P0
المراجعة البشرية تحفظ rubric مستمرًا، لكن adaptation الحالي يمر عبر `response.is_correct = rubric_score > 0` ثم يحوله إلى full boolean correctness. قراءة 0.10 و1.00 قد تتحولان إلى evidence متساوٍ على خطوة صوتية أحادية. يجب توحيد graded-audio evidence owner لاحقًا، وعدم إعادة كتابة قرارات تاريخية بصمت.

### AUD-A03-002 — P1
Assessment/profile/completion لا تستخدم latest-submission semantics بشكل موحد؛ بعضها `first()` وبعضها يفحص كل التاريخ.

### AUD-A03-003 — P1
Human invalid review ما زال يعيد فتح Attempt فورًا بدل deferred explicit rerecord semantics.

### AUD-A03-004 — P1
SpeechAnalysis منفصل عن human review: Admin لا يرى transcript/alignment/confidence ولا يوجد adjudication link واضح.

### AUD-A03-005 — P1
وجود threshold + calibration-version env يمكن أن يولد machine `auto_accepted` داخل subsystem دون attested calibration registry. لا score mutation اليوم، لكنه خطر release/governance.

### AUD-A03-006 — P1
Speech queue ليس له atomic worker claim/lease؛ أكثر من worker قد يستدعي provider لنفس job.

### AUD-A03-007 — P2
manual retry budget/provider recovery/unexpected-error durability تحتاج عقدًا أوضح.

### AUD-A03-008 — P1 BLOCKED
لا Production ASR Provider/Calibration معتمد. لا تحاول “إغلاق” ذلك بمزود وهمي.

### AUD-A03-010 — Carry to A07
storage abstraction / `stream-by-key` scope / worker observability تُراجع أمنيًا وتشغيليًا في A07.

---

## 7. أهم نتيجة معمارية من A03

هناك مساران مختلفان يجب توحيدهما لاحقًا من مصدر حقيقة واحد:

1. Core learning: حديث — latest + append-only + explicit rerecord + same-level continuation.
2. Pre/Post assessment: تاريخي — reopen/mutate-same-submission وبعض all/first submission queries.

قد يكون blocking داخل الاختبار حتى review قرارًا بحثيًا مشروعًا، لكن طمس التسجيل السابق ليس مشروعًا ولا يتوافق مع العقد الأحدث.

---

## 8. اختبارات A03

- توجد regression tests جيدة لمسار Core الحديث وحدود promotion/pending.
- يوجد test تاريخي في assessment يفرض reopen + replace same submission، وهو جزء من legacy contract لا دليل صحة.
- speech tests تستخدم injected fixture provider فقط.
- **لم يتم في جلسة A03 الحالية تشغيل Test Suite جديدة.** لا تُحوّل static audit إلى PASS تشغيل جديد.

---

## 9. نقطة الاستكمال الدقيقة الآن — A04 فقط

ابدأ A04 التفصيلي، ولا تصلح P0/P1 بعد.

### المطلوب

1. بناء Matrix لكل Admin route:
   - route
   - owner/page/component
   - AdminUI primitives المستخدمة
   - local CSS/system duplication
   - loading/error/empty states
   - keyboard/focus
   - RTL
   - responsive behavior
   - mobile risk
   - API dependencies
   - tests/evidence

2. تدقيق تفصيلي للصفحات على الأقل:
   - `/admin`
   - `/admin/students`
   - `/admin/students/new`
   - `/admin/students/[id]`
   - `/admin/reports`
   - `/admin/skill-reports`
   - `/admin/audio-review`
   - `/admin/content-preview`
   - `/admin/settings`
   - `/admin/account`
   - `/admin/login`

3. Student Details أولوية P1:
   - 320
   - 360
   - 390
   - 430
   - 768
   - Desktop

   تحقق من:
   - no horizontal overflow
   - tabs usable
   - summary cards
   - action stacking
   - forms/input widths
   - modals
   - keyboard/focus/error states
   - RTL

4. Settings:
   - أثبت أين أنشأ Design System ثانيًا بدل AdminUI.
   - لا تصلحه الآن.

5. `/admin/account`:
   - route/link/test/dependency scan قبل أي قرار حذف/redirect.

6. Student frontend:
   - assessment/activity/rerecord/mobile states
   - لا تعيد Overlay blocking.

### مخرجات A04

- تحديث Master Audit.
- تحديث التقرير المتخصص A04/A05 الحالي أو إصدار ملحق A04 إذا لزم.
- Master Gap entries بملاك حقيقة واضحين.
- لا production code fixes.

---

## 10. بعد A04

التسلسل الإلزامي:

A04 → A05 badges end-to-end → A06 manual semantic media → A07 → A08 → A09 → Master Gap Register → A10 → final gates → A11/Railway.

لا يُعكس هذا الترتيب بسبب ظهور فجوة P0 أثناء التدقيق؛ P0 توثق الآن وتدخل أول موجة A10 بعد اكتمال صورة A00–A09، ما لم يظهر خطر نشط يتطلب إيقافًا أمنيًا منفصلًا.
