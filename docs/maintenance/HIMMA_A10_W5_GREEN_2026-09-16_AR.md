# هِمّة — A10 / W5 GREEN

**التاريخ:** 2026-09-16  
**الموجة:** W5 — Historical Cleanup / Performance / Test Ownership  
**الحالة:** `CLOSED GREEN`  

## Exact-SHA Evidence

- **Exact code/docs candidate SHA that passed:** `728025a8fd5ff1fa182db4085ad18dd45142041a`
- **Quality Gate:** #869
- **Run ID:** `35053591742`
- Security: SUCCESS
- Frontend: SUCCESS
- Backend: SUCCESS
- Integration / Playwright: SUCCESS

Backend evidence on the same SHA:

- Catalog validation: `105 items / 44 canonical skills / 0 explicit V1 media gaps`
- Canonical release: `125 items`
- Release SHA256: `d23153f45fd8ad5ad6d5eed234d515dc8ec53e0b51c514506619a842277bc1cc`
- Projection SHA256: `a9a2873307e9bebc24680edaaaf5250d98cca1f84c15a93f9538878a371cd3f3`
- Alembic upgrade → downgrade base → upgrade: SUCCESS
- Alembic model drift check: no new upgrade operations
- Canonical seed idempotency: SUCCESS
- Backend pytest: `890 passed, 5 warnings`

## W5 remediation closed

- `AUD-BE-001`: public `/activities` routes now have one canonical router owner; historical modules remain service-only where still required.
- `AUD-BE-002`: current publication/dev sync points to canonical `seed_all`/publisher; historical correction/projection seeds are not executed as the current runtime path.
- `AUD-BE-004`: recovery/current-runtime tests are explicitly separated from historical seed ownership and execute against the current canonical publication world.
- `AUD-A04-004`: legacy `/admin/account` is a compatibility redirect to canonical `/admin/settings`; no parallel account surface remains.
- `AUD-BADGE-009`: RewardEvent history is no longer cascade-deleted with operational Attempt cleanup; FK uses `SET NULL`, with migration and regression coverage.
- `AUD-PERF-002`: `/researcher/students` uses a batched projection with query-budget coverage for cohorts of 1/10/50 and parity checks for early promotion/reopened L3.
- `AUD-PERF-003`: notification GET is read-only; audio-review and reinforcement-escalation notifications materialize/resolve on lifecycle transitions with idempotent tests.
- `AUD-MEDIA-003`: approved unused images remain reserve assets; no deletion/reuse solely because an asset is unused.
- `AUD-MEDIA-004`: duplicate character binaries are not destructively canonicalized without dependency/external-path proof; runtime canonical paths are documented/retained safely.
- `AUD-MEDIA-005`: public files lacking direct textual refs are not deleted without runtime/build/source proof.

`AUD-SEC-004` upload-size/storage-cleanup boundary was already closed in W2 and re-passed here through `test_w2_security_runtime.py`; W5 did not reopen that security control.

## Important evidence rule

Any commits created after SHA `728025a8...` only to update continuity/status documents are documentation-only descendants. They must not be described as the SHA that passed Quality Gate #869.

## Next

W6 is now allowed to start. W6 must close final acceptance gaps, including reward lifecycle E2E, broad accessibility/responsive acceptance, exact-head CI ownership/final gate, and remaining test-ownership/final-journey acceptance. At W6 GREEN stop; do not execute A11/deploy/Railway/Production/final merge without a new explicit authorization.
