# PROMPT — استلام منصة هِمّة والاستكمال من A10/W1

أنت الآن المسؤول الهندسي التنفيذي الكامل عن منصة **هِمّة** في المستودع:

`7eaur/himma-`

الفرع الحالي للعمل:

`audit/comprehensive-repository-review-2026-09-10`

هذه ليست محادثة تحليل جديدة، ولا أريد إعادة العمل من البداية. أنت تستلم مشروعًا تم تدقيقه وتنفيذ جزء من صيانته بالفعل، ومهمتك أن **تفهم الحالة الحالية من Git والوثائق ثم تواصل التنفيذ من نفس نقطة التوقف دون فقد أي قرار أو الرجوع عن أي إصلاح**.

## أول خطوة إلزامية

1. اجلب HEAD الحالي للفرع `audit/comprehensive-repository-review-2026-09-10` ولا تفترض SHA قديمًا.
2. اقرأ أولًا كامل الملف:

`docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-10_A10_W1_FULL_AR.md`

3. ثم اقرأ حسب الحاجة المباشرة للتنفيذ:

- `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_COMPREHENSIVE_REPOSITORY_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A03_AUDIO_SPEECH_REVIEW_ADAPTATION_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A08_FULL_JOURNEY_INTEGRATION_E2E_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A09_BRANCH_CLASSIFICATION_2026-09-10_AR.md`
- `docs/specs/SOURCE_OF_TRUTH.md`
- `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`
- `docs/maintenance/CANONICAL_CONTENT_EXECUTION_UPDATE_2026-09-10_AR.md`
- `AGENTS.md`
- `.agents/rules/00-himma-core.md`
- `.agents/rules/10-delivery-protocol.md`
- `.agents/rules/20-security-quality.md`

لا تعِد A00–A09؛ هي مغلقة كتدقيق.

## الحالة الحالية التي تستلمها

نحن الآن في:

`A10 / W1 — Academic & History Integrity`

تم بالفعل تنفيذ هذه الإصلاحات في W1:

- توحيد latest AudioSubmission / latest review helpers في `audio_review_state.py`.
- pending review queue أصبحت latest-only.
- منع review لتسجيل تاريخي بعد وجود تسجيل أحدث.
- invalid review لا يعيد فتح Attempt تلقائيًا؛ يصبح `rerecord_required` فقط.
- assessment completion صار يعتمد latest submission/latest AudioReview.
- assessment rerecord صار append-only بدل overwrite.
- الطالب يجب أن يفتح rerecord task صراحة قبل إعادة التسجيل.
- التسجيل القديم يبقى immutable history والتسجيل الجديد يصبح active لأنه الأحدث.
- أُنشئ `services/api/level_completion.py` كمالك canonical لاكتمال المستوى:
  - 10/10 Core = complete.
  - L1/L2 يمكن أن يكتمل عبر automatic early promotion الصحيح عند 6–9 Core.
  - L3 يحتاج 10/10.
  - manual override لا يصنع completion evidence.

آخر code-bearing checkpoint قبل commits التوثيق كان:

`ead44bf492cdbea35b65dc9ddce54fe7de4a20ef`

لكن لا تعتمد عليه كـHEAD؛ اجلب HEAD الحالي أولًا.

## نقطة الاستكمال الدقيقة

ابدأ الآن مباشرة من W1 ولا تنتقل W2 قبل إغلاقه:

1. اربط `level_completion.py` مع `journey.py` وRewards في `adaptation.py` وأي consumer يعتمد completion/posttest/admin state. لا تترك Journey وBadge بمنطقين مختلفين.
2. أصلح `AUD-A03-009`: الصوت graded يجب أن يدخل adaptation كقيمة رقمية من `AudioReview.rubric_score`، لا أن يتحول إلى Boolean يجعل 0.10 و1.00 متساويين.
3. أصلح `AUD-BE-003`: pending audio summary يجب أن يبقى صحيحًا حتى لو يوجد sibling actionable step، مع استمرار same-level navigation.
4. راجع `protected.py`/profile وأي assessment status consumer واجعله latest-submission only.
5. حدّث واجهة الاختبار لتعرض deferred rerecord task وتفتحها صراحة ثم تعيد التسجيل؛ لا ترجع للـold blocking overlay.
6. أضف regression tests لكل boundary السابقة، خصوصًا:
   - invalid → task → explicit open → new submission → old retained.
   - historical submission لا يعود actionable.
   - numeric rubric 0/0.1/0.7/1.0.
   - early promotion completion/reward عند 6–9 Core.
   - manual override لا يصنع completion.
   - L3 يحتاج 10/10.
   - pending learning audio count مع sibling actionable.
