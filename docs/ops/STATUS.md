# STATUS — Himma Platform

**Last updated:** 2026-09-05  
**Repository:** `7eaur/himma-`  
**Branch:** `recovery/ui-media-admin-overhaul`  
**Program:** Full Maintenance / Recovery  
**Current focus:** Phase A — recover the learner recording/review vertical slice and restore the exact-SHA Quality Gate without weakening academic evidence rules.

## Active vertical slice — PHASE_A_AUDIO_REVIEW_VERTICAL_SLICE_RECOVERY

**Starting executable HEAD:** `269dcf43e4d8ec1bc9c124a5ef935d6b1c56b1ce`.

**Affected acceptance IDs:** `AC-STD-009`, `AC-ADM-008`, `AC-IMP-004`, `AC-IMP-005`, `AC-IMP-006`, `AC-REL-002`, `AC-REL-007`, `AC-AUD-003`.

### Verified failure/root cause before coding

The current Quality Gate is red in the Playwright vertical slice. The learner UI records and uploads a reading blob, then posts the returned audio metadata to the canonical learning activity submit endpoint. That endpoint currently rejects `read_aloud` / `timed_read_aloud` interactions instead of persisting the recording for supervisor review. In addition, the current activity step-state treats any non-`rerecord_required` `AudioSubmission` as step completion, so a future `pending` recording would incorrectly become completion evidence.

This is a frontend/backend runtime-contract mismatch, not a reason to restore an audio skip or to fake an automatic score.

### Phase A plan

1. Extend the canonical learning activity submission contract to accept validated persisted-audio metadata for reading interactions and create a `pending` `AudioSubmission` with no automatic correctness score.
2. Make audio step-state explicit: `pending` = waiting and **not complete**; `graded` = supervisor decision may satisfy the step; `rerecord_required` = reopen for a new recording.
3. Keep the attempt/session/mastery path blocked while review is pending; do not manufacture success/evidence.
4. Update the native learner renderer to show the pending-review state explicitly rather than trying to advance through it.
5. Add/adjust regression coverage for pending -> supervisor decision -> continue, and for rerecord.
6. Run targeted backend/frontend tests first, then the full Quality Gate. Phase A is not closed until the applicable gate is green on the exact final executable candidate.

### Migration impact

**None expected.** Phase A reuses the existing `AttemptResponse` and `AudioSubmission` schema and supervisor-review authority. No destructive migration, reset, reseed of learner history, or data deletion is planned.

### Test plan

- Backend: learning reading submission persists a `pending` `AudioSubmission`; pending is not attempt/activity completion; valid supervisor grading unlocks progression; invalid review reopens rerecord.
- Frontend: recording submission renders a deterministic waiting-for-supervisor state and does not expose a bypass.
- E2E: learner recording -> pending review -> supervisor decision -> academic continuation.
- Final: full Himma CI Quality Gate on the exact final executable SHA.

## Current runtime truth

- Original approved content: 105 items.
- Runtime total: 125.
- Reinforcement total: 35.
- Skills: 44.
- Source path: `Approved versioned source -> deterministic seed/projection -> PostgreSQL runtime -> structured API -> deterministic renderer`.
- Reports remain descriptive and never create mastery evidence.

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
- `LET-01` now contains the approved **مَ** recording sourced from `SYL-15`, while retaining the stable runtime ID/path.
- `WRD-29` = `موز`.
- `SYL-13` = `سَا`.
- `INS-01` = قصة ليان في المزرعة.
- `INS-02` = قصة نادر في الشاطئ.
- The ten changed/new WAV/MP3 binaries were verified as physically present in GitHub and content-matched to the approved payload by file size and Git blob SHA; SHA-256 evidence is recorded in the authoritative audio contract.

Authoritative reference:
`docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`.

### Student recording review — ACTIVE

Temporary Audio Skip is fully removed from UI, styles, API router, feature flag and backend module. It cannot be restored by an environment variable.

Until the approved automatic speech model is integrated, student recordings follow:

`record -> persist/upload -> supervisor review -> accepted or rerecord required -> continue`

Supervisor review is authoritative. Waiting for review is not success, score or mastery evidence.

### Automated speech analysis — OPEN FUTURE GATE

Target: Reference-Guided Arabic Reading Analysis = ASR + reference alignment + C/D/I/S + phonemic helper evidence.

M08 as **production automatic speech analysis** remains open for provider selection/integration, calibration, confidence policy, privacy/retention and governed human override. This is no longer a static-audio gap.

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
- M04 Student Product UI — CLOSED baseline; current branch still requires exact-SHA visual evidence after relevant changes.
- M05 Supervisor UX — CLOSED baseline.
- M06 Responsive/Accessibility — CLOSED baseline; regressions remain gate-protected.
- M07 Research Reports — CLOSED baseline.
- M08 Fixed audio — CLOSED; automatic speech model integration — OPEN/FUTURE GATE.
- M09 Release/UAT — IN PROGRESS; no production launch is authorized by this status.

## CI rule

Never declare the current branch PASS because an older SHA was green. For the final candidate, inspect current HEAD and require applicable Quality/M04/M09 conclusions for that exact code candidate. Documentation-only commits may move HEAD without changing executable code and must be distinguished accordingly.

## Remaining work

1. Complete Phase A learner-recording/review contract recovery and restore the Quality Gate on the exact candidate.
2. Confirm M04 on the relevant UI candidate and inspect its artifact where authenticated views are covered.
3. Confirm M09 readiness on the current executable candidate.
4. Complete remaining M09 full single-candidate UAT, monitoring/support, rollback and privacy/retention acceptance.
5. Integrate/calibrate the future speech model only under a separately approved M08 plan.

## Governance

No destructive git, no direct edits to accepted stage branches, no deletion of academic history to make seeds pass, no fabricated media, no production merge/release without explicit user approval.
