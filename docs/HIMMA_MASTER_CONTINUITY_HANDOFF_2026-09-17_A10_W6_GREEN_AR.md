> **HISTORICAL / SUPERSEDED:** هذه الوثيقة محفوظة للتاريخ والدليل فقط. الحالة الحالية بعد 2026-09-18 موجودة في START_HERE_AR.md وSTART_HERE_AR.md. أي عبارة هنا مثل NOT MERGED / NOT DEPLOYED / ACTIVE / STOP أو branch قديم لا تصف الوضع الحالي.

# هِمّة — Master Continuity Handoff — A10 / W6 GREEN

**التاريخ:** 2026-09-17  
**Repository:** `7eaur/himma-`  
**Execution branch:** `audit/comprehensive-repository-review-2026-09-10`  
**الحالة:** `A00–A09 CLOSED; W1–W6 GREEN; STOP`

## 1) Exact tested functional SHA

`c5174f33b11be80500fdd72c0456efbef062f5ad`

Commit:

`fix(auth): count only failed login attempts`

أي descendant توثيق لاحق هو docs-only ولا يستبدل SHA الاختبارات أعلاه.

## 2) Final exact-SHA evidence

### Quality Gate

- Run number: **902**
- Run ID: `35198824643`
- Conclusion: **SUCCESS**
- Security: SUCCESS
- Frontend: SUCCESS
- Backend: SUCCESS — `893 passed, 5 warnings in 407.92s`
- Integration: SUCCESS — Playwright `20 passed (3.8m)`
- Playwright report artifact ID: `10487337192`

### M09 Release Readiness

- Run number: **211**
- Run ID: `35198824646`
- Job ID: `105128375595`
- Conclusion: **SUCCESS**
- Backend product regression: `893 passed, 5 warnings in 349.01s`
- Deterministic declared browser product regression: `19 passed (4.4m)`
- PostgreSQL: backup created, restored into isolated database, `PostgreSQL restore verification passed.`
- Object storage: `Object-store backup created with 43 object(s).`; `Object-store restore verified for 43 object(s).`
- Ephemeral policy: `Backup/restore evidence verified; no data backup artifact will be uploaded from CI.`

## 3) Failure evidence traced from M09 #210

M09 #210 / Run `35167789050` / job `105032657002` reached the deterministic browser suite after all earlier readiness steps.

Three specs failed because `POST /auth/login` returned HTTP `429` instead of `200`:

- `apps/web/tests/e2e/vertical-slice.spec.ts` — first failure in `loginAsSupervisor`;
- `apps/web/tests/e2e/w6-responsive.spec.ts`;
- `apps/web/tests/e2e/w6-same-student-journey.spec.ts`.

Quality Gate had not exposed the defect because its integration runtime defaults to development; M09 exercises protected `trial` controls.

## 4) Root cause

`enforce_auth_rate_limit()` incremented both shared IP and identifier counters before credential validation. Successful authentication cleared only the identifier counter, intentionally leaving the IP counter. Consequently, successful supervisor logins from one CI/shared/NAT address accumulated as if they were failed attempts and the twenty-first valid login was blocked.

The issue was in backend auth limiter semantics, not Playwright timing, fixtures, frontend locators, seeded data, sessions, or workflow orchestration.

## 5) Fix

- Pre-auth enforcement now reads/checks existing counters only.
- New `record_auth_rate_limit_failure()` increments IP and identifier counters only after invalid credentials.
- Successful authentication still clears identifier failures.
- Invalid attempts across rotating identifiers still aggregate against the shared IP budget.
- Redis unavailability remains fail-closed in protected runtime.
- No retries, timeout inflation, skip/xfail/xpass, weaker assertions, hard-coded CI exception, or runtime repair overlay.

Functional files:

- `services/api/auth_rate_limit.py`
- `services/api/auth.py`
- `services/api/test_w2_security_runtime.py`
- `docs/ops/STATUS.md` active-slice trace in the functional commit

## 6) Verification

Local before push:

- targeted security runtime: `15 passed, 5 warnings`
- full backend: `893 passed, 5 warnings`
- compile and `git diff --check`: clean

Exact-SHA CI then passed both complete gates, including the two independent declared Playwright executions and both restore checks.

## 7) Unchanged product/system contracts

No database migration/schema, canonical content, academic threshold, promotion/completion, reward, audio submission/review, ASR governance, frontend acceptance assertion, retry, or timeout changed.

Placement/activity/promotion contracts and canonical runtime of 125 items/44 skills remain intact. No Student Audio Skip exists. Human Supervisor Review remains authority; automated ASR remains advisory.

## 8) Historical blockers

Resolved and retained as history:

- PostgreSQL `account_lockout_states` bootstrap/order;
- backend regression interference from protected trial controls;
- dead MinIO archived URL / HTTP 410;
- M09 #210 auth-limiter/Playwright failure.

Do not reopen without new regression evidence.

## 9) Remaining outside W6

- Production ASR `AUD-A03-008`: external approval blocked.
- `AUD-SEC-006`: deployed-header verification, A11/later.
- `AUD-A11Y-005`: manual human screen-reader acceptance not claimed.
- `AUD-GIT-001`: final merge not executed.
- A11 / Deploy / Railway / Production were not started.

## 10) Stop boundary

W6 is closed by executable exact-SHA evidence. **STOP.** Await a new explicit owner assignment before any later phase or external boundary.
