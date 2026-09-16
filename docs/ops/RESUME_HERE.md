# RESUME HERE — A10 / W6 Final Release Readiness

**Last updated:** 2026-09-17  
**Repository:** `7eaur/himma-`  
**Execution branch:** `audit/comprehensive-repository-review-2026-09-10`  
**Default branch:** `stage/02-content`  
**Current phase:** `A10`  
**Current wave:** `W6 / Final Exact-SHA Acceptance`  
**Current status:** `W1–W5 GREEN; W6 Quality Gate GREEN, M09 Release Readiness RED; NO A11 / NO MERGE / NO DEPLOY`

## Live truth rule

ابدأ دائمًا بـFetch للـlive execution branch HEAD.

لا تفترض أن آخر SHA توثيق هو exact tested code SHA. إذا كانت commits اللاحقة توثيقًا فقط، استخدمها كنقطة قراءة/استئناف، لكن احتفظ بآخر functional SHA كدليل الاختبار.

Source of Truth:

`live code → PostgreSQL schema/Alembic → executable tests + exact-SHA CI → canonical contracts/approved decisions → STATUS/progress/current handoff → history`

## Read first

1. `NEXT_CONVERSATION_PROMPT.md`
2. `START_HERE_AR.md`
3. `docs/ops/STATUS.md`
4. `docs/ops/progress.json`
5. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-17_A10_W6_FINAL_READINESS_BLOCKER_AR.md`
6. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_STATUS_UPDATE_2026-09-16_AR.md`
7. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
8. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_EXECUTION_ADDENDUM_2026-09-12_AR.md`
9. `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md`
10. `docs/specs/SOURCE_OF_TRUTH.md`
11. `AGENTS.md` ثم `.agents/rules/`.

## Closed work — do not reopen without new evidence

- A00–A09: CLOSED AUDIT.
- W1 GREEN — `ea132c9afbe152d0afa5ae581c058ce3248a0c48`, Quality Gate #813 / Run `34467329988`.
- W2 GREEN — `77ac72174a9e21163f6341ea8e0fcc172269eac3`, Quality Gate #822 / Run `34548388760`.
- W3 GREEN — `62e34b151e46b406cf3936201f80010abbe9d8d1`, Quality Gate #848 / Run `34729450663`.
- W4 GREEN — exact code SHA `c26fc9f9f2995d3fa5acea1d01b2e68041577534`, Quality Gate #858 / Run `35043108503`.
- W5 GREEN — exact code SHA `728025a8fd5ff1fa182db4085ad18dd45142041a`, Quality Gate #869 / Run `35053591742`; backend `890 passed, 5 warnings`.

Do not redo W4 badge/media decisions or W5 backend/performance/media cleanup unless a new exact-SHA failure proves regression.

## Current W6 functional evidence

Last verified functional candidate before the current documentation descendants:

`565ba4092c4312c55e7e57a8c45e32f8997afd8d`

Commit:

`ci(w6): run M09 readiness on audit exact head`

On this exact SHA:

- Quality Gate #885 / Run `35136617396` — **SUCCESS**.
- M04 Responsive #347 / Run `35136619472` — **SUCCESS**.
- M09 Release Readiness #207 / Run `35136619488` — **FAILURE**.

Quality Gate #885 is the current proof that Security + Frontend + Backend + Integration/Playwright passed together on one exact SHA.

## W6 implementation already proven

Do not rebuild these from scratch:

- Global security-header source contract + local live-response verification.
- Reward lifecycle E2E: award → canonical asset → Student/Admin → refresh → idempotency.
- Deterministic same-student journey: live pretest → canonical learning evidence → supervisor posttest authorization → live posttest → report evidence.
- Responsive acceptance at 320/360/390/430/768/Desktop, including Admin Student Detail.
- Automated Axe + keyboard + RTL + touch + reduced-motion + zoom/contrast/progress semantics.
- `apps/web/tests/TEST_OWNERSHIP.md` owns release evidence; `browser-flow.spec.ts` is legacy/debug only.
- Backend no longer blocks Integration in Quality Gate.

Manual human screen-reader verification is **not** claimed. Deployed security-header verification is **not** claimed.

## Exact blocker now

The only current blocker in W6 is final M09 Release Readiness composition (`AUD-A08-003`).

M09 #207 job `104930486030` failed at:

`Run backend product regression`

Result:

`3 failed, 891 passed, 2 skipped, 5 warnings`

Failing tests:

1. `tests/test_account_lockouts.py::test_admin_lockout_threshold_expiry_and_recovery`
2. `tests/test_account_lockouts.py::test_student_lockout_clears_after_successful_authentication`
3. `tests/test_account_lockouts.py::test_admin_and_student_lockout_namespaces_are_isolated`

All fail at `services/api/services/account_lockouts.py:40` during `db.flush()` with:

`PostgreSQL UndefinedTable: relation "account_lockout_states" does not exist`

## Root-cause hypothesis to verify, not merely assume

Current M09 order materially is:

1. start native PostgreSQL/Redis;
2. install backend dependencies;
3. run full backend product regression;
4. reset database;
5. canonical release validation;
6. Alembic migration/readiness/idempotency;
7. pinned MinIO/runtime/frontend;
8. declared Playwright release suite;
9. PostgreSQL backup/restore;
10. private object-storage backup/restore.

Therefore pytest starts before M09 establishes the migrated schema required by the current account-lockout tests.

The next executor must verify the actual model/migration owner for `account_lockout_states` and compare the successful Quality Gate backend bootstrap with M09. The likely correct repair is to establish the current migrated schema before backend regression while preserving the later clean reset and independent canonical migration/readiness checks.

Do not:

- skip/xpass the tests;
- hand-create `account_lockout_states` inside tests;
- weaken account-lockout behavior;
- delete backend regression from M09;
- use retries to hide deterministic failure.

## First files to inspect

- `.github/workflows/m09-release-readiness.yml`
- `.github/workflows/ci.yml`
- `services/api/tests/test_account_lockouts.py`
- `services/api/services/account_lockouts.py`
- account-lockout model and Alembic migration/version
- shared backend test/schema bootstrap used by Quality Gate
- `apps/web/tests/TEST_OWNERSHIP.md`

## Exact next action

1. Fetch current live HEAD.
2. Inspect descendants after `565ba409...`; if docs-only, do not treat them as tested code.
3. Verify account-lockout schema/migration ownership and the setup difference between Quality Gate and M09.
4. Fix the workflow/schema-bootstrap root cause with the smallest correct change.
5. Preserve the later clean DB reset, canonical validation, migration/idempotency checks, MinIO/runtime, declared Playwright suite and both backup/restore checks.
6. Commit on the execution branch.
7. New code/workflow SHA must pass **full Quality Gate + full M09 Release Readiness on the same exact SHA**.
8. If any part fails, inspect exact logs and fix root cause; do not weaken acceptance.
9. Only after both gates are green on one exact SHA: write W6 GREEN closure, update STATUS/progress/gap overlay/NEXT_CONVERSATION_PROMPT/RESUME_HERE, record exact tested SHA separately from docs-only descendants.
10. **STOP at W6 GREEN.**

## Product rules that must remain intact

Academic flow:

`login → Pretest → placement → level activities → adaptation/reinforcement → canonical completion/promotion → Posttest`

Current rules:

- Placement `<50=L1`, `50..<80=L2`, `80..100=L3`.
- Activity `>=80 success`, `70..<80 guided retry`, `<70 reinforcement`.
- L1/L2 early promotion after >=6 Core only when canonical mastery/critical evidence is satisfied.
- L3 requires 10 Core.
- No automatic demotion.
- Manual override is not completion/badge evidence.
- Latest three valid active-session Core evidences use 50/30/20 weighting.

Content/runtime:

- Approval version: `HIMMA-CONTENT-APPROVAL-2026-09-08`.
- Canonical runtime total: 125 items = 30 Pretest + 30 Posttest + 30 Core + 35 Reinforcement.
- Skills: 44.
- Publication path: approved/versioned contracts → canonical compile/release → deterministic publication → PostgreSQL runtime → structured APIs → deterministic UI.

Audio:

- no Student Audio Skip;
- submissions append-only, latest is active;
- human Supervisor Review is current academic authority;
- automated ASR is advisory;
- Production ASR `AUD-A03-008` remains blocked pending external provider/calibration/privacy/cost/governance approval.

## Fixed constraints

- No Docker.
- No fake ASR.
- No Temporary Audio Skip.
- No history deletion.
- No Speech/Pronunciation Lab merge.
- No final merge.
- No weakened tests / skip / xpass.
- No runtime repair overlays.
- No PASS/CLOSED without exact-SHA evidence.
- No A11 / Deploy / Railway / Production without explicit new authorization.

## Stop condition

The only valid stop for the current schedule is:

`W6 GREEN with exact-SHA Quality Gate GREEN + full exact-SHA M09 Release Readiness GREEN, documented; then STOP.`