# STATUS — Himma Platform

**Last updated:** 2026-09-05  
**Repository:** `7eaur/himma-`  
**Branch:** `recovery/ui-media-admin-overhaul`  
**Program:** Full Maintenance / Recovery  
**Current focus:** Phase F — student-path regression closure, after exact-SHA green implementation of Phases D and E.

## Current executable evidence

**Latest executable candidate before continuity/docs-only commits:**

`07e83ba57244410f160a727b3c50001fbd7451a1`

All three required gates completed successfully on that exact SHA:

- Himma CI — Quality Gate: run `33958275012` — **SUCCESS**.
- Himma M04 — Responsive Visual Gate: run `33958275097` — **SUCCESS**.
- Himma M09 — Release Readiness Gate: run `33958275085` — **SUCCESS**.

The branch may now contain newer documentation-only commits. Do not confuse documentation HEAD with the last executable candidate; re-fetch HEAD before every write and inspect exact-SHA Actions after executable changes.

## Continuity reference

Authoritative current handoff:

`docs/ops/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-05_AR.md`

It contains the detailed project context, recent commit trail, academic/audio contracts and remaining F -> I execution plan.

---

## Phase A — PHASE_A_AUDIO_REVIEW_VERTICAL_SLICE_RECOVERY — CLOSED

**Starting executable HEAD:** `269dcf43e4d8ec1bc9c124a5ef935d6b1c56b1ce`  
**Closed executable candidate:** `6ab969730f99585afa8053e5fece882538c5caaa`

Restored the learner reading contract:

`record -> persist/upload -> supervisor review -> graded or rerecord_required -> continue`

`AudioSubmission.status="uploaded"` is waiting for supervisor review and is not success, score, activity completion or mastery evidence. `graded` may satisfy the reading round; `rerecord_required` reopens the same round. No fabricated automatic speech score exists.

Exact-SHA Phase A evidence:

- Quality Gate `33954323651` — SUCCESS.
- M04 `33954323671` — SUCCESS.
- M09 `33954323649` — SUCCESS.

---

## Phase B — PHASE_B_RUNTIME_BYPASS_CLOSURE_AUDIT — CLOSED

No reachable learner audio/media completion bypass remains.

- `/api/runtime-flags` is compatibility-only and always reports `temporary_audio_skip: false`.
- `declared_media_gap_skip` is fail-closed and cannot manufacture completion evidence.
- Historical markers remain readable only for old records and are excluded from score/mastery evidence.
- Pending uploaded audio cannot complete/master an activity.
- Missing required media fails closed.

No destructive migration or learner-history rewrite was performed.

---

## Phase C — PHASE_C_APPROVED_AUDIO_BINARY_CONTRACT — CLOSED

Deterministic static audio contract:

- Approved assets: **54**.
- WAV binaries: **54**.
- MP3 binaries: **54**.
- Required static audio missing: **0**.
- `LET-01` = approved **مَ** bytes sourced from `SYL-15` while retaining stable runtime ID/path.
- `SYL-13` = `سَا`.
- `WRD-29` = `موز`.
- `INS-01` = قصة ليان في المزرعة.
- `INS-02` = قصة نادر في الشاطئ.

`assets/audio/HIMMA_AUDIO_V1/manifest.csv` plus the catalog validator enforce existence/membership/checksum integrity. This does not claim perceptual listening quality or calibrated ASR quality.

Authoritative contract:

`docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`

---

## Phase D — PHASE_D_DETERMINISTIC_STRUCTURED_PROJECTION — CLOSED

Main implementation:

`30356bdb2301cf213e9ff257470730693900ceaa`

`refactor(content): make learning projection structured and deterministic`

Regression lock:

`62136541e7f8fdef0464d9535c7cc1876dae3b48`

`test(content): lock structured learning projection contract`

Outcome:

