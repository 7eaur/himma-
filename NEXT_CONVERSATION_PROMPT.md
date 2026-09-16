# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت الآن المسؤول الهندسي والمنتجي الكامل عن منصة **هِمّة** في المستودع:

`7eaur/himma-`

فرع التنفيذ:

`audit/comprehensive-repository-review-2026-09-10`

لا تعتمد على ذاكرة محادثات سابقة. **ابدأ من المستودع الحي مباشرة.**

## أول شيء إلزامي

1. Fetch للـlive execution branch HEAD. لا تفترض أن أي SHA مذكور هنا ما زال HEAD؛ آخر functional SHA قد تتبعه commits توثيق فقط.
2. اقرأ بالترتيب:
   - `START_HERE_AR.md`
   - `docs/ops/RESUME_HERE.md`
   - `docs/ops/STATUS.md`
   - `docs/ops/progress.json`
   - `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-17_A10_W6_FINAL_READINESS_BLOCKER_AR.md`
   - `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_STATUS_UPDATE_2026-09-16_AR.md`
   - `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
   - `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_EXECUTION_ADDENDUM_2026-09-12_AR.md`
   - `docs/specs/SOURCE_OF_TRUTH.md`
   - `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md`
   - `AGENTS.md` ثم `.agents/rules/00-himma-core.md`, `.agents/rules/10-delivery-protocol.md`, `.agents/rules/20-security-quality.md`.
3. تحقق حيًا من Actions على آخر functional/code candidate، ولا تعتبر docs-only commits exact tested code SHA.
4. لا تعِد A00–A09 ولا W1–W5. نقطة الاستئناف الوحيدة هي **W6 final Release Readiness blocker**.

## Source of Truth

الترتيب التنفيذي للحقيقة:

`live code + PostgreSQL migrations/schema + executable tests/CI + current canonical contracts/approved decisions + current STATUS/progress/handoff + historical audit docs`

المحادثات السابقة ليست Source of Truth.

## الحالة المثبتة التي لا تعيد تنفيذها

- A00–A09: CLOSED AUDIT.
- W1 GREEN — `ea132c9afbe152d0afa5ae581c058ce3248a0c48`, Quality Gate #813 / Run `34467329988`.
- W2 GREEN — `77ac72174a9e21163f6341ea8e0fcc172269eac3`, Quality Gate #822 / Run `34548388760`.
- W3 GREEN — `62e34b151e46b406cf3936201f80010abbe9d8d1`, Quality Gate #848 / Run `34729450663`.
- W4 GREEN — exact code SHA `c26fc9f9f2995d3fa5acea1d01b2e68041577534`, Quality Gate #858 / Run `35043108503`.
- W5 GREEN — exact code SHA `728025a8fd5ff1fa182db4085ad18dd45142041a`, Quality Gate #869 / Run `35053591742`.
- W6: **IN PROGRESS — final Release Readiness blocker only.**

## آخر functional candidate مثبت

Exact functional/code candidate:

`565ba4092c4312c55e7e57a8c45e32f8997afd8d`

Commit:

`ci(w6): run M09 readiness on audit exact head`

على هذا الـSHA نفسه:

- Quality Gate #885 / Run `35136617396` = **SUCCESS**.
- M04 Responsive #347 / Run `35136619472` = **SUCCESS**.
- M09 Release Readiness #207 / Run `35136619488` = **FAILURE**.

Quality Gate #885 يثبت أن Security + Frontend + Backend + Integration/Playwright كلها خضراء على SHA واحد بعد إصلاحات W6 السابقة.

## ما تم في W6 ولا تعِده

تم تنفيذ وإثبات الآتي في Quality Gate #885:

- security headers source contract + local live-header verification.
- full reward lifecycle E2E: award → canonical asset → Student/Admin → refresh → idempotency.
- deterministic same-student live pretest → canonical learning evidence → supervisor posttest authorization → live posttest.
- responsive matrices على 320/360/390/430/768/Desktop بما فيها Admin Student Detail.
- automated Axe + keyboard + RTL + reduced-motion + zoom/contrast/progress semantics.
- `apps/web/tests/TEST_OWNERSHIP.md` يحدد release evidence؛ `browser-flow.spec.ts` legacy/debug وليس release evidence.
- Backend/Integration الحاليان لا يحملان blocker قديمًا في Quality Gate.

لا ترجع لإصلاحات overflow/sequence/opacity السابقة إلا إذا ظهر evidence جديد على SHA جديد.

## نقطة التوقف الدقيقة الآن — M09 #207

Workflow:

`.github/workflows/m09-release-readiness.yml`

Run:

`#207 / 35136619488`

Job:

`104930486030`

فشل في step:

`Run backend product regression`

النتيجة:

`3 failed, 891 passed, 2 skipped, 5 warnings`

الاختبارات الثلاثة الوحيدة الفاشلة:

1. `tests/test_account_lockouts.py::test_admin_lockout_threshold_expiry_and_recovery`
2. `tests/test_account_lockouts.py::test_student_lockout_clears_after_successful_authentication`
3. `tests/test_account_lockouts.py::test_admin_and_student_lockout_namespaces_are_isolated`

كلها تفشل في:

`services/api/services/account_lockouts.py:40`

عند `db.flush()` بسبب PostgreSQL:

