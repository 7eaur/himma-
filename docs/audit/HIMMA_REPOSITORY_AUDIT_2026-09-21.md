# Himma Comprehensive Repository Audit

Status: IN PROGRESS — evidence gathering only  
Audit branch: `audit/full-repository-review-20260921`  
Baseline repository: `7eaur/himma-`  
Baseline default branch: `stage/02-content`  
Baseline commit: `71d3aaf64d5872f5e73f1df796b3c879492de3d4`  
Started: 2026-09-21 (Asia/Aden)

## Guardrails

- No product code changes.
- No database mutations or migrations.
- No deployment or production configuration changes.
- Findings require code/runtime/CI/history evidence.
- Documentation claims are not accepted without code verification.
- The audit includes all live branches, not only the default branch.

## Review scope

1. Repository topology, branch ancestry, stale/divergent work, pull requests, and CI.
2. Backend architecture, API contracts, authentication, authorization, data integrity, and error handling.
3. PostgreSQL schema/migrations, content model, lifecycle invariants, and operational safety.
4. Reading/writing/audio assessment flows, C/D/I/S classification, phonemic analysis, reinforcement, and progression.
5. Frontend information architecture, student/admin journeys, responsiveness, accessibility, performance, and visual consistency.
6. Test coverage, false-positive gates, fixtures, dead code, unused assets/dependencies, duplicated logic, and patches.
7. Configuration, secrets boundaries, observability, deployment, recovery, and documentation drift.
8. Cleanup, unification, remediation, and final delivery plan.

## Evidence standard

Each confirmed finding will record:

- Finding ID and severity.
- Exact branch/commit.
- File path and relevant symbol/lines.
- Reproduction or static proof.
- User/product/operational impact.
- Root cause.
- Proposed resolution.
- Regression tests and acceptance criteria.
- Relationship to other findings.

## Baseline facts

- The repository default and official branch is `stage/02-content`, not a branch named `stage`.
- Baseline default HEAD is `71d3aaf64d5872f5e73f1df796b3c879492de3d4`.
- The last documented functional/gate SHA is its direct parent, `0bf1390bdbc0a19330c807d82d646424490b5a2b`.
- `71d3aaf` changes documentation only (13 documentation files); it does not change product code.
- There were 52 live branches before this audit branch was created; all 52 were returned as unprotected.
- There are three open pull requests at the baseline time: PR #2, PR #3, and PR #4.
- There are no repository releases or tags.
- The working tree contains 1,242 tracked/non-Git files in the checkout, including 166 under `docs/`, 188 under `services/`, 198 under `apps/`, 512 under `assets/`, and 111 under `reference/`.

## Audit log

### Phase 1 — Repository truth and topology

Status: evidence captured; remediation has not started.

#### Branch classification summary

- 38 pre-existing branches are fully contained by `stage/02-content`.
- 5 ASR/speech-lab branches are intentionally divergent and excluded from current delivery by the accepted product boundary.
- `deployment/platform-sandbox` is an obsolete divergent deployment experiment with 9 unique commits.
- Two additional non-audio branches are divergent and absent from the current branch inventory decision:
  - `redesign/audio-review-compact-20260920`: 5 unique commits.
  - `integration/audio-review-compact-20260920`: 8 unique commits.
- Four functional branches are descendants of the official baseline and are not merged into the default branch:
  - `stage/audio-review-playback-20260921`: 6 commits ahead.
  - `stage/content-review-readonly-20260921`: 4 commits ahead.
  - `ux/admin-content-library-20260921`: 5 commits ahead.
  - `ux/content-review-readonly-20260921`: 3 commits ahead; its PR is closed without merge.
- The audit branch is a docs-only descendant created from the exact baseline and is excluded from product classification.

## Confirmed findings — Phase 1

### HIM-AUD-001 — HIGH — Official default HEAD is not green

**Evidence**

- Branch: `stage/02-content`.
- HEAD: `71d3aaf64d5872f5e73f1df796b3c879492de3d4`.
- Himma CI Quality Gate runs #977 (`35542800223`) and #980 (`35544994161`) both failed.
- In both runs, backend and frontend jobs passed, but the security job failed at `Scan current tree for committed secrets`; integration was then skipped.
- The scanner reported three `generic-api-key` findings in documentation: `START_HERE_AR.md`, `docs/ops/progress.json`, and the current handoff.

**Impact**

- The official branch violates its own `Keep it green` delivery rule.
- The full integration result is unknown for the exact official HEAD because integration was skipped.
- A red official HEAD can be mistaken for a verified release because current documents still display `CLOSED / PRODUCTION_GREEN`.

**Likely root cause**

- Long evidence identifiers/digests in documentation match the generic API-key rule. The available logs support a scanner false positive, but this must be confirmed without exposing or weakening real-secret detection.

**Proposed resolution (not executed)**

- Reproduce Gitleaks locally against the exact tree.
- Confirm each finding is a non-secret evidence identifier.
- Add narrowly scoped, documented allowlist fingerprints or encode evidence in a scanner-safe structured form; do not disable the generic rule globally.
- Require a fresh exact-HEAD QG with integration executed.

**Acceptance**

- Security, backend, frontend, and integration all pass on the same official SHA.
- A seeded real-secret fixture still fails the scanner test.

### HIM-AUD-002 — HIGH — Deployment is not blocked by the required quality gate

**Evidence**

- For red SHA `71d3aaf`, Railway API, Railway Web, and Vercel statuses are all `success`.
- The same SHA has two completed failing QG runs.
- Railway deployment IDs associated with this SHA differ from the IDs documented for `0bf1390b`.

