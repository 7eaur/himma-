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

### Phase 3 — Executable verification, packaging, and inactive surfaces

Status: baseline checks executed; PostgreSQL migration cycling and authenticated browser journeys remain open.

#### Exact baseline verification executed on 2026-09-21

- Backend: `902 passed`, `5 warnings`, Python 3.12, SQLite test fixture, 336.77 seconds.
- Frontend: ESLint passed; `tsc --noEmit` passed; Jest `10/10` suites and `40/40` tests passed; Next.js production build passed and generated 20 routes/pages.
- Dependency audit: `pip-audit 2.10.1 -r services/api/requirements.txt` reported no known vulnerabilities at resolution time; `npm audit --audit-level=high` reported zero vulnerabilities.
- Content: legacy catalog validation passed at 105 items/44 skills; canonical release passed at 125 items with verified media and digest `e6c749add3652ca8aa896065218673eaac8a07cd0cbca1e92710f35f14f5a904`.
- The two tests under `packages/content/tests` passed when invoked directly (`2 passed`), but are not collected by the normal backend command from `services/api`.
- Public production desktop visual inspection covered the landing page, student login, and supervisor login. All rendered, had coherent RTL hierarchy, and exposed labelled controls. Authenticated/admin/student journeys were not claimed from this public inspection.

The green checks above are positive evidence, but they do not invalidate HIM-AUD-010 or HIM-AUD-011: the current suite does not exercise the cross-origin playback contract or ordinary-supervisor provisioning denial.

## Confirmed findings — Phase 3

### HIM-AUD-013 — HIGH — Production Python runtime is different from the tested runtime and dependencies are not reproducibly locked

**Evidence**

- `.github/workflows/ci.yml` runs backend and integration on Python 3.12.
- `deploy/railway-api.Dockerfile:2` builds production from `python:3.13-slim`.
- `services/api/requirements.txt` uses open lower bounds (`>=`) for 16 of 17 direct dependencies; there is no Python lock file or hashed constraints file.
- The same requirements file resolved successfully during this audit, but that only proves the dependency set selected on 2026-09-21. A future build can select different versions without a repository change.
- The test run already emits framework deprecation warnings, including Starlette's deprecated `HTTP_413_REQUEST_ENTITY_TOO_LARGE` symbol.

**Impact**

- CI can pass on Python 3.12 and one transitive dependency graph while Railway publishes a different interpreter/dependency graph.
- A rebuild of an unchanged commit is not guaranteed to produce the same behavior or artifact, weakening rollback and exact-SHA evidence.

**Proposed resolution (not executed)**

- Choose one supported Python version for development, CI, and production and pin the container base by immutable digest.
- Generate a reviewed lock/constraints file with hashes; update it through an explicit dependency-refresh workflow that runs tests and audits.
- Treat deprecation warnings as scheduled maintenance with owner/deadline before the corresponding breaking upgrades.

**Acceptance**

- CI tests the exact interpreter and locked graph used by the production image.
- Rebuilding the same commit resolves identical artifacts/dependency versions, and vulnerability auditing runs against that locked graph.

### HIM-AUD-014 — MEDIUM — CI omits repository-owned package checks and one E2E dependency is accidental

**Evidence**

- `packages/content/package.json` defines TypeScript `build` and `lint`, but CI only invokes its Python catalog validator; it never runs the package TypeScript build/lint.
- `packages/content/tests/test_reinforcement_v2_contract.py` is outside `services/api`; `pytest` executed with working directory `services/api` does not collect it. The two tests pass only when run separately from the repository root.
- `apps/web/tests/e2e/w6-axe.spec.ts` imports `axe-core`, but `apps/web/package.json` does not declare it. It currently exists only transitively through `eslint-config-next -> eslint-plugin-jsx-a11y`.
- The `@himma/content` TypeScript compile happened to pass in this audit when driven with the web installation's TypeScript binary; that is not a declared package installation or CI contract.

**Impact**

- Package code/tests can regress while the main gate stays green.
- A harmless change in ESLint's transitive graph can make the accessibility E2E suite fail to resolve `axe-core` even though project code did not change.

**Proposed resolution (not executed)**

- Define one root workspace/test orchestrator or explicitly run every owned package's install/build/lint/test in CI.
- Move/collect content tests under a deliberate test root.
- Declare `axe-core` directly at the version expected by the accessibility tests.

**Acceptance**

- A deliberate failure in `packages/content/src/index.ts` and in `packages/content/tests` fails CI.
- `npm ls axe-core` shows a direct declared dependency for the E2E owner.

### HIM-AUD-015 — MEDIUM — Repository contains inactive or misleading deployable-looking subsystems

**Evidence**