- Active projection no longer imports/uses `re` to parse legacy prompts.
- Active projection no longer depends on `step.prompt_text` for learner-visible structured fields.
- Removed active `_extract_quoted`, `_single_visible_stimulus`, `_strip_serialized_choices`, `_clean_stimulus` style inference.
- Projection contract is `structured_db_runtime_v1`.
- Structured DB runtime + explicit approved/source-derived overrides drive the student projection.
- Stable IDs, option IDs, media mappings and correctness metadata are preserved.
- Regression tests prove answers are not leaked into learner stimuli/question text and lock important approved content including `L1-CORE-06`.

No schema migration was required; seed remains idempotent/non-destructive.

Phase D is covered by the current exact-SHA green candidate `07e83...`.

---

## Phase E — PHASE_E_RUNTIME_READINESS_HARDENING — CLOSED

Implementation:

`ba8940cff873a1982389a61715cdb5e8b864ff1c`

`feat(readiness): enforce exact content and approved audio contracts`

Tests:

`4e495cbddf9dcfa84fd6caee39a844394bb902f0`

`test(readiness): cover exact projection and approved audio gates`

Version correction:

`1ee0c939eac20b4b9aa2236958010ebbb53c1928`

`fix(readiness): match active structured learning projection version`

`/ready` now fails closed on the deployment/runtime contract rather than only checking that services answer. It checks:

- config
- PostgreSQL
- Redis
- object storage
- exact approved runtime counts
- exact pretest/learning/posttest experience versions
- learning rounds count against persisted DB steps
- the required corrective approved audio assets and their WAV/MP3 presence

Expected runtime counts:

- pretest = 30
- learning = 65
- posttest = 30

The student runtime remains DB-driven; readiness does not replace DB content loading with filesystem content loading.

Phase E is covered by the current exact-SHA green candidate `07e83...`.

---

## Additional hardening after Phase E

Current executable HEAD includes:

`07e83ba57244410f160a727b3c50001fbd7451a1`

`test(reports): prove report reads cannot mutate academic state`

This regression proves report reads do not mutate academic state. It is important hardening but does not itself close Phase F/G/H.

---

## Active Phase F — Student Path Regression Closure

Reconfirm the complete learner journey:

`login -> pretest -> reviewed audio -> placement -> level activities -> targeted reinforcement -> promotion gates -> L3 completion -> posttest`

Required coverage includes:

- 30-question pretest and 30-question posttest.
- Neutral pre/post assessment feedback: no revealing correct/wrong, answer-revealing hints or retry behavior.
- PRE-Q03 target `م`, other form `مـ`.
- POST-Q14 = `نَخْلَة`.
- Assessment uploaded audio remains blocked pending review; re-audit navigation helpers so pending audio is not accidentally treated as answered before review.
- Placement thresholds remain <50 L1, 50..<80 L2, 80..100 L3 subject to gates.
- L1/L2 promotion requires >=6 core, mastery >=85, critical floor >=70, required critical coverage, no unresolved reinforcement/review blocker, one-level promotion only.
- No automatic demotion.
- L3 requires full evidence before journey completion/posttest.
- Reinforcement is targeted only; no random/cross-level fallback.
- Memory interactions show images first, no timer auto-hide, learner presses `التالي`, then recall/reorder.
- `L1-CORE-06` approved onset-pair contract remains exact; موز uses `WRD-29`.
- `L1-CORE-09` uses `INS-01` (ليان) with skill `الفهم السمعي المباشر`.
- `L1-REIN-11` uses `INS-02` (نادر) with the same skill.
- No retired `path_sequence` runtime fallback.
- Retakes use canonical assessment completion, preserve old attempts, and maintain exactly one `official_for_reporting`.

Add only missing regression/E2E coverage; do not change academic meaning merely to make tests green.

---

## Planned Phase G — Supervisor Audio/Admin UX Closure

Reconfirm:

- pending queue uses `AudioSubmission.status="uploaded"`.
- playback/review state works.
- accept vs `rerecord_required` transitions are explicit.
- learner waiting/rerecord state survives reload/resume.
- supervisor remains the grading authority.
- no fake/hidden automatic score.
- review/audit history is durable and never deleted to simplify retries.
- a reviewed valid recording resumes the canonical learner path without manual DB repair.

