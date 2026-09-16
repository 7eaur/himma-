# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت الآن المسؤول الهندسي والمنتجي الكامل عن منصة **هِمّة** في المستودع:

`7eaur/himma-`

فرع التنفيذ:

`audit/comprehensive-repository-review-2026-09-10`

لا تعتمد على ذاكرة محادثات سابقة. **ابدأ من المستودع الحي مباشرة.**

## أول شيء إلزامي

1. Fetch للـlive execution branch HEAD. لا تفترض أن SHA أدناه ما زال HEAD لأن بعده قد توجد commits توثيق فقط.
2. اقرأ بالترتيب:
   - `docs/ops/STATUS.md`
   - `docs/ops/progress.json`
   - `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-17_A10_W6_FINAL_READINESS_BLOCKER_AR.md`
   - `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_STATUS_UPDATE_2026-09-16_AR.md`
   - `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
   - `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_EXECUTION_ADDENDUM_2026-09-12_AR.md`
   - `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md`
   - `START_HERE_AR`
   - `AGENTS.md` وملفات `.agents/rules/` المشار إليها فيه.
3. تحقق حيًا من Actions على آخر functional/code candidate، ولا تعتبر commits التوثيق exact tested code SHA.
4. لا تعيد A00–A09 ولا W1–W5. نقطة الاستئناف الوحيدة هي **W6 final Release Readiness blocker**.

## Source of Truth

الترتيب التنفيذي للحقيقة:

`live code + PostgreSQL migrations/schema + executable tests/CI + current canonical contracts/approved decisions + current STATUS/progress + historical audit docs`

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

Quality Gate #885 يثبت أن Security + Frontend + Backend + Integration/Playwright أصبحت كلها خضراء على SHA واحد بعد إصلاحات W6 السابقة.

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

الأمر يجمع full backend regression، والنتيجة:

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

الـM09 الحالي يرتب التنفيذ هكذا تقريبًا:

1. Start native PostgreSQL/Redis.
2. Install backend dependencies.
3. **Run full backend product regression.**
4. Reset database.
5. Canonical release validation.
6. Alembic migration/readiness/idempotency.
7. MinIO/runtime/frontend/Playwright/backup-restore.

إذًا الـpytest الحالي يبدأ قبل migration/bootstrap الذي ينشئ schema الحالي. هذه **مرشحة root cause قوية مدعومة بالـworkflow والـfailure**، لكن قبل التعديل تحقق من migration/schema owner الفعلي لـ`account_lockout_states` ومن testing policy.

لا تصلحها عبر skip/xpass، ولا بإنشاء الجدول يدويًا داخل الاختبار، ولا بإضعاف lockout behavior، ولا بإزالة backend regression من M09.

## أول مهمة تنفيذية الآن

1. Fetch live HEAD وتحقق أن التغييرات بعد `565ba409...` توثيق فقط؛ إذا وُجد كود أحدث افهمه أولًا.
2. اقرأ تحديدًا:
   - `.github/workflows/m09-release-readiness.yml`
   - `services/api/tests/test_account_lockouts.py`
   - `services/api/services/account_lockouts.py`
   - model/migration التي تملك `account_lockout_states`
   - Quality Gate backend schema/bootstrap steps في `.github/workflows/ci.yml`
3. حدّد لماذا Quality Gate backend يمر بينما M09 backend regression يبدأ بدون الجدول.
4. أصلح **workflow/schema bootstrap root cause** بحيث product regression يعمل على schema migrated صحيح، مع بقاء clean reset اللاحق واختبارات canonical release/migrations/idempotency كما هي.
5. لا تستخدم Docker؛ PostgreSQL/Redis native وMinIO pinned كما هو موثق.
6. Commit الإصلاح على execution branch.
7. لأن SHA تغيّر، شغّل/تحقق من **Quality Gate كامل + M09 Release Readiness على نفس exact new SHA**.
8. لا تعتبر W6 Green إذا نجح Quality Gate وحده. يجب أن يصل M09 إلى نهايته ويجتاز أيضًا:
   - backend product regression
   - canonical release/migration/readiness checks
   - declared release Playwright suite
   - PostgreSQL backup/restore
   - object-storage backup/restore
9. إذا فشل أي جزء، أصلح root cause وكرر على SHA جديد، بدون retries تُستخدم لإخفاء deterministic failure.
10. فقط عندما يكون Quality Gate وM09 كاملين GREEN على نفس exact SHA: حدّث W6 closure docs/STATUS/progress/gap overlay، سجّل exact passing SHA/run IDs، ثم **STOP**.

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

Production ASR (`AUD-A03-008`) يبقى blocked حتى external provider/calibration/privacy/cost/governance approval.

`AUD-SEC-006`: source/local header contract منفذ؛ deployed-header verification يبقى A11 فقط.

`AUD-A11Y-005`: automated executable acceptance منفذ؛ لا تدّعِ manual human screen-reader verification لأنها لم تُنفذ.

`AUD-GIT-001`: لا تعمل final merge تحت هذه الخطة؛ final branch/release governance يبقى ضمن الحد اللاحق/قرار المالك.

## قاعدة الاستمرار

لا تكتفِ بتقرير. بعد قراءة المصادر والتحقق الحي، نفّذ إصلاح M09 من الجذر وتابع الـexact-head gates حتى W6 GREEN أو حتى يظهر blocker خارجي حقيقي. عند W6 GREEN توقف ولا تنتقل إلى A11.
