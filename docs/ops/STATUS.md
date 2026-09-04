# STATUS — Himma Platform

**Last updated:** 2026-09-04  
**Repository:** `7eaur/himma-`  
**Branch:** `recovery/ui-media-admin-overhaul`  
**Program:** Full Maintenance / Recovery  
**Current focus:** final CI/UAT verification after architecture, UI and approved-audio reconciliation.

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

1. Obtain/confirm current Quality Gate after the approved binaries and latest E2E fixes.
2. Confirm M04 on the relevant UI candidate and inspect its artifact where authenticated views are covered.
3. Confirm M09 readiness on the current executable candidate.
4. Complete remaining M09 full single-candidate UAT, monitoring/support, rollback and privacy/retention acceptance.
5. Integrate/calibrate the future speech model only under a separately approved M08 plan.

## Governance

No destructive git, no direct edits to accepted stage branches, no deletion of academic history to make seeds pass, no fabricated media, no production merge/release without explicit user approval.