- `services/worker/main.py` contains only an infinite 10-second heartbeat loop and no queue consumption; its sole dependency is Redis, which it never imports or uses.
- The actual speech job consumer is `services/api/speech_worker.py`; no workflow, deployment file, or production code references `services/worker/main.py`.
- `packages/contracts/package.json` declares `main: index.ts`, but no such file exists and no repository source imports `@himma/contracts`.
- `@himma/content` exposes a TypeScript facade that no application imports; runtime content is compiled/published through Python and JSON sources.
- Root utilities `test_integration.py`, `test_minio.py`, `set_researcher_pass.py`, and `services/api/create_db.py` have no current workflow/code references and sit outside the owned test/runtime entry points.

**Impact**

- Operators and new engineers can deploy or maintain components that do no useful work, or assume a shared contract package exists when it does not.
- Security/dependency/ownership surface grows without product value.

**Proposed disposition (not executed)**

- Classify each item as active, archive/reference, or delete. Do not keep placeholder deployable packages in the active tree.
- If a worker service is required, point it to the real queue consumer with an explicit deployment contract; otherwise remove `services/worker`.
- Remove the empty contracts package or implement and consume it under tests; do not retain a broken package manifest.
- Move historical/manual utilities to a clearly non-production archive only if evidence retention requires them.

**Acceptance**

- Every active package/service has an owner, executable check, deployment/use reference, and correct entry point.
- A generated unused-surface inventory is empty or contains only documented archive exceptions.

### HIM-AUD-016 — MEDIUM — Local configuration has two conflicting owners and a stale Docker workflow

**Evidence**

- `.env.example` uses `DATABASE_URL`, `S3_BUCKET_NAME=himma-audio`, and includes `HIMMA_MAX_STUDENTS`.
- `env.example` instead uses split `DB_*` variables, `S3_BUCKET_NAME=himma-storage`, `API_PORT`, and lacks `HIMMA_MAX_STUDENTS`.
- Current application database code requires `DATABASE_URL`; split `DB_*` variables are owned only by `docker-compose.yml`.
- `docker-compose.yml` remains at repository root and presents PostgreSQL/Redis/MinIO as a local workflow, including mutable `minio/minio:latest`, while `docs/specs/ARCHITECTURE_BASELINE.md` says the project does not depend on Docker locally and current CI starts native services.

**Impact**

- Following the wrong example can configure a different bucket or omit the study-wide capacity control.
- The root Compose file appears authoritative but conflicts with the accepted operating model and uses a mutable storage image.

**Proposed disposition (not executed)**

- Make `.env.example` the single generated/validated environment contract shared by API, web, scripts, CI, and deployment documentation.
- Remove or archive `env.example` and the root Compose workflow after verifying no supported operator uses them; if Compose is intentionally retained as optional, label it explicitly and pin every image by digest.

**Acceptance**

- A configuration-schema check proves every required runtime variable appears once with one meaning/default policy.
- Onboarding and CI reference the same supported local service workflow.

### HIM-AUD-017 — MEDIUM — Authentication redirect context is generated but discarded

**Evidence**

- `apps/web/src/proxy.ts:10-17` redirects an unauthenticated protected request to the role-appropriate login and stores the original path/query in `?next=...`.
- `apps/web/src/proxy.test.ts` explicitly tests preservation of `/student/session/4?mode=resume` in that query parameter.
- Both login pages ignore `next`; after success they always replace the route with `/admin` or `/student`.

**Impact**

- Session expiry, deep links, notifications, and bookmarks lose the requested context after reauthentication.
- The test proves only the first half of the contract, so the suite stays green while the end-to-end behavior is incomplete.

**Proposed resolution (not executed)**

- Parse `next` through a strict same-origin relative-path allowlist for the authenticated role, then redirect there after login; otherwise use the role home.
- Add E2E coverage from protected deep link through login to final destination, including hostile absolute/protocol-relative values.

**Acceptance**

- Valid role-scoped deep links resume exactly; external URLs and cross-role paths are rejected to the safe home route.

### HIM-AUD-018 — LOW — Content package documentation describes a retired runtime owner

**Evidence**

- `packages/content/README.md` calls `src/catalog.json` the sole executable mirror and says `services/api/seed.py` reads only that catalog.
- Current source-of-truth and executable code compile a 125-item release from the 105-item baseline plus versioned additions through `canonical_release.py` and publish it through the canonical publisher.
- The audit executed both boundaries: the legacy validator correctly reported 105, while canonical release correctly reported 125.

**Impact**

- A maintainer can edit/validate only the 105-item baseline and incorrectly believe the full runtime release is covered.

**Proposed resolution (not executed)**

- Rewrite the package README around the baseline-input versus canonical-runtime distinction and link the single publish/readiness path.

### Phase 1 branch disposition addendum

