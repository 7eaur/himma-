# STATUS — Himma Platform

**Last updated:** 2026-09-05  
**Repository:** `7eaur/himma-`  
**Branch:** `recovery/ui-media-admin-overhaul`  
**Program:** Full Maintenance / Recovery  
**Current focus:** Phase B → I corrective closure, beginning with a fail-closed audit of every remaining student-audio bypass/runtime compatibility path before touching projection/readiness debt.

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

## Active vertical slice — PHASE_B_RUNTIME_BYPASS_CLOSURE_AUDIT

**Starting executable HEAD:** `6ab969730f99585afa8053e5fece882538c5caaa`.

**Acceptance focus:** `AC-06`, `AC-07`, `AC-13`, `AC-14`, `AC-15`.

### Phase B plan

1. Re-audit the current target branch for all active and compatibility references to:
   `temporary_audio_skip`, `TemporaryAudioSkip`, `TEMP_AUDIO_SKIP`, `HIMMA_TEMP_AUDIO_SKIP`, `skip_recording`, `temporary-audio`, `runtime-flags`, and `declared_media_gap_skip`.
2. Classify every hit as active runtime, historical-data compatibility, docs, test, or dead code.
3. Require fail-closed behavior: no public/student request may manufacture a completed/correct attempt because media is missing or a recording is skipped.
4. Preserve historical attempt/assessment records and compatibility markers required to read old data; do not delete learner history.
5. Add or refine negative regression coverage only where the current suite does not already prove the invariant.
6. If the active bypass is already absent and the current M09/Quality tests prove it, close Phase B without unnecessary code churn.

### Migration impact

**None planned.** Historical records must remain readable. No destructive migration, reset, reseed of learner history, or data deletion is permitted.

### Phase B test plan

- Student/public activity submission schema contains no skip control.
- Missing required media fails closed rather than creating completion evidence.
- Uploaded/pending review audio cannot count as completion/mastery.
- Historical skip markers, where still readable for old data, are excluded from score/mastery and are not reachable as a current student action.
- Exact-SHA Quality Gate + M09 after any executable Phase B change.

## Planned remaining closure slices

### Phase C — approved audio binary/runtime contract

Verify manifest, committed WAV/MP3 pairs, runtime references and validator coverage for all approved fixed audio, including `LET-01`, `SYL-13`, `WRD-29`, `INS-01`, and `INS-02`. Deterministic file/manifest integrity may be asserted; perceptual waveform quality is not claimed without a listening-capable evidence step.

### Phase D — deterministic structured projection

Remove raw prompt/regex/string inference from `seed_learning_posttest_projection_runtime.py` and any equivalent active projection path. Approved structured source fields must drive the runtime projection while preserving stable IDs and approved content.

### Phase E — runtime readiness hardening

Audit `/ready` against PostgreSQL, Redis, object storage, expected approved runtime counts/version/projection and required audio contract. Add only missing checks and regression tests.

### Phase F — student-path regression closure

Reconfirm login -> pretest -> supervisor-reviewed readings -> placement -> level activities -> targeted reinforcement -> promotion gates -> posttest, including neutral pre/post feedback, memory interaction behavior, approved L1 auditory content and no retired `path_sequence` runtime fallback.

### Phase G — supervisor audio/admin UX closure

Reconfirm review queue, playback/review state, accept/rerecord transitions, learner waiting state and durable review history. Supervisor remains authoritative until a separately approved calibrated speech model exists.

### Phase H — proven-dead legacy cleanup

Search and remove only proven-dead runtime/UI hacks, including forbidden old enhancers or DOM-state inference. Do not remove historical compatibility required for stored academic records.

### Phase I — final single-candidate closure

Require Quality Gate + M04 + M09 to complete successfully on the same final executable SHA, then record the final evidence in ops docs. A documentation-only commit may be distinguished from its executable candidate under the repository policy.

## Current runtime truth

- Original approved content: 105 items.
- Runtime total: 125.
- Reinforcement total: 35.
- Skills: 44.
- Source path: `Approved versioned source -> deterministic seed/projection -> PostgreSQL runtime -> structured API -> deterministic renderer`.
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

- Approved fixed assets: **54**.
- WAV binaries: **54**.
- MP3 binaries: **54**.
- Missing required static audio: **0**.
- `LET-01` contains the approved **مَ** recording sourced from `SYL-15`, while retaining the stable runtime ID/path.
- `WRD-29` = `موز`.
- `SYL-13` = `سَا`.
- `INS-01` = قصة ليان في المزرعة.
- `INS-02` = قصة نادر في الشاطئ.

Authoritative reference: `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`.

### Student recording review — CLOSED BASE CONTRACT / GATE-PROTECTED

Temporary Audio Skip has been removed from the active learner path. Current reviewed-learning behavior is gate-protected by backend and E2E coverage. Phase B is a fresh current-branch closure audit to ensure no alternative runtime bypass remains.

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

Never declare the current branch PASS because an older SHA was green. For every executable closure candidate, inspect current HEAD and require the applicable Quality/M04/M09 conclusions for that exact SHA. Documentation-only commits may move HEAD without changing executable code and must be distinguished explicitly.

## Governance

No destructive git, no direct edits to accepted stage branches, no deletion of academic history to make seeds pass, no fabricated media, and no production merge/release without explicit user approval.
