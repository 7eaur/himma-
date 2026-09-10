# STATUS — Himma Platform

**Last updated:** 2026-09-10  
**Repository:** `7eaur/himma-`  
**Active branch:** `audit/comprehensive-repository-review-2026-09-10`  
**Current state:** `A00–A09 AUDIT CLOSED — A10/W1 IN PROGRESS — NO MERGE / NO DEPLOY`  

> هذا الملف يعكس نقطة التنفيذ الحالية. أي أقسام Recovery/Integration أقدم هي أدلة تاريخية فقط وليست HEAD أو release candidate حاليًا.

## Current continuity source

المرجع الأول للمحادثات الجديدة:

`docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-10_A10_W1_FULL_AR.md`

Checkpoint التنفيذ الحالي:

`docs/maintenance/HIMMA_A10_W1_EXECUTION_CHECKPOINT_2026-09-10_AR.md`

Master gaps:

`docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`

## Current code checkpoint

آخر code-bearing checkpoint قبل commits التوثيق:

`ead44bf492cdbea35b65dc9ddce54fe7de4a20ef`

لا يُفترض أنه HEAD الحالي بعد commits التوثيق؛ يجب جلب HEAD قبل أي تنفيذ جديد.

## Audit status

A00–A09 مغلقة كتدقيق:

- A00 Baseline / CI — CLOSED AUDIT.
- A01 Backend ownership — CLOSED AUDIT.
- A02 Seeds / migrations / legacy — CLOSED AUDIT.
- A03 Audio / Speech / Review / Adaptation — CLOSED AUDIT.
- A04 Admin / Student Details / Mobile — CLOSED AUDIT.
- A05 Rewards / Badges — CLOSED AUDIT.
- A06 Images / Media — CLOSED AUDIT.
- A07 Security / Performance / Accessibility / Observability — CLOSED AUDIT.
- A08 Full Journey / Integration / E2E — CLOSED AUDIT.
- A09 All Branches — CLOSED AUDIT.
- Master Gap Register — COMPLETE.

لا تعاد هذه المراحل من الصفر.

## A10 / W1 — work completed so far

W1 = Academic / History Integrity.

تم تنفيذ:

- `8f5e3aa6d736faee579924f7a813d0e033879cac` — centralized latest AudioSubmission/latest AudioReview helpers.
- `6a877335bf51f575450f199767321fdced3fdd14` — human review preserves history; invalid review no longer auto-reopens Attempt; historical submission cannot become active review.
- `b114d8618b94db01cff0bcd99303fe3de4449619` — assessment completion/scoring reads latest audio state/review.
- `00926e115840799c689375008e8f66744fa2b41d` — assessment rerecord is append-only and requires explicit learner open.
- `ead44bf492cdbea35b65dc9ddce54fe7de4a20ef` — added canonical `level_completion.py` owner.

## A10 / W1 — still open

- Wire `level_completion.py` into Journey/Rewards/relevant completion consumers.
- Fix numeric `AudioReview.rubric_score` evidence in adaptation; do not Boolean-collapse 0.10 and 1.00.
- Fix `AUD-BE-003`: pending review aggregate must remain correct when a sibling step is actionable.
- Make profile/protected assessment state latest-submission only.
- Update assessment frontend for deferred explicit rerecord task flow.
- Add regression tests for all W1 boundaries.
- Run targeted and relevant full gates and record exact SHA.

**There is no new Green exact-SHA claim for A10 yet.**

## Active academic contract

### Initial placement

- `<50%` → L1.
- `50%..<80%` → L2.
- `80%..100%` → L3.

### Learning / Adaptation V4

- Activity `>=80` → pass.
- `70..<80` → guided retry.
- `<70` → targeted reinforcement.
- L1/L2 early promotion: >=6 Core + mastery >=85 + critical coverage + critical floor >=70 + no unresolved reinforcement/supervisor/audio blocker at irreversible boundary.
- one-level promotion only.
- no automatic demotion.
- L3 completion requires all 10 Core.
- newest 3 valid active-session evidences weighted 50/30/20.

## Canonical content/runtime contract

- Runtime total: **125**.
- Pretest: 30.
- Posttest: 30.
- Learning runtime: 65.
- Reinforcement: 35.
- Skills: 44.
- Projection contract: `structured_db_runtime_v1`.
- Architecture: `approved_versioned_source -> deterministic_structured_projection -> postgres_runtime -> structured_api -> deterministic_renderer`.

Do not revert to the historical 105-item runtime world.

## Audio contract

Static approved audio:

- Approved IDs: 54.
- WAV: 54.
- MP3: 54.
- Required static audio gaps: 0.

Student audio authority:

`record -> persist/upload -> supervisor review -> graded / rerecord_required -> explicit rerecord when required`

- uploaded/pending = neutral academic state.
- unresolved learning audio does not block same-level navigation/support.
- irreversible promotion/L3 completion waits on unresolved audio.
- assessment may wait for human review before the next assessment item under the current contract.
- rerecord is deferred until explicit learner open.
- rerecord is append-only; old submissions remain immutable history.
- latest AudioSubmission is active state.
- graded only may become academic evidence.
- human supervisor review is currently authoritative.

Production ASR is **not approved**. Speech Lab branches remain research-only and excluded from merge.

## Branch governance

A09 compared 20 branches.

- historical B/Stage/recovery/integration branches are already contained or obsolete for current work; no blind merge.
- Speech/Pronunciation Lab branches: EXCLUDE FROM MERGE until independent ASR approval.
- `deployment/platform-sandbox`: reference only; no Docker/Temporary Audio Skip revival.

## Baseline CI evidence before A10

Reference run `34419490966` on `7cb2192b0c31bc85dcf98a470023e9cc6f1598e0`:

- Security PASS.
- Frontend PASS.
- canonical validation PASS.
- Alembic up/down/up PASS.
- drift PASS.
- canonical seed idempotency PASS.
- Backend: 823 passed / 2 failed / 825.
- Integration skipped because Backend gate failed.

This is baseline evidence only, not a PASS for current A10 code.

Historical Recovery exact-SHA evidence `976b7c2ed8b9c6f1535a22a0b3a94b2c233f75eb` and runs `33979846641/639/640` remain archived evidence for the 2026-09-05 recovery state only; they do not authorize the current branch.

## Remaining external / production gates

Still unresolved before real production where applicable:

- Production ASR provider/calibration/privacy/cost/governance if automatic speech decisions are pursued.
- intervention/session duration decision before study activation.
- child-recording retention policy before real-child production data.
- domain/hosting/deployment settings.
- supervising organization details/logo for final reporting.
- credential rotation before production/deployment if any historical real credentials were exposed.

## Execution boundary

No Merge, Release, Deploy, Railway finalization or Docker use is authorized at this state.

Next action: continue **A10/W1** from the full handoff, close it with real regression evidence, then move to W2 according to the Master Gap Register.