# منصة هِمّة — MASTER CONTINUITY HANDOFF بعد إغلاق A00–A09

**التاريخ:** 2026-09-10  
**الحالة:** `A00–A09 AUDIT COMPLETE / A10 W1 NEXT — NO MERGE — NO DEPLOY`  
**المستودع الرسمي:** `7eaur/himma-`  
**فرع التنفيذ قبل التدقيق:** `integration/canonical-content-2026-09-08@7cb2192b0c31bc85dcf98a470023e9cc6f1598e0`  
**فرع التدقيق/الصيانة الحالي:** `audit/comprehensive-repository-review-2026-09-10`

> لا تبدأ من الصفر. Git الحالي هو الحقيقة التنفيذية إذا تقدم عن SHA مذكور هنا. اقرأ Master Gap Register والتقرير الجامع ثم نفذ A10/W1 فقط. لا تعد A00–A09.

---

## 1. ما هي هِمّة والعقود التي لا تتغير بلا قرار مستقل

هِمّة منصة تعليمية عربية للصف الثالث وصعوبات القراءة:

`كود الطالب → اختبار قبلي → تصنيف → L1/L2/L3 → تقوية تكيفية → اختبار بعدي → تقارير`

المحتوى الكانوني الحالي بعد اعتماد 2026-09-08:

- Pretest: 30.
- Core: 30 = 10 لكل مستوى.
- Reinforcement: 35 = L1 12 / L2 11 / L3 12.
- Posttest: 30.
- الإجمالي: **125 عنصرًا**.
- 44 مهارة.

التصنيف الأساسي:

- <50% → L1.
- 50–<80% → L2.
- 80–100% → L3.

قواعد ثابتة:

- لا Docker.
- لا Merge/Deploy قبل انتهاء A10 وFinal Gates.
- لا repair/overlay runtime جديد.
- لا حذف history أو old recordings.
- pending/uploaded audio محايد أكاديميًا.
- pending audio لا يمنع same-level navigation/support/reinforcement.
- unresolved audio يمنع فقط promotion/L3 completion عند irreversible boundary.
- `rerecord_required` deferred task يفتحها الطالب صراحة.
- rerecord يجب أن ينشئ AudioSubmission جديدًا ويحفظ القديم.
- latest AudioSubmission هو active state.
- graded فقط يدخل evidence الأكاديمي.
- لا blocking overlay قديم.
- لا Production ASR Provider معتمد.
- machine confidence ليس academic truth.
- early promotion في L1/L2 يبقى معتمدًا؛ L3 يحتاج 10 Core.

---

## 2. مصادر الحقيقة الحالية

اقرأ عند الاستكمال بالترتيب:

