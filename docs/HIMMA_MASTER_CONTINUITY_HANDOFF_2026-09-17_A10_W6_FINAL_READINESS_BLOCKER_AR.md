# HIMMA MASTER CONTINUITY HANDOFF — 2026-09-17 — A10 / W6 FINAL READINESS BLOCKER

## 1. Purpose

هذا الملف هو نقطة التسليم الحالية للمحادثة التالية. لا يعتمد على ذاكرة المحادثات؛ اعتمد على المستودع الحي ثم استخدم هذا الملف لتحديد موضع الاستئناف بدقة.

**Repository:** `7eaur/himma-`  
**Execution branch:** `audit/comprehensive-repository-review-2026-09-10`  
**Default branch:** `stage/02-content`  
**Execution phase:** `A10`  
**Current wave:** `W6 / Final Exact-SHA Acceptance`  
**Current state:** `W1–W5 GREEN; W6 Quality Gate GREEN but M09 Release Readiness RED; do not start A11.`

## 2. Live truth rule

عند بدء المحادثة التالية:

1. Fetch live execution branch HEAD أولًا.
2. لا تفترض أن SHA أدناه هو HEAD لأن هذا handoff وملفات الحالة تُكتب كـdocs-only descendants بعد آخر functional candidate.
3. إذا كانت commits بعد functional candidate توثيقًا فقط، احتفظ بـfunctional SHA كدليل الاختبار، لكن استأنف من live HEAD.
4. إذا ظهر كود/Workflow أحدث، افهم الفرق قبل أي تعديل.

Source of Truth order:

`live code → PostgreSQL migrations/schema → executable tests/CI → canonical contracts/approved decisions → STATUS/progress → historical audit docs`

## 3. Read order for the next conversation

اقرأ بالترتيب:

1. `NEXT_CONVERSATION_PROMPT.md`
2. `docs/ops/STATUS.md`
3. `docs/ops/progress.json`
4. هذا الملف
5. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_STATUS_UPDATE_2026-09-16_AR.md`
6. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
7. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_EXECUTION_ADDENDUM_2026-09-12_AR.md`
8. `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR`
9. `START_HERE_AR.md`
10. `AGENTS.md` ثم `.agents/rules/00-himma-core.md`, `.agents/rules/10-delivery-protocol.md`, `.agents/rules/20-security-quality.md`.

لا تعِد A00–A09. ملفاتها للتاريخ/root cause فقط.

## 4. Closed execution history — do not reopen without new evidence

- W1 GREEN — `ea132c9afbe152d0afa5ae581c058ce3248a0c48`, Quality Gate #813 / Run `34467329988`.
- W2 GREEN — `77ac72174a9e21163f6341ea8e0fcc172269eac3`, Quality Gate #822 / Run `34548388760`.
- W3 GREEN — `62e34b151e46b406cf3936201f80010abbe9d8d1`, Quality Gate #848 / Run `34729450663`.
- W4 GREEN — exact code SHA `c26fc9f9f2995d3fa5acea1d01b2e68041577534`, Quality Gate #858 / Run `35043108503`.
- W5 GREEN — exact code SHA `728025a8fd5ff1fa182db4085ad18dd45142041a`, Quality Gate #869 / Run `35053591742`; backend `890 passed, 5 warnings`.

W4 owner/client decisions are already resolved in `docs/ops/HIMMA_W4_OWNER_CLIENT_APPROVAL_2026-09-14.md`; do not ask for the same approval again.

## 5. W6 work already implemented

Do not rebuild these from scratch unless a new failing exact-SHA run gives evidence:

### Security headers

`apps/web/next.config.ts` has global app header policy including CSP baseline, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, and permissions policy. Unit/live local header acceptance exists. Production/deployed verification is not claimed and belongs to A11 only.

### Reward lifecycle

W6 has deterministic reward coverage for award → canonical badge identity/asset → Student → Admin → refresh → idempotency. This is the executable W6 acceptance for `AUD-BADGE-006` / `AUD-A08-008`.

### Same-student journey

W6 has a deterministic single-student journey with live pretest, canonical middle-learning evidence, supervisor posttest authorization, live posttest, and final report evidence. The bounded middle-learning test helper persists canonical completion evidence; it is not a fake pre/post browser flow.

### Responsive acceptance

Critical Student surfaces and Admin Student Detail are covered at deterministic widths including 320/360/390/430/768/Desktop. Earlier 320px overflow was fixed.

### Accessibility acceptance

W6 includes Axe blocking scans plus keyboard, RTL, touch, reduced motion, zoom-equivalent width, contrast and progress semantics. Earlier student-login contrast failure caused by an opacity entrance animation was repaired by using a transform-only higher-specificity module animation.

Manual human screen-reader verification has **not** been performed and must not be fabricated.

### Test ownership

`apps/web/tests/TEST_OWNERSHIP.md` explicitly defines the release-evidence suite. `browser-flow.spec.ts` is legacy/debug evidence only and is superseded for release acceptance by deterministic specs.

### CI composition

`.github/workflows/ci.yml` accepts the audit branch and runs the declared W6 release E2E set with native PostgreSQL/Redis and pinned MinIO; no Docker.

`.github/workflows/m09-release-readiness.yml` was expanded to include backend product regression, canonical release/migration/readiness, declared Playwright release suite, PostgreSQL backup/restore, and object-storage backup/restore. Its current schema-bootstrap order is the remaining blocker.

## 6. Exact W6 functional candidate and current CI truth

Last verified functional candidate before this handoff documentation:

`565ba4092c4312c55e7e57a8c45e32f8997afd8d`

Commit message:

`ci(w6): run M09 readiness on audit exact head`

### Quality Gate

Quality Gate #885 / Run ID `35136617396` on exact SHA `565ba409...` = **SUCCESS**.

