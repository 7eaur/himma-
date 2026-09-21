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

### Phase 2 — Delivery gates, runtime boundaries, and authorization

Status: code-level evidence captured; broader backend/frontend review remains in progress.

## Confirmed findings — Phase 2

### HIM-AUD-009 — CRITICAL — Pull requests to the official branch can receive no quality gate

**Evidence**

- The official/default branch is `stage/02-content`.
- `.github/workflows/ci.yml:6-10` runs `pull_request` only when the base branch is `main`; it does not include `stage/02-content` or `stage/*`.
- The same workflow's push filter includes `stage/*` but excludes `ux/*`.
- Ready PR #3 uses head `ux/admin-content-library-20260921` and base `stage/02-content`; GitHub reported no Actions runs for that PR/head.
- HIM-AUD-006 confirms that the target branch is also unprotected.

**Impact**

- A ready functional PR can be merged into the official branch without backend tests, frontend type/lint/unit/build checks, integration tests, dependency audit, or secret scanning ever running for the proposed merge.
- A post-merge push may start CI, but deployment can already proceed independently of that CI (HIM-AUD-002), so post-merge detection is not a safe substitute for a PR gate.

**Root cause**

- Workflow branch filters still encode `main` as the review target while repository governance moved the official/default branch to `stage/02-content`.
- Push and pull-request coverage are defined independently and have drifted from the live branch/PR naming scheme.

**Proposed resolution (not executed)**

- Trigger the full quality gate for pull requests whose base is the official branch (prefer an explicit canonical-branch setting or include `stage/02-content`).
- Add a small workflow-policy test that compares the GitHub default branch and open PR bases/heads with CI trigger coverage.
- Require the exact PR merge result, not only the head SHA, when enabling GitHub merge protection.

**Acceptance**

- A test PR from `ux/*` to `stage/02-content` starts the complete QG.
- GitHub blocks merge when any required job is absent, pending, skipped because of an upstream failure, or failed.

### HIM-AUD-010 — HIGH — Supervisor audio playback is broken by an internal CSP/streaming contract conflict

**Evidence**

- `apps/web/src/app/admin/(dashboard)/audio-review/page.tsx:35-42` calls `/api/recordings/stream-by-key`, reads JSON, and assigns the returned `data.url` directly to the audio element.
- `services/api/recordings.py:218-242` returns an external S3-compatible presigned `get_object` URL rather than streaming bytes from the application origin.
- `apps/web/next.config.ts:5-18` sets `media-src 'self' blob:` and `connect-src 'self'`, so the external storage origin is not permitted.
- `apps/web/src/app/api/[...path]/route.ts:18-57` does not forward an inbound `Range` header and only returns `content-type`, `cache-control`, and `x-request-id`; it cannot currently act as a range-safe media proxy even if the backend route is changed to return bytes.
- Open PR #4 independently implements same-origin authenticated streaming and range forwarding for this exact regression, but it is not merged into the official branch.

**Impact**

- A supervisor can receive a valid queued recording yet be unable to listen to it, blocking the human academic review authority and therefore assessment completion/progression.
- Relaxing CSP to accept a storage host would couple browser security policy to an external endpoint and still leave authorization/range behavior split across origins.

**Root cause**

- The storage API contract (`JSON containing an external URL`) and the browser security contract (`same-origin media only`) were designed/tested independently.
- Existing header tests assert general CSP hardening but do not exercise the actual audio playback origin or byte-range path.

**Proposed resolution (not executed)**

- Adopt one authenticated same-origin media endpoint that validates the key and authorization, fetches/streams the private object, supports `Range`, and returns only a safe header allowlist.
- Extend the BFF to forward `Range` and preserve `206`, `Content-Range`, `Accept-Ranges`, `Content-Length`, and the validated audio content type.
- Keep the restrictive CSP rather than adding a broad external media origin.

**Acceptance**

- Browser E2E verifies play/seek/resume for a real private object under the production CSP.
- Unauthorized and invalid-key requests fail; non-audio objects cannot be proxied; a byte-range request receives correct `206` semantics.

### HIM-AUD-011 — HIGH — Any supervisor can create another privileged supervisor account

**Evidence**

- `services/api/dependencies.py:get_current_user` recognizes one privileged role, `researcher`; it has no owner/administrator capability distinction.
- `services/api/protected.py:107-130` allows every authenticated `researcher` to list all supervisor accounts and create another active `researcher` account.
- `apps/web/src/app/admin/(dashboard)/settings/page.tsx` exposes the supervisor-management tab and create form to every authenticated supervisor; it performs no capability check.
- The requirements reference defines a single researcher/admin role and explicitly places a multi-researcher institutional permission system outside scope; no accepted decision grants all supervisors account-provisioning authority.

**Impact**

- Compromise or misuse of any supervisor account can create a new persistent privileged account.
- There is no technical boundary between academic supervision and security-sensitive identity administration.

**Root cause**

- Product terminology migration from `researcher` to `supervisor` retained a flat legacy role while account-management features were added to the same role.

**Proposed resolution (not executed)**

- Decide the intended ownership model explicitly. For the smallest research deployment, restrict provisioning to a bootstrap owner or an offline/secret-controlled administrative operation.
- If multiple supervisors remain supported, add an explicit capability/role boundary, audit it, and test denial for ordinary supervisors.
- Review already-created accounts and document the recovery/revocation owner.

**Acceptance**

- An ordinary supervisor receives `403` for account provisioning and privileged account enumeration.
- The authorized owner path is separately authenticated, audited, rate limited, and covered by positive/negative tests.

### HIM-AUD-012 — MEDIUM — Critical domain invariants are not enforced by the database

**Evidence**

- `ContentAssetLink` allows `item_id` and `step_id` to both be null or both be set; there is no check constraint requiring exactly one parent.
- `AudioSubmission.status` is a free string with no check constraint, while runtime logic assumes a finite state set including `uploaded`, `graded`, and `rerecord_required`.
- `AudioSubmission` has no constraint preventing duplicate current rows for the same response/storage object; latest-row ordering is used as the application authority.
- `AdaptationDecision.action`, `decision_source`, `previous_level`, and `new_level` are unconstrained columns. Its model comment still lists `demote`, while current product tests and decisions forbid automatic demotion.
- The migrations mirror these unconstrained definitions; the gap is not only an ORM declaration issue.

**Impact**

- A script, seed, future endpoint, failed retry, or concurrent operation can persist impossible states that application code later interprets unpredictably.
- Corrupt asset ownership or audio/adaptation state can affect content projection, review queues, and progression evidence.

**Proposed resolution (not executed)**

- Add explicit check/unique/partial-index constraints after profiling existing production data.
- Centralize enum/state definitions used by migrations, ORM validation, API schemas, and tests.
- For intentionally append-only histories, encode the current-row uniqueness rule or make the selection policy explicit and concurrency-safe.

**Acceptance**

- Direct SQL tests prove invalid parent combinations, statuses, actions, sources, and levels are rejected.
- Migration preflight reports any existing violating rows before constraint installation.

## Phase 2 open verification

- Determine whether account provisioning was intentionally approved outside the current requirements reference; absent such a decision, HIM-AUD-011 remains an authorization defect.
- Profile live database rows before prescribing exact new constraints for HIM-AUD-012.
- Compare PR #4 implementation with the acceptance criteria above; its existence does not by itself prove the fix complete.