- `redesign/audio-review-compact-20260920` and `integration/audio-review-compact-20260920` share five old commits and are 27 official commits behind. The integration branch adds only three follow-up commits.
- None of their eight commits is an ancestor of the official branch. The official branch instead contains a newer sibling implementation starting at `50d0477 refactor(admin): compact audio review workspace`, plus later deep-link/test work.
- Their intended behavior (two-column evidence/evaluation, stable decision names, optional notes, compact mobile CSS, visual QA) is visibly represented in the current official page/global admin workflow and tests.
- Disposition: archive/delete after recording this proof; do not merge either divergent branch into the official line.

### Phase 4 — Assessment authority, reporting integrity, and query behavior

Status: critical route/report interactions reproduced against the baseline; wider endpoint-by-endpoint review remains in progress.

#### Runtime probes executed on 2026-09-21

- Router enumeration found 77 declared operations but only 75 unique method/path signatures. The duplicates are exactly `POST /assessment/start` and `POST /assessment/session/{session_id}/finish`.
- The generated OpenAPI document describes the legacy `assessment.start_assessment` and `assessment_completion.finish_assessment` operations, while the retake router is registered first and current retake integration behavior proves that its handlers receive requests.
- An isolated database probe created one completed official pretest (score 65, level 2) followed by an in-progress non-official retake. The research report returned the retake as `in_progress`, with `score: null` and `starting_level: null`, discarding the still-official completed result.
- Query instrumentation of an otherwise empty cohort report produced 4 SELECTs for 1 student, 16 for 5 students, and 151 for 50 students. This is the exact linear `1 + 3N` floor before attempts and other evidence add further queries.

## Confirmed findings — Phase 4

### HIM-AUD-019 — HIGH — Assessment start and finish each have two route owners, and documentation describes a different handler from runtime

**Evidence**

- `services/api/assessment_retake.py:123-162` owns `POST /assessment/start` with retake authorization/attempt-history behavior; `services/api/assessment.py:363-407` also owns the same method/path with a different legacy policy.
- `services/api/assessment_retake.py:165-177` owns `POST /assessment/session/{session_id}/finish` and marks the completed attempt official; `services/api/assessment_completion.py:254-266` also owns that method/path but only completes/scores the session.
- `services/api/main.py:56-64` claims every critical URL has one mounted owner and must not depend on router order, but includes the retake router first, completion second, and assessment third.
- OpenAPI resolves each duplicate to the later legacy handler (`start_assessment...` and `finish_assessment...`), so generated clients/docs do not describe the handler selected by first-match request dispatch.
- `services/api/test_assessment_completion_route.py:1-21` claims to verify one authoritative finish owner but compares only the assessment and completion routers; it omits the retake router that contains the duplicate. There is no equivalent whole-application start-route uniqueness assertion.

**Impact**

- Router reordering or framework inclusion behavior can silently bypass retake authorization/history on start or fail to select the new official attempt on finish.
- Operations and generated clients can reason from an OpenAPI contract that differs from actual request behavior.
- The current regression test provides false confidence because it does not inspect all mounted routers or unique method/path signatures.

**Root cause**

- New retake behavior was implemented as replacement endpoint wrappers while the previous endpoint declarations remained mounted.
- Ownership is tested module-by-module instead of at the assembled application boundary.

**Proposed resolution (not executed)**

- Keep exactly one route declaration for each public method/path. Move scoring and retake policy into reusable services invoked by that single owner.
- Add an assembled-app assertion that no method/path signature is duplicated, plus explicit assertions for endpoint module/function identity and OpenAPI operation identity.
- Add contract tests that a completed test cannot restart without authorization and that finishing a retake atomically makes it the only official attempt.

**Acceptance**

- The assembled route table has one unique signature per operation, with no duplicate start/finish owner.
- OpenAPI, request dispatch, and source ownership all name the same handler.

### HIM-AUD-020 — HIGH — Research reports ignore the official assessment attempt and can erase a valid baseline during a retake

**Evidence**

- `AssessmentSession.official_for_reporting` exists specifically to identify the selected completed pre/post attempt, and retake completion updates it in `assessment_retake.py:86-90`.
- `services/api/reports.py:59-67` does not filter or prioritize that flag. It loads all pre/post sessions by ID and overwrites each type with the newest row.
- `reports.py:70-139` then derives score, starting/final level, elapsed time, attempt counts, and cohort improvement from that newest row.
- The reproduced case—official completed pretest score 65/level 2 plus a newer in-progress retake—returned `pretest.status = in_progress`, `score = null`, and `starting_level = null` even though the official completed baseline remained valid.
- Retake tests verify flag transitions, while report tests cover single-attempt and generic incomplete-posttest cases; no test connects report selection to `official_for_reporting` during a retake.

**Impact**

- Starting a retake can temporarily remove a learner's valid baseline and reduce completed-pretest/paired cohort counts in dashboards and exports.
- A failed, abandoned, or long-running retake can leave research output inconsistent with the explicitly selected official academic record.
- Study metrics can change because a retake began, before any replacement result is complete and accepted.