7. شغّل targeted tests ثم البوابات المناسبة. لا تقل PASS إلا بنتيجة فعلية على SHA محدد.
8. وثّق ما تنفذه في handoff/audit checkpoint، ثم أكمل. لا تتوقف لمجرد التوثيق.

## القرارات الأكاديمية التي لا يجوز الرجوع عنها

- canonical content الحالي = **125 عنصرًا**.
- 30 pretest + 30 posttest.
- 3 مستويات، لكل مستوى 10 Core + 5 Reinforcement.
- placement: `<50=L1`, `50..<80=L2`, `>=80=L3`.
- activity: `>=80 pass`, `70..<80 guided retry`, `<70 reinforcement`.
- L1/L2 early promotion = >=6 Core + mastery >=85 + critical coverage + floor >=70 + no unresolved blockers عند boundary.
- لا automatic demotion.
- L3 لا يكتمل إلا بـ10 Core.
- newest three valid evidences weighted 50/30/20.

## عقد الصوت غير القابل للكسر

- uploaded/pending = neutral أكاديميًا.
- pending لا يمنع same-level learning/support.
- unresolved audio يمنع فقط irreversible promotion/L3 completion في learning.
- assessment يجوز له انتظار human review قبل الانتقال حسب العقد الحالي.
- rerecord_required deferred until explicit learner open.
- rerecord append-only.
- latest AudioSubmission = active state.
- لا حذف history.
- graded فقط يدخل evidence.
- Human supervisor review هي السلطة الأكاديمية الحالية.
- لا Production ASR provider معتمد.
- لا mock provider ولا machine confidence كحقيقة أكاديمية.

## قواعد التنفيذ

- لا Docker.
- لا Merge الآن.
- لا Deploy الآن.
- لا Railway الآن.
- لا Temporary Audio Skip.
- لا حذف AudioSubmissions أو Reward/Assessment history.
- لا تغيير canonical content المعتمد بدون سبب أكاديمي موثق.
- لا تضف repair/overlay layer جديدة؛ أصلح owner/root cause.
- افحص الكود الحقيقي ولا تحكم من أسماء الملفات.
- لا تدمج Speech/Pronunciation Lab branches؛ هي research only حتى اعتماد مستقل.
- لا تدمج `deployment/platform-sandbox`؛ هو مرجع قديم فقط.
- Git الحالي هو الحقيقة التنفيذية إذا سبق تقريرًا قديمًا، لكن لا تلغِ القرارات الأكاديمية الموثقة بصمت.
- لا تدّع نتائج اختبار لم تُشغّل.

## طريقة تعاملك معي

تصرّف كـPrincipal Engineer/Architect مسؤول عن المنتج كاملًا، وليس كمنفذ patches متفرقة.

لا تكتفِ بتقارير أو وعود. استخدم صلاحيات GitHub المتاحة، افحص الملفات، عدّل فعليًا، اختبر، وثّق، ثم واصل.

لا تتوقف بدون سبب حقيقي. إذا واجهت dependency خارجيًا أو قرارًا أكاديميًا يحتاج اعتمادي، قل بوضوح ما الذي يمنعك وما الذي أنجزته قبله. غير ذلك استمر حتى إغلاق W1 ثم انتقل حسب Master Gap Register.

ابدأ الآن من HEAD الحالي ومن **ربط Level Completion owner → Journey/Rewards**، ثم تابع بقية W1.