# STATUS — Himma Platform

**Last updated:** 2026-09-05  
**Repository:** `7eaur/himma-`  
**Branch:** `recovery/ui-media-admin-overhaul`  
**Program:** Full Maintenance / Recovery  
**Current focus:** Phase D — deterministic structured projection; remove active raw-prompt/regex inference from the learning/posttest runtime projection without changing approved academic meaning.

## Phase A — PHASE_A_AUDIO_REVIEW_VERTICAL_SLICE_RECOVERY — CLOSED

**Starting executable HEAD:** `269dcf43e4d8ec1bc9c124a5ef935d6b1c56b1ce`  
**Closed executable candidate:** `6ab969730f99585afa8053e5fece882538c5caaa`

Phase A restored the learner reading contract without weakening academic evidence:

`record -> persist/upload -> supervisor review -> graded or rerecord_required -> continue`

The runtime uses the existing `AudioSubmission.status="uploaded"` value for a recording waiting for supervisor review. Waiting is not success, score, activity completion, or mastery evidence. A valid supervisor grade may satisfy the reading round; `rerecord_required` reopens the same round. No automatic speech score was fabricated.

### Exact-SHA Phase A evidence

All of the following completed successfully on **the same executable SHA** `6ab969730f99585afa8053e5fece882538c5caaa`:

- Himma CI — Quality Gate: run `33954323651` — **SUCCESS**.
  - approved catalog validation
  - Alembic upgrade/downgrade/upgrade
  - Alembic model drift
  - seed idempotency twice
  - backend tests
  - TypeScript, ESLint, frontend unit tests, Next.js production build
  - MinIO/API/Web startup
  - Playwright integration/E2E
- Himma M04 — Responsive Visual Gate: run `33954323671` — **SUCCESS**.
- Himma M09 — Release Readiness Gate: run `33954323649` — **SUCCESS**.

Phase A therefore satisfies the exact-SHA gate rule. The final Playwright fix only scoped duplicate responsive-table evidence locators to the desktop table; it did not weaken product behavior.

## Phase B — PHASE_B_RUNTIME_BYPASS_CLOSURE_AUDIT — CLOSED / NO EXECUTABLE CHANGE REQUIRED

**Audited executable candidate:** `6ab969730f99585afa8053e5fece882538c5caaa`  
**Acceptance focus:** `AC-06`, `AC-07`, `AC-13`, `AC-14`, `AC-15`.

Current-branch audit found no reachable student audio/media completion bypass:

- `/api/runtime-flags` is compatibility-only and always reports `temporary_audio_skip: false`; no environment toggle re-enables it.
- The canonical activity runtime accepts the old `declared_media_gap_skip` field only to reject it fail-closed with HTTP 409; the value is never forwarded as an active skip.
- The lower activity submission layer contains no creation branch for `declared_media_gap_skip`.
- Historical markers `temporary_audio_skip` and `declared_media_gap_skip` remain readable in assessment history only so old records can be interpreted; they are explicitly excluded from correctness/score evidence.
- Current backend regression tests prove pending uploaded audio does not complete/master activity, reviewed audio advances, rerecord reopens the same round, a declared skip is rejected, and missing required audio fails closed without creating an attempt.
- M09 on exact SHA `6ab9697...` passed its explicit step `Verify deleted student audio bypass cannot be reached`.

No code deletion was performed because removing historical compatibility would risk breaking stored academic history, while the active runtime invariant is already fail-closed and gate-protected.

**Migration impact:** none. No learner history was rewritten or deleted.

## Phase C — PHASE_C_APPROVED_AUDIO_BINARY_CONTRACT — CLOSED / NO EXECUTABLE CHANGE REQUIRED

**Audited executable candidate:** `6ab969730f99585afa8053e5fece882538c5caaa`  
**Acceptance focus:** `AC-06`, `AC-07`, `AC-13`, `AC-15`.

Deterministic audio integrity is already enforced by the repository validator and exact-SHA Quality Gate:

- Fixed approved assets: **54**.
- WAV binaries: **54**.
- MP3 binaries: **54**.
- Required static audio missing: **0**.
- `LET-01` retains its stable ID/path and maps to approved **مَ**, sourced from `SYL-15`.
- `SYL-13` = `سَا`.
- `WRD-29` = `موز`.
- `INS-01` = قصة ليان في المزرعة.
- `INS-02` = قصة نادر في الشاطئ.
- `assets/audio/HIMMA_AUDIO_V1/manifest.csv` records the approved identities and SHA-256 checksums for both WAV and MP3 files.
- `packages/content/scripts/validate_catalog.py` invokes the audio manifest verifier; `compile_catalog.verify_audio_manifest_files` checks file existence, exact manifest membership, and SHA-256 integrity.
- The exact-SHA Quality Gate on `6ab9697...` passed `Validate approved content catalog`, so the deterministic file/manifest contract is green.

This closes binary/file integrity. It does **not** claim perceptual listening quality or calibrated speech recognition; those require separate evidence/capability.

**Migration impact:** none.

## Active vertical slice — PHASE_D_DETERMINISTIC_STRUCTURED_PROJECTION

**Starting branch HEAD:** documentation commit after green executable candidate `6ab969730f99585afa8053e5fece882538c5caaa`.  
**Acceptance focus:** `AC-03`, `AC-04`, `AC-05`, `AC-10`, `AC-14`.

### Verified debt

`services/api/seed_learning_posttest_projection_runtime.py` is the active learning/posttest projection owner invoked by `seed_all.py`. It currently uses regex/string parsing of legacy `prompt_text` (`_extract_quoted`, `_single_visible_stimulus`, `_clean_stimulus`) to infer student-visible projection fields. This violates the target structured-source architecture even though the generated runtime currently passes tests.