**Proposed resolution (not executed)**

- Select the one completed `official_for_reporting = true` attempt for research outcome fields. Represent an active retake separately instead of replacing the official result.
- Enforce at most one official completed attempt per student/session type with a PostgreSQL partial unique index after production-data profiling.
- Add report regressions for pending, completed, abandoned, and superseded retakes, including cohort XLSX/PDF exports.

**Acceptance**

- Starting an authorized retake does not change official scores, placement, paired counts, or improvement metrics.
- Completing the retake switches all report/export surfaces to the new official attempt in one committed transaction.

### HIM-AUD-021 — MEDIUM — Assessment completion and official-attempt selection are committed in separate transactions

**Evidence**

- `assessment_completion.finish_session` updates the student/session and commits at `services/api/assessment_completion.py:231-235`.
- Its retake wrapper only afterwards clears prior official flags, marks the completed session official, and commits again at `services/api/assessment_retake.py:174-176`.
- The direct duplicate completion owner never calls the official-selection function at all (HIM-AUD-019).

**Impact**

- A process failure or database error between the two commits leaves a completed result without the intended official selection, while prior flags and reporting may retain a contradictory state.
- A retry sees a completed session and rejects it before repairing the missing official transition.

**Proposed resolution (not executed)**

- Make the completion service flush but not commit; let one route-level transaction persist scoring, learner state, audit evidence, and official selection atomically.
- Add a forced-failure test immediately before commit and prove rollback restores every affected row.

**Acceptance**

- There is one transaction boundary for completion and official selection, and no observable completed-but-unselected intermediate state.

### HIM-AUD-022 — MEDIUM — Cohort reporting has a proven per-student N+1 query floor

**Evidence**

- `services/api/reports.py:149-151` loads all students and then calls `build_student_research_report` once per student.
- Each call separately loads pre/post sessions, core sessions, and reinforcement cycles; students with sessions add separate attempt-count queries at `reports.py:83-91`.
- SQLAlchemy instrumentation measured 4 SELECTs for 1 empty student, 16 for 5, and 151 for the configured 50-student maximum: `1 + 3N` before attempt-count queries.
- Exports build the same cohort report synchronously before serializing XLSX/PDF, so the query multiplication affects both dashboard reads and downloads.

**Impact**

- Database round trips grow linearly per student and per evidence category, creating avoidable latency and load at the project's own configured cohort limit.
- Additional report fields implemented in the same pattern will compound the cost.

**Proposed resolution (not executed)**

- Fetch selected official sessions, core summaries, attempt counts, and reinforcement aggregates in bounded set-based queries keyed by student ID.
- Add a query-budget regression at 1 and 50 students; the upper bound should be constant or a small documented constant independent of cohort size.

**Acceptance**

- A 50-student cohort report stays within the agreed query budget and produces byte-for-byte equivalent normalized report data.

### Phase 5 — Authorization matrix, documentation ownership, assets, and release images

Status: assembled API dependency matrix and static/runtime surface inventory captured; authenticated visual journeys and production-data profiling remain open.

#### Positive boundary evidence

- Every mounted learner operation declares `get_current_student`; every mounted supervisor/research operation declares `get_current_user`; shared identity/catalog reads use `get_any_authenticated`.
- The only business asset route without authentication is `/media/{asset_id}`. It resolves IDs from checked-in approved manifests and validates resolved paths remain below the approved asset roots; arbitrary filesystem paths are not accepted.
- No confirmed cross-student IDOR was found in the inspected assessment, activity, adaptation, journey, recording, report, or review ownership queries. This is a positive static result, not a substitute for a two-student negative integration matrix.
- Login throttling is active in `trial`/`production`, hashes identifiers before Redis storage, combines IP and identifier budgets, and fails closed when Redis is unavailable.

### HIM-AUD-023 — MEDIUM — Documentation has multiple simultaneous “current” owners and an active-looking obsolete policy

**Evidence**

- `docs/` contains 166 files (163 Markdown), including 40 files named as handoffs and 30 named as checkpoints; 121 Markdown files contain closure/green/readiness language.
- `docs/ops/DOCUMENTATION_INDEX.md` lists 19 separate documents/rules as `CURRENT / AUTHORITATIVE`, including mutable status, roadmap, changelog, evidence, deployment, open-items, decisions, architecture, and branch inventory owners.
- Those current documents duplicate the same branch/SHA/state fields. Several still assert `CLOSED / PRODUCTION_GREEN` and exact SHA `0bf1390b` despite the red/deployed descendant and open production defect recorded in HIM-AUD-001 through HIM-AUD-004.
- `docs/maintenance/SOURCE_OF_TRUTH_POLICY_AR.md` labels itself `ACTIVE` but names retired branch `recovery/ui-media-admin-overhaul` as the branch being unified. It is not listed in the documentation index, while its title/status still makes it appear authoritative.
- The index itself marks `HIMMA_BRANCH_INVENTORY_2026-09-18_AR.md` current even though HIM-AUD-005 proves that inventory omits live branches and active PR work.