`UndefinedTable: relation "account_lockout_states" does not exist`

## Root-cause evidence الحالي

الـM09 الحالي يرتب التنفيذ ماديًا هكذا:

1. Start native PostgreSQL/Redis.
2. Install backend dependencies.
3. **Run full backend product regression.**
4. Reset database.
5. Canonical release validation.
6. Alembic migration/readiness/idempotency.
7. MinIO/runtime/frontend.
8. Declared release Playwright suite.
9. PostgreSQL backup/restore.
10. Private object-storage backup/restore.

إذًا pytest يبدأ قبل migration/bootstrap الذي ينشئ schema الحالي المطلوب لاختبارات account lockout.

هذه root-cause hypothesis قوية ومدعومة بالـworkflow والـfailure، لكن قبل التعديل تحقق من model/migration owner الفعلي لـ`account_lockout_states` ومن setup الناجح داخل Quality Gate.

لا تصلحها عبر skip/xpass، ولا بإنشاء الجدول يدويًا داخل الاختبار، ولا بإضعاف lockout behavior، ولا بإزالة backend regression من M09.

## أول مهمة تنفيذية الآن

1. Fetch live HEAD وتحقق إن كانت التغييرات بعد `565ba409...` توثيقًا فقط؛ إذا وُجد كود/workflow أحدث افهمه أولًا.
2. اقرأ تحديدًا:
   - `.github/workflows/m09-release-readiness.yml`
   - `.github/workflows/ci.yml`
   - `services/api/tests/test_account_lockouts.py`
   - `services/api/services/account_lockouts.py`
   - model/migration التي تملك `account_lockout_states`
   - shared backend schema/test bootstrap المستخدم في Quality Gate
   - `apps/web/tests/TEST_OWNERSHIP.md`
3. حدّد لماذا Quality Gate backend يمر بينما M09 backend regression يبدأ بدون الجدول.
4. أصلح **workflow/schema bootstrap root cause** بحيث product regression يعمل على current migrated schema صحيح، مع بقاء clean reset اللاحق واختبارات canonical release/migrations/idempotency كما هي.
5. لا تستخدم Docker؛ PostgreSQL/Redis native وMinIO pinned كما هو موثق.
6. Commit الإصلاح على execution branch.
7. لأن SHA تغيّر، تحقق من **Quality Gate كامل + M09 Release Readiness كامل على نفس exact new SHA**.
8. لا تعتبر W6 Green إذا نجح Quality Gate وحده. يجب أن يصل M09 إلى النهاية ويجتاز أيضًا:
   - backend product regression
   - canonical release/migration/readiness/idempotency
   - runtime readiness
   - declared release Playwright suite
   - PostgreSQL backup/restore
   - object-storage backup/restore
9. إذا فشل أي جزء، أصلح root cause وكرر على SHA جديد، بدون retries تُستخدم لإخفاء deterministic failure.
10. فقط عندما يكون Quality Gate وM09 كاملين GREEN على نفس exact SHA: حدّث W6 closure docs + `STATUS.md` + `progress.json` + gap overlay + continuity docs، سجّل exact passing SHA/run IDs منفصلة عن docs-only HEAD، ثم **STOP**.

## عقود المنتج التي يجب الحفاظ عليها

- Placement: `<50=L1`, `50..<80=L2`, `80..100=L3`.
- Activity: `>=80 success`, `70..<80 guided retry`, `<70 reinforcement`.
- L1/L2 early promotion بعد >=6 Core فقط عند تحقق canonical mastery/critical evidence.
- L3 requires 10 Core.
- No automatic demotion.
- Manual override لا يعني completion أو badge.
- latest three valid active-session Core evidences تستخدم weights 50/30/20.
- Canonical approval version: `HIMMA-CONTENT-APPROVAL-2026-09-08`.
- Runtime content: 125 items = 30 Pretest + 30 Posttest + 30 Core + 35 Reinforcement; 44 skills.
- Human Supervisor Review هي السلطة الأكاديمية الحالية للصوت.
- Production ASR (`AUD-A03-008`) غير معتمد بعد.

## حدود لا يجوز تجاوزها

- لا A11.
- لا Deploy / Railway / Production.
- لا final merge.
- لا Docker.
- لا fake ASR.
- لا Temporary Audio Skip.
- لا history deletion.
- لا Speech/Pronunciation Lab merge.
- لا weakened tests / skip / xpass.
- لا runtime repair overlays.
- لا PASS/CLOSED بلا exact-SHA evidence.

`AUD-SEC-006`: source/local header contract منفذ؛ deployed-header verification يبقى A11 فقط.

`AUD-A11Y-005`: automated executable acceptance منفذ؛ لا تدّعِ manual human screen-reader verification لأنها لم تُنفذ.

`AUD-GIT-001`: لا تعمل final merge تحت هذه الخطة؛ final branch/release governance يبقى ضمن الحد اللاحق/قرار المالك.

## قاعدة الاستمرار

لا تكتفِ بتقرير. بعد قراءة المصادر والتحقق الحي، نفّذ إصلاح M09 من الجذر وتابع الـexact-head gates حتى **W6 GREEN** أو حتى يظهر blocker خارجي حقيقي. عند W6 GREEN توقف ولا تنتقل إلى A11.