# ابدأ من هنا — مستودع هِمّة

هذه نقطة الدخول التنفيذية لأي محادثة أو وكيل جديد يعمل على منصة **هِمّة**.

> لا تعتمد على ذاكرة المحادثات أو SHA قديم. ابدأ دائمًا من المستودع الحي ثم استخدم التوثيق الحالي لتحديد نقطة الاستئناف.

## 1) المستودع والفروع

- Repository: `7eaur/himma-`
- Default branch: `stage/02-content`
- Execution branch: `audit/comprehensive-repository-review-2026-09-10`
- Current execution phase: `A10`
- Current wave: `W6 / Final Exact-SHA Acceptance`
- Current state: `W1–W5 GREEN; W6 Quality Gate GREEN but M09 Release Readiness RED; NO A11 / NO MERGE / NO DEPLOY`

لا تعدّل الفروع الأساسية مباشرة، ولا تستخدم force-push/reset destructive، ولا تعتبر helper branches فروع تسليم نهائية.

## 2) ترتيب القراءة الإلزامي

ابدأ بالترتيب التالي:

1. `NEXT_CONVERSATION_PROMPT.md`
2. `docs/ops/STATUS.md`
3. `docs/ops/progress.json`
4. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-17_A10_W6_FINAL_READINESS_BLOCKER_AR.md`
5. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_STATUS_UPDATE_2026-09-16_AR.md`
6. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
7. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_EXECUTION_ADDENDUM_2026-09-12_AR.md`
8. `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md`
9. `docs/specs/SOURCE_OF_TRUTH.md`
10. `AGENTS.md` ثم `.agents/rules/00-himma-core.md`, `.agents/rules/10-delivery-protocol.md`, `.agents/rules/20-security-quality.md`.

ملفات A00–A09 والـhandoffs القديمة تبقى تاريخًا ومرجع root-cause فقط؛ لا تُستخدم كنقطة استئناف إذا تعارضت مع الحالة الحالية.

## 3) Source of Truth

عند التعارض استخدم هذا الترتيب:

`live code → PostgreSQL schema/Alembic migrations → executable tests + exact-SHA CI → canonical contracts/approved decisions → current STATUS/progress/handoff → historical audit docs`

لا تعلن PASS/CLOSED اعتمادًا على وثيقة فقط.

## 4) الحالة التنفيذية الحالية

- A00–A09: CLOSED AUDIT؛ لا تعاد.
- W1: GREEN.
- W2: GREEN.
- W3: GREEN.
- W4: GREEN.
- W5: GREEN.
- W6: **IN PROGRESS — final Release Readiness blocker only**.

Exact evidence للـwaves المغلقة موجود في `docs/ops/STATUS.md` و`docs/ops/progress.json`.

آخر functional candidate مثبت قبل التوثيق الحالي:

`565ba4092c4312c55e7e57a8c45e32f8997afd8d`

على نفس SHA:

- Quality Gate #885 / Run `35136617396` = **SUCCESS**.
- M04 Responsive #347 / Run `35136619472` = **SUCCESS**.
- M09 Release Readiness #207 / Run `35136619488` = **FAILURE**.

Quality Gate #885 يثبت Security + Frontend + Backend + Integration/Playwright على نفس SHA. لذلك لا تعِد إصلاحات W6 السابقة المتعلقة بالـoverflow أو student-login contrast أو sequence interaction إلا إذا ظهر evidence جديد.

## 5) نقطة التوقف الدقيقة

الـblocker الحالي الوحيد داخل W6 هو `AUD-A08-003` / M09 Release Readiness.

في M09 #207، step:

`Run backend product regression`

انتهى بـ:

`3 failed, 891 passed, 2 skipped, 5 warnings`

الاختبارات الفاشلة الوحيدة:

1. `tests/test_account_lockouts.py::test_admin_lockout_threshold_expiry_and_recovery`
2. `tests/test_account_lockouts.py::test_student_lockout_clears_after_successful_authentication`
3. `tests/test_account_lockouts.py::test_admin_and_student_lockout_namespaces_are_isolated`

كلها تفشل عند `services/api/services/account_lockouts.py:40` أثناء `db.flush()` بسبب PostgreSQL:

`UndefinedTable: relation "account_lockout_states" does not exist`

الـworkflow الحالي يشغّل full backend regression قبل schema migration/bootstrap المطلوب. هذه هي root-cause hypothesis الحالية التي يجب التحقق منها مقابل migration owner والـQuality Gate setup قبل أي تعديل.

## 6) أول ملفات يجب فحصها عند الاستئناف

- `.github/workflows/m09-release-readiness.yml`
- `.github/workflows/ci.yml`
- `services/api/tests/test_account_lockouts.py`
- `services/api/services/account_lockouts.py`
- model + Alembic migration التي تملك `account_lockout_states`
- shared backend test/schema bootstrap المستخدم في Quality Gate
- `apps/web/tests/TEST_OWNERSHIP.md`

الهدف هو مقارنة setup الناجح في Quality Gate مع M09 وإصلاح schema bootstrap/order من الجذر، لا اختراع مسار ثالث.

## 7) ما تم بالفعل في W6 ولا يعاد

W6 الحالي يحتوي ويختبر:

- security headers contract + local live-header verification؛ deployed verification لاحق/A11 فقط.
- full reward lifecycle E2E: award → canonical asset → Student/Admin → refresh → idempotency.
- deterministic same-student pretest → canonical learning evidence → supervisor authorization → live posttest.
- responsive matrices 320/360/390/430/768/Desktop بما فيها Admin Student Detail.
- Axe + keyboard + RTL + reduced-motion + zoom/contrast/progress semantics.
- explicit release-test ownership في `apps/web/tests/TEST_OWNERSHIP.md`؛ `browser-flow.spec.ts` legacy/debug فقط.
- Backend + Integration passed together في Quality Gate #885.

Manual human screen-reader verification لم يُنفذ ولا يجوز الادعاء به.

## 8) المنتج والعقود الأساسية التي يجب الحفاظ عليها

المسار الأكاديمي العام:

`Student login → Pretest → placement → level activities → adaptation/reinforcement → canonical completion/promotion → Posttest`

القواعد الحالية:

- Placement: `<50 → L1`, `50..<80 → L2`, `80..100 → L3`.
- Activity: `>=80 success`, `70..<80 guided retry`, `<70 reinforcement`.
- L1/L2 early promotion بعد >=6 Core عند تحقق mastery/critical evidence الكانونية.
- L3 requires 10 Core.
- No automatic demotion.
- Manual override لا يعني completion أو badge.
- latest three valid active-session Core evidences تستخدم weights 50/30/20.

## 9) المحتوى والصوت والميديا

الإصدار الكانوني للمحتوى:

`HIMMA-CONTENT-APPROVAL-2026-09-08`

الـruntime يثبت 125 item:

- 30 Pretest
- 30 Posttest
- 30 Core
- 35 Reinforcement
- 44 skills

المسار الصحيح:

`approved/versioned contracts → canonical compile/release → deterministic publication → PostgreSQL runtime → structured APIs → deterministic UI`

لا runtime overlays ولا seeders تاريخية كـauthority جديدة.

الصوت:

- لا Student Audio Skip.
- latest AudioSubmission هو active والقديم immutable.
- rerecord append-only.
- human Supervisor Review هي السلطة الأكاديمية الحالية.
- automated ASR advisory فقط.
- Production ASR (`AUD-A03-008`) blocked حتى provider/calibration/privacy/cost/governance approval.

W4 media lexical decisions مغلقة ومعتمدة؛ لا تعِد طلب الموافقة.

## 10) قاعدة الإغلاق لـW6

أي تعديل code/workflow ينتج SHA جديدًا.

لا تُغلق W6 إلا عندما يمر على **نفس exact SHA**:

1. full Quality Gate: Security + Frontend + Backend + Integration/Playwright.
2. full M09 Release Readiness حتى النهاية، بما فيه:
   - backend product regression
   - canonical release/migration/readiness/idempotency
   - runtime readiness
   - declared release Playwright suite
   - PostgreSQL backup/restore
   - object-storage backup/restore

عندها فقط:

- أنشئ W6 GREEN closure.
- حدّث `STATUS.md`, `progress.json`, gap overlay, `NEXT_CONVERSATION_PROMPT.md`, `RESUME_HERE.md`.
- سجّل exact tested code SHA منفصلًا عن أي docs-only descendant.
- **STOP.**

## 11) القيود الثابتة

- No Docker.
- No fake ASR.
- No Temporary Audio Skip.
- No history deletion.
- No Speech/Pronunciation Lab merge.
- No final merge.
- No weakened tests / skip / xpass.
- No runtime repair overlays.
- No PASS/CLOSED without exact-SHA evidence.
- No A11 / Deploy / Railway / Production ضمن هذا الجدول.

## 12) قاعدة الاستئناف

لا تبدأ بتقرير عام ولا تعيد A00–A09 أو W1–W5.

ابدأ من live HEAD، افهم أي descendants بعد آخر functional candidate، ثم نفّذ فقط إصلاح M09 schema/bootstrap blocker. بعد كل تغيير تحقق من exact-head Quality Gate + M09 على نفس SHA. توقف عند W6 GREEN.