If current implementation already proves these invariants, close without unnecessary churn.

---

## Planned Phase H — Proven-Dead Legacy Cleanup

Search/classify active runtime vs historical compatibility vs docs/tests vs dead code for:

- `temporary_audio_skip`
- `TemporaryAudioSkip`
- `TEMP_AUDIO_SKIP`
- `HIMMA_TEMP_AUDIO_SKIP`
- `skip_recording`
- `temporary-audio`
- `runtime-flags`
- `declared_media_gap_skip`
- `AssessmentExperienceEnhancer`
- `AssessmentLetterStimulusPreviewFix`
- `MutationObserver`
- `querySelector`
- `innerText`
- portal/runtime DOM injection
- hashed-class CSS patches
- repeated `!important` patch architecture

Delete only proven-dead runtime/UI code. Preserve compatibility needed to interpret stored academic history.

The native frontend standard remains React components + CSS modules/design tokens + explicit state; no DOM-state inference.

---

## Planned Phase I — Final Single-Candidate Closure

After F/G/H, select one final executable SHA and require all of the following on that exact SHA:

- approved catalog validation
- audio manifest/binary validation
- Alembic upgrade/downgrade/upgrade
- model drift
- seed idempotency twice
- full backend tests
- TypeScript
- ESLint
- frontend unit tests
- Next production build
- MinIO/API/Web integration startup
- Playwright E2E
- M04
- M09

Then update STATUS/progress/decision evidence with final run IDs and final executable SHA.

No production merge/release without explicit user authorization.

---

## Runtime truth

- Original approved content: 105 items.
- Runtime total: 125.
- Reinforcement total: 35.
- Skills: 44.
- Architecture: `approved_versioned_source -> deterministic_structured_projection -> postgres_runtime -> structured_api -> deterministic_renderer`.
- Reports are descriptive read models and never create mastery evidence.
- Seeds are version-aware, idempotent and non-destructive.

## Student / architecture

- Unified task design system is active.
- Old `student-experience.css`, `activity-polish.css`, DOM enhancers and MutationObserver-based state inference were removed.
- Assessment completion has one canonical owner.
- Public activities have one canonical owner.
- `patch_db_runtime()` is removed.
- L1 auditory story replacement is projected from versioned source.

## Audio / M08

- Fixed prompt/story audio — CLOSED.
- Student recording supervisor-review base contract — CLOSED/GATE-PROTECTED.
- Automated speech analysis — OPEN FUTURE GATE only.

Target future architecture if separately approved:

`Reference-Guided Arabic Reading Analysis = ASR + reference alignment + C/D/I/S + phonemic helper evidence`

Do not fabricate automatic scores for the current release.

## Stage status

- M00 Restore Green — CLOSED.
- M01 Placement — CLOSED baseline.
- M02 Adaptation — CLOSED baseline/refined.
- M03 Reinforcement — CLOSED/reconciled.
- M04 Student Product UI — CLOSED baseline; current exact-SHA gate is green on `07e83...`.
- M05 Supervisor UX — CLOSED baseline; Phase G is a final regression/closure audit.
- M06 Responsive/Accessibility — CLOSED baseline; M04 gate remains protective.
- M07 Research Reports — CLOSED baseline + non-mutation regression on `07e83...`.
- M08 Fixed audio — CLOSED; automatic speech analysis remains future.
- M09 automated release-readiness gate — green on `07e83...`; final release still requires final single candidate + explicit authorization.

## CI rule

Never declare the current branch PASS because an older SHA was green. For every executable closure candidate, require Quality/M04/M09 conclusions for that exact SHA. Documentation-only commits may move HEAD and must be distinguished from the executable candidate.

## Governance

No Docker locally, no destructive git, no direct modification of accepted stage branches, no deletion/reset of academic history, no fabricated media or scoring, and no production merge/release without explicit user approval.