**Impact**

- Updating one state document cannot make repository truth consistent; stale copies continue to direct owners and future agents.
- “Historical unless listed” is insufficient when historical policy files still self-identify as ACTIVE and current-listed files are stale.
- Documentation volume increases secret-scanner false positives and review noise, as already manifested in HIM-AUD-001.

**Proposed resolution (not executed)**

- Reduce live state to one generated machine-readable manifest and one human entry page. Keep decisions/specifications as separate stable records, not parallel status owners.
- Move dated handoffs/checkpoints to an explicit archive tree with an archive banner generated/validated in CI, or preserve them outside the active product tree when Git history already supplies provenance.
- Generate branch/deployment/gate fields from GitHub and deployment metadata; prohibit hand-entered duplication across current documents.

**Acceptance**

- A documentation linter finds exactly one owner for official branch, functional SHA, deployed SHA, gate SHA, release state, and open-work state.
- No archived file self-identifies as current/active, and current links cannot point to stale branch inventories.

### HIM-AUD-024 — LOW — The web public tree retains confirmed duplicate and scaffold-only assets

**Evidence**

- Five flat character files under `apps/web/public/characters/boy-*.png` are byte-identical by SHA-256 to the canonical files under `characters/boy/*.png`. Runtime references use the nested paths.
- `file.svg`, `globe.svg`, `next.svg`, `vercel.svg`, and `window.svg` are unchanged Next scaffold assets with no application reference.
- `brand/logo-flat.svg`, four `public/audio/fb-*.mp3` files, and `characters/girl/try-again.png` have no production source reference. The feedback audio is referenced only by the root manual scripts already classified inactive in HIM-AUD-015.
- These confirmed/candidate inactive public assets total approximately 880 KiB. Reward badge assets were excluded from this finding because their paths are generated by the backend reward catalog even when a literal filename is absent from frontend source.

**Impact**

- Duplicate public URLs and retired assets obscure which visual/audio contract is canonical and can be accidentally reused.
- Static output and review surface include files with no supported product owner.

**Proposed disposition (not executed)**

- Delete byte-identical duplicates and framework scaffolds after a generated route/reference check.
- Decide whether feedback audio is a planned governed feature; otherwise remove it with the inactive manual scripts. Do not delete any catalog/manifest-generated asset based only on text search.

**Acceptance**

- A build-time asset graph accounts for every file in `public/` as directly referenced, catalog-generated, compatibility-routed, or explicitly retained.

### HIM-AUD-025 — MEDIUM — Release containers copy broad source trees and run as root

**Evidence**

- There is no repository `.dockerignore`.
- `deploy/railway-api.Dockerfile` uses `COPY . /app`, so the API build/runtime image receives frontend source, 1.3 MiB of documentation, 18 MiB of historical/reference material, tests, manual utilities, and other repository content in addition to required API/content/assets.
- The tracked working areas are approximately 92 MiB `assets/`, 18 MiB `reference/`, 6.6 MiB `apps/`, 5.6 MiB `services/`, and 1.3 MiB `docs/`; the packed Git repository is about 108 MiB. The runtime needs selected assets and content inputs, not the complete reference/frontend/history surface.
- Both Railway Dockerfiles inherit the default root user and define no `USER`. The API image is also single-stage and retains source/tests and installation context in the runtime layer.

**Impact**

- Builds transfer and preserve unnecessary material, increasing build time, image size, cache invalidation, and the amount of proprietary/reference content present in a compromised container.
- A process compromise begins with root privileges inside the container rather than a least-privileged application identity.

**Proposed resolution (not executed)**

- Define an explicit build context allowlist via `.dockerignore` and narrow `COPY` instructions to required runtime code, migrations, canonical content inputs, and approved served assets.
- Use multi-stage builds, remove test/manual/cache material from runtime layers, pin bases by digest, and run both services as dedicated non-root users with read-only filesystem expectations where practical.
- Add an image-content/size policy and container user assertion to CI.

**Acceptance**

- Runtime images contain no `reference/`, historical docs, frontend source in the API image, test suites, or repository metadata; both report a non-zero non-root UID.

### HIM-AUD-026 — MEDIUM — The deployed browser security policy still permits inline scripts and omits transport pinning

**Evidence**

- `apps/web/next.config.ts:3-24` sets several useful headers but declares `script-src 'self' 'unsafe-inline'` and emits no `Strict-Transport-Security` header.
- A live response from `https://himma-web-production.up.railway.app/` on 2026-09-21 confirmed the same inline-script allowance, no HSTS header, and disclosure of `X-Powered-By: Next.js`.
- The policy uses neither a nonce nor script hashes, so CSP cannot block an injected inline script if a future rendering/injection defect is introduced.

