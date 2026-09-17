# STATUS — Himma Platform

**Last updated:** 2026-09-17  
**Repository:** `7eaur/himma-`  
**Execution branch:** `audit/comprehensive-repository-review-2026-09-10`  
**Current state:** `A00–A09 CLOSED — W1–W6 GREEN — STOP — NO A11 / NO MERGE / NO DEPLOY`

## W6 closure evidence

Exact tested functional SHA:

`c5174f33b11be80500fdd72c0456efbef062f5ad`

Commit: `fix(auth): count only failed login attempts`.

| Gate | Exact evidence | Conclusion |
|---|---|---|
| Quality Gate | #902 / Run `35198824643` | SUCCESS |
| M09 Release Readiness | #211 / Run `35198824646` / job `105128375595` | SUCCESS |
| QG backend | `893 passed, 5 warnings` | PASS |
| QG Integration Playwright | `20 passed (3.8m)` | PASS |
| M09 declared Playwright suite | `19 passed (4.4m)` | PASS |
| PostgreSQL backup/restore | `PostgreSQL restore verification passed.` | PASS |
| Object storage backup/restore | 43 objects backed up and restored/verified | PASS |
| Backup artifact policy | no data backup artifact uploaded from CI | PASS |

Any later documentation commit is docs-only and does not replace this tested SHA.

## Root cause and fix

M09 #210 failed because three release tests received `429` from `POST /auth/login`; the first was `vertical-slice.spec.ts` in `loginAsSupervisor`. The protected runtime limiter incremented both IP and identifier counters before credential validation, but successful authentication cleared only the identifier counter. Valid logins from the shared CI IP therefore exhausted the 20-attempt IP budget.

The fix separates checking from recording: pre-auth calls only check existing counters, and `record_auth_rate_limit_failure()` increments IP and identifier only after invalid credentials. Successful authentication still clears the identifier failure counter; the shared IP counter still aggregates invalid attempts across rotating identifiers; Redis remains fail-closed.

Changed functional files:

- `services/api/auth_rate_limit.py`
- `services/api/auth.py`
- `services/api/test_w2_security_runtime.py`
- `docs/ops/STATUS.md` in the functional commit for active-slice traceability

No schema/migration, content, academic rule, audio contract, retry, timeout, skip, xfail, assertion weakening, or runtime repair overlay changed.

## Closed work

A00–A09 and W1–W6 are closed. Do not reopen without new regression evidence. Historical M09 #210 and earlier PostgreSQL/trial/MinIO blockers remain documented as history, not current blockers.

## Remaining outside W6

- `AUD-A03-008`: Production ASR external approval.
- `AUD-SEC-006`: deployed-header verification in A11/later.
- `AUD-A11Y-005`: manual human screen-reader verification not claimed.
- `AUD-GIT-001`: final merge not executed.
- A11 / Deploy / Railway / Production require explicit new authorization.

## Hard stop

No Docker. No fake ASR. No Temporary/Student Audio Skip. No history deletion. No Speech/Pronunciation Lab merge. No final merge. No weakened tests. No runtime repair overlays. **STOP after W6 GREEN.**