**Impact**

- A commit can reach deployed environments while the mandatory gate is red.
- Exact-SHA release evidence can become internally contradictory.
- A future functional/security regression could be published before required verification finishes.

**Proposed resolution (not executed)**

- Make production deployment depend on the required exact-SHA gate conclusion, not only a push to the branch.
- Separate preview deployments from production and label them distinctly.
- Add a release assertion that deployed SHA equals the approved gate SHA.

**Acceptance**

- A deliberately failing QG commit cannot update production.
- A successful release records one approved SHA across QG, M04/M09 as applicable, Railway API/Web, and current documentation.

### HIM-AUD-003 — HIGH — Current production documentation is already stale

**Evidence**

- Current documents say production is deployed at `0bf1390b` with API deployment `f160b611-...` and Web deployment `7f6fec27-...`.
- GitHub deployment statuses show successful Railway API/Web deployments for descendant SHA `71d3aaf` with different deployment IDs.
- `71d3aaf` is docs-only, so runtime behavior may be equivalent, but the claimed exact deployed SHA is no longer exact.

**Impact**

- Incident response, rollback selection, and audit evidence can target the wrong deployment record.
- The distinction between functional SHA and deployed artifact SHA is not represented consistently.

**Proposed resolution (not executed)**

- Track `functional_sha`, `artifact_sha`, and `deployed_sha` as separate fields.
- Update release evidence automatically from verified deployment metadata rather than hand-maintained prose.

### HIM-AUD-004 — HIGH — “Closed” status conflicts with live unmerged functional work and a production defect

**Evidence**

- `docs/ops/OPEN_ITEMS.md` says only external/owner items remain and specifically says merge/deploy and Admin Content Review are no longer open.
- PR #2 and PR #3 both implement competing Admin Content Review redesigns from the same baseline.
- PR #4 is an open draft titled `fix(audio): make supervisor playback same-origin and range-safe` and records that production upload/queue/stream succeeded while browser playback failed because the UI used an external presigned URL blocked by CSP.
- The PR #4 branch changes API streaming, BFF Range forwarding, admin playback, and regression tests (216 additions / 22 deletions across five files).

**Impact**

- Owners can be told the project is closed while a user-visible production workflow is known broken.
- Parallel work may overwrite or conflict with another active solution.

**Proposed resolution (not executed)**

- Introduce one machine-readable current-work ledger tied to PRs/issues.
- A confirmed production defect must automatically move the relevant area from CLOSED to REGRESSION_OPEN.
- Do not declare closure while draft/ready PRs target the official branch without an explicit disposition.

### HIM-AUD-005 — MEDIUM — Branch inventory is obsolete and incomplete

**Evidence**

- `docs/maintenance/HIMMA_BRANCH_INVENTORY_2026-09-18_AR.md` covers 39 branches.
- The live repository had 52 branches before the audit branch was created.
- It omits the current PR branches and the two divergent non-audio compact-review branches.

**Impact**

- Its conclusion that no non-audio branch carries unmerged required work is no longer valid as a current-state claim.
- Cleanup or merge decisions based on it can lose active work or preserve obsolete work indefinitely.

**Proposed resolution (not executed)**

- Generate branch inventory from Git ancestry and PR state.
- Record owner, purpose, last activity, relation to official, CI state, and disposition for every branch.

### HIM-AUD-006 — MEDIUM — No branch protection is reported for any live branch

**Evidence**

- GitHub branch listing returned `protected: false` for all 52 pre-audit branches, including `stage/02-content`.

**Impact**

- Direct pushes can bypass review, status checks, and linear-history expectations.
- This magnifies the deployment-before-gate risk in HIM-AUD-002.

**Proposed resolution (not executed)**

- Protect the official branch with required QG checks, review/owner approval, conversation resolution, and force-push/deletion denial.
- Decide explicitly whether M04/M09 are mandatory for every change or path/risk dependent.

### HIM-AUD-007 — MEDIUM — Competing implementations target the same admin flow

**Evidence**

- PR #2 and PR #3 both target `stage/02-content` and independently rebuild `/admin/content-preview`.
- Both change the same primary page and responsive E2E file, but with materially different implementations and test coverage.
- PR #2 is draft with 1,660 additions / 186 deletions; PR #3 is ready with 200 additions / 126 deletions.

**Impact**

- Review intent is ambiguous; merging both would conflict, while choosing one without an explicit decision can discard useful coverage.
- Large CSS/page rewrites make regression review harder.

**Proposed resolution (not executed)**

- Name one canonical PR, close/supersede the other with a recorded comparison, and cherry-pick only independently valuable tests if needed.

### HIM-AUD-008 — MEDIUM — Release traceability lacks immutable tags/releases

**Evidence**

- No Git tag or GitHub Release exists despite multiple documents describing production releases and exact SHAs.

**Impact**

- Release identity depends on mutable branch/docs conventions.
- Rollback and artifact provenance require manual reconstruction.

**Proposed resolution (not executed)**

- Create signed/annotated release tags only after verified gates and production confirmation.
- Attach the evidence manifest and migration/content digests to a GitHub Release or equivalent immutable record.

## Phase 1 open verification

- The latest rerun QG #987 for `71d3aaf` was still in progress at the evidence snapshot; two prior completed runs on the same SHA failed identically.
- Code-level verification of PR #4's playback root cause belongs to the backend/frontend audit phases and will not rely only on the PR description.
- The two divergent compact audio-review branches require semantic comparison against the contained implementation before a delete/archive recommendation.