**Impact**

- CSP provides less defense-in-depth against cross-site scripting than its presence suggests.
- Without HSTS, the browser does not remember an HTTPS-only policy for subsequent visits; platform redirects alone are not the same browser-enforced boundary.

**Proposed resolution (not executed)**

- Move to a nonce/hash-compatible Next.js CSP and remove `unsafe-inline` from `script-src` after verifying framework/runtime compatibility.
- Add HSTS only after confirming every production/subdomain dependency is HTTPS-safe; disable the framework signature header.
- Add a production header probe to the release gate, not only static configuration tests.

**Acceptance**

- Live production responses contain the approved HSTS policy, omit `X-Powered-By`, and execute with a nonce/hash CSP that rejects an injected inline-script fixture.

### Phase 6 — Executed test inventory and coverage truth

Status: complete-suite measurements captured on the baseline; production code was not changed.

#### Positive execution evidence

- The complete backend suite passed on the audit host: `902 passed, 5 warnings in 438.80s`.
- Backend statement coverage across the application source, excluding tests/migrations/seed and verification utilities, measured 83% (`7,004` statements, `1,198` missed).
- The complete frontend Jest suite passed: 10 suites and 40 tests.
- The checked-in Playwright suite contains 22 specification files, including full assessment journeys that complete 30 questions, the human audio-review step, and session finish. The completion path therefore has some browser-level coverage even though its direct backend coverage is weak.

### HIM-AUD-027 — HIGH — Green test totals conceal unexecuted suites and critical coverage gaps

**Evidence**

- Running Jest with explicit collection over `apps/web/src/**/*.{ts,tsx}` measured only 24.09% statements, 67.14% branches, 27.05% functions, and 24.09% lines. `apps/web/jest.config.js:8-16` defines no coverage threshold, so the ordinary 40-test result remains green regardless of how much production code is untested.
- The zero-coverage frontend surface includes both login pages, almost all admin pages, the student assessment page, the authenticated BFF route, auth routes, most shared components, `useAudioRecorder`, and IndexedDB support. The student dashboard and activity page have meaningful unit coverage, so this is not a blanket absence of tests; it is a risk-weighting gap.
- The backend aggregate is stronger at 83%, but critical modules remain thin: `assessment_completion.py` 26%, `storage.py` 26%, `activities.py` 57%, `speech_analysis.py` 67%, `recordings.py` 67%, and `auth_session_state.py` 68%. The real speech job consumer `speech_worker.py` and media-contract validator each measured 0%.
- The successful direct backend suite does not execute the success body of `assessment_completion.finish_session` (`assessment_completion.py:211-237`); it exercises validation/fail-closed branches. Browser journeys do finish assessments, but that does not provide focused concurrency, rollback, or transaction-boundary coverage for HIM-AUD-021.
- The repository has 22 Playwright spec files. The main CI and M09 workflows hard-code the same 12 filenames, while M04 separately runs `responsive-smoke.spec.ts`. Nine specs are referenced by no workflow: `audio-review-filtered-context`, `browser-flow`, `font-loading`, `home-login`, `p03-screenshots`, `student-detail-cross-device-integrity`, `student-detail-journey-states`, `student-detail-partial-source-errors`, and `student-viewport-safety`.
- Several omitted specs are substantive regression coverage rather than disposable screenshots: filtered audio-review context, cross-device student integrity, partial-source failure behavior, journey states, viewport safety, and font loading. A newly added spec can therefore exist indefinitely without CI noticing it.
- `apps/web/playwright.config.ts:20-31` launches the only browser project with `--disable-web-security`. This changes the browser same-origin/CORS security model for every E2E run and reduces fidelity to the deployed topology.
- `apps/web/tests/e2e/home-login.spec.ts:42-45` catches and discards the failed wrong-credential error assertion. If that spec is run without the backend, the test reports success without proving its stated behavior.

**Impact**

- Passing totals such as `902`, `40`, and `23` can be repeated in release documents while important repository-owned tests never execute and high-risk browser/API code has no enforced coverage floor.
- The BFF/audio path implicated in HIM-AUD-010, assessment finalization in HIM-AUD-021, authentication UI, recording hooks, and admin workflows can regress without a targeted required test failing.
- Disabling web security can hide integration failures involving origin and CORS that users experience in a normal browser.

**Proposed resolution (not executed)**

