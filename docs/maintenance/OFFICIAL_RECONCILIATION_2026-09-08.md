# Official repository reconciliation — audit and execution record
Date: 2026-09-08
Status: IN_PROGRESS — initial code audit; not an acceptance certificate.

## Pinned evidence
- Official repository: 7eaur/himma-
- Official source policy: docs/maintenance/SOURCE_OF_TRUTH_POLICY_AR.md.
- Base branch: recovery/ui-media-admin-overhaul.
- Base HEAD: e1cb0bb3ec10087a4032d189cf1d2bbf54c47163.
- Independent work branch: integration/official-content-reconciliation-2026-09-08.
- Prior executable candidate: 976b7c2ed8b9c6f1535a22a0b3a94b2c233f75eb.
- GitHub API verified completed/success for prior candidate: Quality 33979846641, M04 33979846639, M09 33979846640. This is historical evidence, not proof of these new changes.
- Default stage/02-content points to 2626168 (August 17); it must not be mistaken for the current integration base.
- Sandbox PR #2 merged, head f0314817f428235aed26e0db4c64a38548993118.
- Sandbox PR #3 is draft, head be802007d3751fabab68b63ad5c3053b952fdddf; its own transfer record explicitly leaves implementation verification open.

## Confirmed findings before code changes
| ID | Priority | Evidence / root cause | Required correction |
|---|---|---|---|
| A01 | P1 | ContentOption has no active state. seed_student_experience_v2 and seed_l1_auditory_story_replacement delete extra options or overwrite text/correctness/order by position. | Immutable option identities; retire historical rows; active-only new submissions; migration and historical-response tests. |
| A02 | P1 | seed.py _extract_options falls back to returning an entire source_text line. POST-Q08/Q13 are known examples in approved Sandbox documentation. | Explicit structured options and answer contracts; original serialized source remains historical only. |
| A03 | P1 | seed_db_runtime_contract._option_order falls back to option position; content_runtime.step_assets also zips images/options by position. | Explicit semantic mapping with stable option keys; missing mapping is a gap, not an inferred match. |
| A04 | P1 | POST_QUESTIONS n=11 still targets مِ; owner approved مَ, and LET-01 asset semantics already equal مَ. | Update the single content authority, scoring, target, and media together. |
| A05 | P1 | protected.create_student hardcodes 15; locks the invoking User row, allowing different supervisors to race the global capacity. | Central configurable default 50; common database lock and concurrency coverage. |
| A06 | P1 | proxy.ts only matches /admin; student layout is effects-only. | Protect /student including expired and wrong-role sessions; keep login publicly reachable and backend authorization authoritative. |
| A07 | P1 | /assessment/session/{id}/next exposes template_data, including criterion and embedded source/runtime answers, to the authenticated student (ContentItemResponse allows the field). | Sanitize all learner contracts, including legacy reachable endpoints. Verify forbidden fields recursively. |
| A08 | P1 | Two student renderers iterate images rather than an exact current option set; visible image labels reveal the answer vocabulary. | One option card per explicit mapping; shared image-only rendering contract. |
| A09 | P1 | Auditory story audio is rendered inside question rounds; independent listen intro is missing. | Structured intro then question phase; no recording or story playback in question rounds. |
| A10 | P2 | Timed reading displays recordingSeconds to the child. | Hide visual fluency counter while preserving duration collection. |
| A11 | P2 | Prompt playback uses sequential promises without cancellation settlement or pause/resume control. | Shared cancellable playback lifecycle with cleanup between rounds and unmount. |
| A12 | P1 | No official content-preview route/page in pinned tree. | Read-only preview backed by the exact student payload/renderers; no attempts or progress writes. |
| A13 | P1 | seed_all calls multiple independently committed overlays; seed_learning_posttest_projection_runtime monkeypatches base module globals at import. | Explicit deterministic source/projection ownership and atomic content application; no final repair seed masking conflicts. |
| A14 | P1 | review.grade_audio_submission reads uploaded status without row lock before inserting a review. | Serialize competing reviews; only one valid state transition. |
| A15 | P2 | readiness checks count/version markers, but not actual option correctness, mapping integrity, or content-source digest. | Validate semantic runtime invariants and content digest as part of readiness/seed gates. |

## Preserve from official
- DB-only runtime; no per-request JSON parsing.
- 30 pretest / 30 posttest / 30 core / 35 approved reinforcement = 125 runtime items, with 105 historical baseline items and 44 skills.
- ADR-014 placement; V4 same-level support, no automatic demotion, active-session evidence weighting and promotion gates.
- Human-authoritative audio grades; uploaded and rerecord_required are neutral.
- Retake history, manual override safety, durable notifications, reports and exports as read models.
- Existing approved 54 audio IDs / 108 binaries. Missing local downloads do not imply missing repository assets.
- No Docker, merge, deployment, production data changes, or Sandbox branch mutation.

## Intended implementation order
1. Historical-safe content schema/lifecycle, capacity and authenticated route boundaries.
2. Reconcile approved Sep-8 academic data into one versioned structured source; project atomically, preserving existing identities/history.
3. Shared student/preview presentation, explicit media, story phases, playback and internal timing.
4. Verify seed twice, upgrade/downgrade/upgrade, semantic invariants, backend, frontend, security, integration and student E2E on one final candidate.

## Verification in progress
- Text files fetched at pinned SHAs and their Git blob hashes verified.
- Existing attachment blobs reused only when their Git hashes exactly match the remote tree.
- Backend baseline suite running locally on disposable SQLite; no claim that this equals PostgreSQL integration.
- Frontend dependencies installed using the official lockfile.
- Two >1MB story WAV blobs are present remotely but the connector returns empty contents for base64 Contents reads and fails UTF-8 Blob reads; remote media/CI verification remains available. No placeholder files have been created.
- Sandbox evaluation is isolated and is evidence about behavior only, not a candidate for wholesale copying.

## Completion policy
Every finding remains OPEN until code, regression evidence, and (where required) integration evidence are recorded. Draft PR #3 documentation is not evidence of implementation correctness. No merge is authorized by this record.