1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-10_AUDIT_AR.md`
2. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
3. `docs/maintenance/HIMMA_COMPREHENSIVE_REPOSITORY_AUDIT_2026-09-10_AR.md`
4. التقرير المتخصص للموجة المطلوبة.
5. `docs/maintenance/HIMMA_A09_BRANCH_CLASSIFICATION_2026-09-10_AR.md`
6. `docs/maintenance/HIMMA_A08_FULL_JOURNEY_INTEGRATION_E2E_AUDIT_2026-09-10_AR.md`
7. `docs/maintenance/HIMMA_A07_SECURITY_PERFORMANCE_ACCESSIBILITY_OBSERVABILITY_AUDIT_2026-09-10_AR.md`
8. `docs/maintenance/HIMMA_A06_IMAGE_MEDIA_DEEP_AUDIT_2026-09-10_AR.md`
9. `docs/maintenance/HIMMA_A04_ADMIN_MOBILE_DEEP_AUDIT_2026-09-10_AR.md`
10. `docs/maintenance/HIMMA_A04_A05_ADMIN_BADGES_AUDIT_2026-09-10_AR.md`
11. `docs/maintenance/HIMMA_A03_AUDIO_SPEECH_REVIEW_ADAPTATION_AUDIT_2026-09-10_AR.md`
12. A02 inventories/import graph ثم canonical handoffs القديمة عند الحاجة التاريخية.

---

## 3. ماذا أُغلق في التدقيق؟

- A00 Baseline/CI — مغلق.
- A01 Backend ownership — مغلق كتدقيق.
- A02 Seeds/Migrations/Legacy imports — مغلق كتدقيق.
- A03 Audio/Speech/Human Review/Adaptation — مغلق كتدقيق.
- A04 Admin/Student Details/Mobile — مغلق كتدقيق.
- A05 Rewards/Badges — مغلق كتدقيق.
- A06 Images/Media — مغلق كتدقيق.
- A07 Security/Performance/Accessibility/Observability — مغلق كتدقيق.
- A08 Full Journey/Integration/E2E — مغلق كتدقيق.
- A09 All Branches — مغلق كتدقيق.
- Master Gap Register — موجود ومكتمل بما يكفي لبدء A10.

**لا ترجع لأي مرحلة من A00–A09 إلا للتحقق المحدد أثناء إصلاح مرتبط بها.**

---

## 4. CI المرجعي

المرجع الفعلي: Actions run `34419490966` على `7cb2192...`:

- Security PASS.
- Frontend PASS.
- canonical/migrations/drift/seed idempotency PASS.
- Backend 823 passed / 2 failed / 825.
- Integration SKIPPED.

الفشلان:

- `AUD-BE-003`: pending audio summary.
- `AUD-BE-004`: recovery test uses old 105 baseline for PRE-Q05.

`test_m09_full_single_candidate_journey.py` نجح في نفس run، لكن لا يعتبر Browser Journey كاملًا.

فرع `audit/*` لا يُشغل تلقائيًا من push triggers الحالية، لذلك لا يوجد exact-head Green للفرع الحالي بعد commits التوثيقية. Final exact-SHA gates مطلوبة بعد A10.

---

## 5. أخطر الفجوات التي تبدأ بها A10/W1

### P0 — Assessment audio history

`assessment.py` ما زال في rerecord يستبدل نفس AudioSubmission. المطلوب:

- invalid review = latest submission يصبح `rerecord_required` فقط.
- لا reopen تلقائي للمحاولة عند المراجعة.
- learner يفتح rerecord task صراحة.
- rerecord ينشئ AudioSubmission جديدًا ويربطه بالسياق نفسه دون طمس القديم.
- كل display/progress/completion/scoring يستخدم latest submission.

### P0 — Numeric rubric evidence

يوجد مسار يحول `rubric_score > 0` إلى boolean correct. لا يجوز أن تتساوى 0.10 و1.00 أكاديميًا. أصلح owner الأكاديمي نفسه ولا تضف exception patch.

### P1 — Pending audio summary

افصل:

- navigation resolver: ما الخطوة التالية القابلة للتنفيذ؟
- session review summary: كم تسجيلًا أحدثه pending/rerecord/graded؟

وجود step actionable لا يمحو pending count.

### P1 — Level completion truth

Journey/Rewards/UI يجب أن تستهلك owner واحدًا لحالة اكتمال المستوى. لا تجعل الشارة تشترط 10 إذا كان completion المعتمد حصل بالترقية المبكرة 6–9 في L1/L2. لا تلغ early promotion.

---

## 6. بقية الموجات بعد W1

### W2 — Security / Speech boundaries

- auth rate limiting.
- auth/session revocation version عند password/access-code rotation.
- production ENV/readiness security contract.
- legacy presigned recordings max-size/removal بعد dependency proof.
- sanitized errors + correlation IDs.
- atomic speech worker claims/retry contract.
- Production ASR يبقى HOLD.

### W3 — Admin / Student UX / Accessibility / Web reliability

- AdminUI owner واحد.
- Student Details partial-failure states.
- full responsive matrix 320/360/390/430/768/Desktop.
- dialog keyboard lifecycle.
- Settings semantics.
- media BFF cache policy.
- reduced motion + accessible semantic colors + progressbar semantics.

### W4 — Rewards / Badges / Media

- canonical Reward Catalog.
- approved BDG assets.
- L3 naming resolution.
- Student/Admin visual badges.
- reward failure states.
- lexical-stimulus media role after academic approval.
- badge full E2E.

### W5 — Historical cleanup / Performance / Test ownership

- runtime layer extraction.
- seed/projection classification.
- legacy account redirect/archive.
- duplicate/unused asset deletion only after proof.
- query/polling performance.
- archive loose/obsolete tests after replacement proof.

### W6 — Final Gates

Backend، Frontend، Security، Migrations، Drift، Seed-twice، Media، Audio، Integration، E2E، Mobile، Badges، Full Student Journey على exact SHA.

ثم A11 فقط.

---

## 7. A09 Branch Review — قرار نهائي حتى إشعار آخر

تم فحص 20 فرعًا بالcompare.

الفروع القديمة B01/B02/B03/Stage/Recovery/official reconciliation/integration canonical كلها contained (`ahead_by=0`) بالنسبة لفرع المراجعة: **لا Merge مطلوب**.

`b04/asr-pipeline`: unique commits توثيقية تاريخية فقط: لا Merge.

Speech/Pronunciation labs:

- `m08/speech-lab-google-stt`
- `b08/speech-lab-google-stt`
- `b08/arabic-pronunciation-lab`
- `b08/acoustic-pronunciation-evidence`

كلها experimental و**EXCLUDE FROM MERGE** حتى اعتماد مستقل للـASR.

`deployment/platform-sandbox`: لا Merge؛ يحمل Docker/temp-audio-skip وتجربة نشر قديمة. فقط reference محدود لـA11.

لا تنظف الفروع الآن. cleanup بعد final branch/Green/backup.

---

## 8. A08 Journey truth

لا تخلط الاختبارين:

- `vertical-slice.spec.ts`: browser/UI/recording/human review/جزء learning قوي.
- `test_m09_full_single_candidate_journey.py`: domain longitudinal قوي حتى L3/posttest/reporting، لكنه يعتمد persisted assessment snapshots ولا ينفذ Browser Posttest كاملًا.

Final Gate يحتاج deterministic full live journey لطالب واحد عبر المنتج كله، لا مجرد جمع نجاح الاختبارين.

---

## 9. ما لا تفعله أثناء A10

- لا تنقل كود speech lab من فرع تجريبي.
- لا تضف mock provider.
- لا تجعل pending audio blocking داخل المستوى.
- لا تمسح old AudioSubmission.
- لا تحول numeric score إلى pass/fail مبسط دون contract أكاديمي.
- لا تغيّر 125 canonical content بلا قرار موثق.
- لا تستبدل صورة لمجرد أن هناك أصلًا غير مستخدم.
- لا تحذف `/admin/account` قبل dependency proof.
- لا تبن Settings كنظام تصميم ثانٍ.
- لا تستخدم Docker.
- لا Railway/Deploy الآن.

---

## 10. نقطة الاستكمال الدقيقة الآن

**ابدأ A10 / W1 مباشرة.**

الترتيب التنفيذي:

1. اقرأ الكود الحالي لـ`assessment.py`, `review.py`, `audio_review_state.py`, `assessment_completion.py`, `protected.py` والاختبارات ذات الصلة.
2. صمم shared latest-submission/rerecord lifecycle بدل patch route-local.
3. أصلح append-only rerecord/history.
4. أصلح pending review summary.
5. أصلح numeric rubric evidence.
6. وحّد level completion owner لـJourney/Rewards دون كسر early promotion.
7. حدّث/أضف regression tests.
8. شغّل/تحقق من البوابات المتاحة فعليًا قبل إعلان W1 closed.
9. حدّث Master Gap Register + هذا handoff + comprehensive audit عند إغلاق W1.

**لا تنتقل W2 قبل إغلاق W1 أو توثيق blocker حقيقي.**