- Replace duplicated filename allowlists with a declared test manifest: every Playwright spec must be assigned to a required PR tier, scheduled extended tier, or explicit manual/visual tier. Fail CI when a spec is unclassified.
- Add risk-based coverage floors for the authenticated BFF, authentication, recording/audio, assessment completion, official-attempt selection, reports, and admin mutation flows. Use per-module thresholds rather than relying only on a repository aggregate.
- Run at least one required Chromium project with normal web security against the same-origin production-style BFF topology. Isolate fake media-device flags to tests that need them.
- Remove swallowed assertions. Tests that require the full stack must either provision it, explicitly skip with a visible reason, or mock a precise failure contract.
- Add focused failure/concurrency tests for assessment finalization, official-attempt selection, storage/streaming, and notification mutations; preserve the existing full-journey coverage.

**Acceptance**

- CI fails when any Playwright spec is not classified or when a required tier is silently omitted.
- Critical-module coverage meets documented floors, and the baseline Jest coverage cannot fall while remaining green.
- A normal-security browser project proves login, authenticated BFF access, audio byte-range playback, and representative cross-origin rejection behavior.
- No test catches and ignores a failed product assertion.

### HIM-AUD-028 — MEDIUM — Notification mutations report success in the UI when persistence fails

**Evidence**

- `apps/web/src/components/admin/AdminNotifications.tsx:21-28` catches and discards every network exception from the single-notification read request, never checks `response.ok`, then unconditionally decrements the unread count and marks the item read in local state.
- `AdminNotifications.tsx:37` applies the same pattern to “mark all”: it ignores transport failure and every non-2xx response, then unconditionally sets the displayed unread count to zero and all local items to read.
- The backend endpoints are durable mutations and can legitimately fail: `services/api/admin_notifications.py:47-60` returns 404 for a missing item and commits the read state; `:63-74` commits the bulk mutation. Both are authenticated and can also return authorization or infrastructure errors.
- There is no frontend component test for `AdminNotifications`; the backend tests prove only successful/idempotent API behavior. This surface is also part of the zero-coverage frontend area in HIM-AUD-027.

**Impact**

- On an expired session, server error, or lost connection, the interface tells the supervisor that required review work was acknowledged when the durable inbox still considers it unread.
- The next poll or page load can make apparently cleared notifications reappear, undermining trust in a workflow used for audio review and learner intervention.

**Proposed resolution (not executed)**

- Check both transport and HTTP success before updating local state. On failure, retain the unread state and show an actionable error.
- If optimistic updates are desired, snapshot and roll back state on failure, serialize/reconcile concurrent refreshes, and disable duplicate mutation actions while pending.
- Add component tests for 200, 401, 404, 500, network failure, retry, and a refresh racing with a mutation.

**Acceptance**

- A failed mark-one or mark-all request never displays durable success; the unread count remains consistent with the next server response.
- Successful mutations remain idempotent and do not double-decrement during rapid interaction.

### HIM-AUD-029 — MEDIUM — The authenticated BFF is a lossy, fully buffered proxy with no upstream timeout

**Evidence**

- `apps/web/src/app/api/[...path]/route.ts:36` materializes every non-GET/HEAD request as a `Blob`; `:38-39` then waits without an abort deadline and materializes every upstream response as an `ArrayBuffer` before returning any bytes.
- The backend allows audio uploads up to 10 MiB (`services/api/storage.py:8,37-40`), so an accepted upload is buffered at the web boundary and again at the API storage boundary. Export responses are also completely generated and then completely buffered through the BFF.
- The proxy forwards only `content-type`, cookie, `x-request-id`, and optional `idempotency-key`; it constructs the response with only `content-type`, computed cache control, and request ID, plus `set-cookie` (`route.ts:18-28,40-60`).
- Consequently it drops standard representation headers including `Content-Disposition`, `Content-Length`, `Content-Range`, and `Accept-Ranges`, and does not forward the incoming `Range` request. The missing byte-range contract is one cause of the production playback defect in HIM-AUD-010.
- Report endpoints intentionally emit filenames such as `himma-research-cohort.xlsx` and `himma-research-cohort.pdf` in `Content-Disposition` (`services/api/reports.py:454-458,484-524`), but the browser cannot receive those headers through the BFF links used by the reports UI.
- `apps/web/src/app/api/[...path]/route.test.ts` tests only the cache-policy helper; it never executes the proxy, verifies streamed bytes, exercises failure/timeout behavior, or asserts header preservation. The three separate auth BFF routes repeat the no-timeout/full-buffer response pattern.

**Impact**

- Slow or stuck upstream requests can occupy web runtime capacity until an external platform deadline intervenes, with no controlled 504/error contract.
- Buffering delays first byte and multiplies memory pressure for uploads, exports, and future larger payloads.
- Dropped range and disposition metadata changes endpoint behavior at the browser boundary: audio seeking/playback fails and exported files lose their authoritative filenames.

**Proposed resolution (not executed)**