This is the first current W6 exact-head evidence in this handoff proving the complete Quality Gate green after the earlier W6 fixes. Security + Frontend + Backend + Integration/Playwright passed on the same SHA.

### Responsive gate

M04 Responsive #347 / Run ID `35136619472` on the same SHA = **SUCCESS**.

### Release Readiness

M09 Release Readiness #207 / Run ID `35136619488` on the same SHA = **FAILURE**.

Readiness job ID:

`104930486030`

Failed step:

`Run backend product regression`

Later steps were skipped because this step failed.

## 7. Exact current blocker

The M09 backend regression command collected 896 tests and ended with:

`3 failed, 891 passed, 2 skipped, 5 warnings`

The only failures:

1. `tests/test_account_lockouts.py::test_admin_lockout_threshold_expiry_and_recovery`
2. `tests/test_account_lockouts.py::test_student_lockout_clears_after_successful_authentication`
3. `tests/test_account_lockouts.py::test_admin_and_student_lockout_namespaces_are_isolated`

All reach:

`services/api/services/account_lockouts.py:40`

and fail on `db.flush()` with PostgreSQL:

`UndefinedTable: relation "account_lockout_states" does not exist`

This is not a random browser failure and not a reason to weaken lockout behavior.

## 8. Root-cause evidence and hypothesis to verify

The current `.github/workflows/m09-release-readiness.yml` order is materially:

1. checkout;
2. start native PostgreSQL and Redis;
3. Python/dependency setup;
4. **run full backend product regression**;
5. reset database;
6. canonical release validation;
7. Alembic migration/readiness/idempotency sequence;
8. MinIO and service readiness;
9. frontend build/start;
10. declared Playwright release suite;
11. PostgreSQL backup/restore;
12. private object-storage backup/restore.

Therefore the backend pytest regression currently starts before the workflow has migrated/bootstraped the database schema required by the current account-lockout model/tests.

The next engineer must still verify:

- which model/migration owns `account_lockout_states`;
- whether Quality Gate backend already initializes this correctly and can be mirrored without overengineering;
- whether any test fixture contract intentionally owns schema setup.

The likely repair is to establish the migrated current schema before M09 backend regression while preserving the later clean reset and independent canonical/migration/idempotency/readiness checks. Do **not** hand-create the table inside tests as a patch and do not move/delete the regression merely to turn the workflow green.

## 9. First files to inspect at resume point

- `.github/workflows/m09-release-readiness.yml`
- `.github/workflows/ci.yml`
- `services/api/tests/test_account_lockouts.py`
- `services/api/services/account_lockouts.py`
- account-lockout model and owning Alembic migration/version
- any shared backend test fixture/schema bootstrap used by the passing Quality Gate
- `apps/web/tests/TEST_OWNERSHIP.md`

Compare Quality Gate backend initialization against M09 rather than inventing a third setup path.

## 10. Exact next execution sequence

1. Fetch current live HEAD and compare it to functional candidate `565ba409...`.
2. If descendants are docs-only, continue from HEAD but treat `565ba409...` as last tested functional evidence.
3. Verify migration/model ownership of `account_lockout_states` and the M09/Quality-Gate setup difference.
4. Apply the smallest root-cause workflow/schema-bootstrap correction that keeps the full backend regression intact.
5. Preserve the clean reset and all later M09 canonical release/migration/idempotency/runtime/backup checks.
6. Commit to the execution branch.
7. The change produces a new candidate SHA. Require both workflows on that **same exact SHA**:
   - complete Quality Gate;
   - complete M09 Release Readiness.
8. If either fails, inspect exact job logs and repair root cause. Do not call retry a fix for deterministic failures.
9. W6 becomes GREEN only if Quality Gate is fully green and M09 reaches the end with backend regression, canonical/migration/readiness, release Playwright, PostgreSQL backup/restore and object-storage backup/restore all successful on the same candidate.
10. Then create W6 GREEN closure doc, update `STATUS.md`, `progress.json`, gap overlay and `NEXT_CONVERSATION_PROMPT.md`, recording exact code SHA separately from any docs-only descendant.
11. **STOP at W6 GREEN.**

## 11. Gap interpretation at handoff

The current executable W6 candidate has evidence for `AUD-CI-001`, `AUD-A08-001`, `AUD-A08-002`, `AUD-A08-004`, `AUD-A08-005`, `AUD-A08-006`, `AUD-A08-007`, `AUD-A08-008`, `AUD-A08-009`, `AUD-BADGE-006`, automated/executable `AUD-A11Y-005`, and source/local `AUD-SEC-006` through Quality Gate #885/M04 #347.

However do not globally close W6 yet because `AUD-A08-003` final Release Readiness remains red at M09 #207 and its downstream release/backup checks did not run.

`AUD-SEC-006` deployed verification remains A11-only. `AUD-A11Y-005` manual human screen-reader acceptance is not claimed. `AUD-GIT-001` final merge/release-branch governance is outside the current no-final-merge boundary.

## 12. Fixed constraints

- No Docker.
- No fake ASR.
- No Temporary Audio Skip.
- No history deletion.
- No Speech/Pronunciation Lab merge.
- No final merge.
- No weakened tests, skip or xpass.
- No runtime repair overlays.
- No PASS/CLOSED without exact-SHA evidence.
- Production ASR (`AUD-A03-008`) remains blocked pending approved provider/calibration/privacy/cost/governance.
- No A11 / Deploy / Railway / Production without explicit new authorization.

## 13. Stop condition

The only valid stop for this execution schedule is:

`W6 GREEN with exact-SHA Quality Gate GREEN + full M09 Release Readiness GREEN, documented; then STOP.`

At handoff time this condition is **not yet met** because M09 #207 is red.