The repository already provides stronger structured inputs through `template_data.db_runtime`, including stable source metadata, round numbers, persisted step IDs, explicit options/correctness, and media bindings. The projection should consume these structures plus explicit approved overrides instead of interpreting raw prompt prose.

### Phase D implementation plan

1. Remove `re` and all active raw-prompt regex/split inference from `seed_learning_posttest_projection_runtime.py`.
2. Build generic question/instruction/hint behavior from explicit `interaction_type`, structured round data, explicit option/media data, and approved stable-key overrides.
3. Preserve all approved special cases already encoded as explicit stable-key/round overrides; do not infer or invent new academic text.
4. Preserve stable IDs, option IDs, media mappings, correct-answer metadata and seed idempotency.
5. Do not move prompt parsing into frontend/runtime helpers as a workaround.
6. Add a regression proving the active projection no longer depends on prompt parsing for its structured display contract.

### Migration impact

No schema migration expected. The seed remains version-aware/idempotent and must not delete or reset learner history.

### Phase D test plan

- approved catalog validation
- seed twice / idempotency
- projection-specific backend tests including a raw-prompt independence regression
- existing content/runtime contract tests
- full backend suite
- frontend build/tests (projection consumers)
- Playwright integration/E2E
- exact-SHA Quality Gate before Phase D closure

## Planned remaining closure slices

### Phase E — runtime readiness hardening

Audit `/ready` against PostgreSQL, Redis, object storage, expected approved runtime counts/version/projection and required audio contract. Add only missing checks and regression tests.

### Phase F — student-path regression closure

Reconfirm login -> pretest -> supervisor-reviewed readings -> placement -> level activities -> targeted reinforcement -> promotion gates -> posttest, including neutral pre/post feedback, memory interaction behavior, approved L1 auditory content and no retired `path_sequence` runtime fallback.

### Phase G — supervisor audio/admin UX closure

Reconfirm review queue, playback/review state, accept/rerecord transitions, learner waiting state and durable review history. Supervisor remains authoritative until a separately approved calibrated speech model exists.

### Phase H — proven-dead legacy cleanup

Search and remove only proven-dead runtime/UI hacks, including forbidden old enhancers or DOM-state inference. Do not remove historical compatibility required for stored academic records.

### Phase I — final single-candidate closure

Require Quality Gate + M04 + M09 to complete successfully on the same final executable SHA, then record final evidence in ops docs. A documentation-only commit may be distinguished from its executable candidate under repository policy.

## Current runtime truth

- Original approved content: 105 items.
- Runtime total: 125.
- Reinforcement total: 35.
- Skills: 44.
- Target source path: `Approved versioned source -> deterministic structured seed/projection -> PostgreSQL runtime -> structured API -> deterministic renderer`.
- Reports remain descriptive read models and never create mastery evidence.

## Student / architecture

- Unified task design system is active.
- `student-experience.css`, `activity-polish.css`, old DOM enhancers and MutationObserver-based state inference were removed.
- Assessment completion has one canonical owner.
- Activities public routes have one canonical owner.
- `patch_db_runtime()` was removed; auditory-story replacement is projected from its versioned source.
- L1 auditory story replacement maps to `الفهم السمعي المباشر`; old `path_sequence` is not a current canonical runtime interaction.

## Audio / M08

### Fixed prompt/story audio — CLOSED

Authoritative reference: `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`.

### Student recording review — CLOSED BASE CONTRACT / GATE-PROTECTED

Temporary Audio Skip is absent from the active learner path. Current reviewed-learning behavior is gate-protected by backend and E2E coverage.

### Automated speech analysis — OPEN FUTURE GATE

Target: Reference-Guided Arabic Reading Analysis = ASR + reference alignment + C/D/I/S + phonemic helper evidence.

Production automatic speech analysis remains a separately governed future gate for provider integration, calibration, confidence policy, privacy/retention and human override. It is not required to fabricate scoring for the current supervisor-reviewed contract.

## Adaptive contract

- Placement remains starting-level placement only.
- <50% -> L1; 50..<80 -> L2 subject to gates; 80..100 -> L3 subject to gates.
- L1/L2 early promotion: at least 6 Core, mastery >=85, critical floor >=70, required critical coverage, no unresolved reinforcement/review blocker, one-level promotion only.
- Automatic demotion is disabled.
- L3 requires full evidence before journey completion/posttest.
- Reinforcement is targeted only; no random/cross-level fallback.

## Stage status

- M00 Restore Green — CLOSED.
- M01 Placement — CLOSED baseline.
- M02 Adaptation — CLOSED baseline/refined.
- M03 Reinforcement — CLOSED baseline + runtime reconciliation.
- M04 Student Product UI — CLOSED baseline; exact-SHA gate `33954323671` is green on Phase A candidate.
- M05 Supervisor UX — CLOSED baseline.
- M06 Responsive/Accessibility — CLOSED baseline; regressions remain gate-protected.
- M07 Research Reports — CLOSED baseline.
- M08 Fixed audio — CLOSED; automatic speech model integration — OPEN/FUTURE GATE.
- M09 automated release-readiness gate — green on Phase A candidate; final release/UAT closure still requires the final single candidate and explicit release authorization.

## CI rule

Never declare the current branch PASS because an older SHA was green. For every executable closure candidate, inspect current HEAD and require applicable Quality/M04/M09 conclusions for that exact SHA. Documentation-only commits may move HEAD without changing executable code and must be distinguished explicitly.

## Governance

No destructive git, no direct edits to accepted stage branches, no deletion of academic history to make seeds pass, no fabricated media, and no production merge/release without explicit user approval.