- Define an explicit request/response header allowlist by endpoint class, including safe forwarding of `Range` and preservation of `Content-Range`, `Accept-Ranges`, `Content-Length`, and `Content-Disposition` where applicable.
- Stream request and response bodies rather than converting them to `Blob`/`ArrayBuffer`; enforce an early body-size boundary and add an abort deadline with a stable 504 response.
- Consolidate auth and generic proxy behavior into a tested helper while preserving cookie rules and private cache policy.
- Add integration tests against a controllable upstream for partial content, report filename, large/slow body, disconnect, timeout, upstream 5xx, and multi-value cookie behavior.

**Acceptance**

- A browser request for an audio byte range receives a correct 206 response and range headers through the BFF.
- XLSX/PDF downloads retain their backend-declared filenames.
- Slow upstreams terminate at the documented deadline, and body transfer is streamed within an agreed memory budget.

### Phase 7 — Privacy, retention, recovery, and operational boundaries

Status: repository policy/runtime comparison complete; no claim is made that real child data is currently present because production data was not inspected.

#### Positive operational evidence

- The repository contains PostgreSQL and object-store backup/isolated-restore utilities, integrity verification, and a synthetic M09 workflow exercise.
- `/ready` fails closed for required configuration, PostgreSQL, canonical content projection, approved static audio, object storage, Redis, and protected runtime security mode; its public response is sanitized.
- The current manual-review design correctly keeps unreviewed audio academically neutral and does not pretend that an unapproved ASR provider is production-ready.

### HIM-AUD-030 — HIGH — Production is declared green while its own child-recording privacy gate remains unapproved and unenforced

**Evidence**

- The authoritative runbook states: “No real child recording should be admitted until the researcher/client approves the retention/deletion policy” and requires identifiers, storage location, playback/download access, retention duration, study-end deletion/archive, backup destruction, and external-provider transfer terms to be recorded (`docs/ops/M09_RELEASE_UAT_RUNBOOK.md:122-134`).
- The same runbook explicitly says the automated M09 gate closes only infrastructure backup/readiness; privacy decisions and final release approval remain separate (`:148-159`).
- Nevertheless, `docs/ops/STATUS.md:3-7,54-69` declares `CLOSED / PRODUCTION_GREEN`, records successful Railway production services and an available audio bucket, then lists the child data/audio retention decision as only a remaining owner item. `docs/ops/ROADMAP.md:15-20` likewise marks Railway production deployed/verified while retention remains an owner/ethics boundary.
- The deployed code accepts student audio through assessment/activity upload routes and the recording compatibility flow. `services/api/storage.py:31-78` stores accepted audio in the configured object bucket; `services/api/recordings.py:103-188` issues direct upload URLs and finalizes stored objects.
- Repository search finds no student/recording deletion endpoint, retention-duration configuration, scheduled purge/archive job, object-store lifecycle configuration, or study-end erasure verifier. The only recording deletion is a defensive cleanup attempt for an oversized compatibility upload (`recordings.py:169-181`).
- `services/api/readiness.py:35-45,246-260` does not include an approved-retention-policy marker or deletion/lifecycle capability in readiness. Therefore `/ready = 200` cannot prove the runbook's privacy release condition.
- Backup procedures preserve database and object data, but the repository has no approved backup-retention/secure-destruction implementation tied to student deletion. This is exactly one of the unresolved decisions named by the runbook.

**Impact**

- The technical production label can be mistaken for authorization to begin a real-child study even though the repository's own explicit admission gate is still open.
- If real recordings are accepted before policy and deletion mechanics exist, operators cannot demonstrate when primary objects, relational metadata, derived speech records, audit references, and backups should be removed or retained.
- Backups increase recoverability but also create additional copies whose lifecycle must be governed; a restore test is not a retention/deletion policy.

**Proposed resolution (not executed)**

- Change release state to `TECHNICALLY_DEPLOYED / REAL-STUDY-BLOCKED` until the accountable owner/ethics authority approves a versioned policy. Do not infer or invent legal/ethical parameters from code.
- Record the approved data inventory, purpose, access roles, retention periods, legal/consent basis, study-end procedure, backup expiry/destruction, incident owner, and whether any provider receives audio.
- Implement an auditable lifecycle service that covers object-store bytes and all related database/derived records. Decide explicitly which audit evidence must be retained or pseudonymized rather than relying on accidental cascades.
- Add a non-secret policy approval/version marker and lifecycle capability check to the real-study release gate. Keep generic infrastructure readiness separate from authorization to admit participant data.
- Execute a synthetic deletion drill across primary storage, database relationships, derived artifacts, and expired backups before enabling real participants.

**Acceptance**

- Production documentation cannot say study-ready/green while the approved retention-policy version is absent.
- A synthetic participant deletion/expiry drill produces evidence that every governed copy is deleted, archived, or deliberately retained according to the approved policy.
- `/ready` remains an infrastructure probe, while a separate release/admission gate proves policy approval and lifecycle operability.
