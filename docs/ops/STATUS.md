# STATUS — Himma Platform

**Current branch:** `recovery/ui-media-admin-overhaul`

**Current corrective slice:** UI / Media / Supervisor / Student Recovery — `READY_FOR_CLOSURE_GATE`

**Recovery implementation checkpoint:** `7dbc52bcc70a5768c81cd04065be00f1949c429d`

**Recovery evidence run:** GitHub Actions #171 — `32928214424` — backend/frontend/integration all successful.

**Underlying roadmap stage:** Stage 4 / P07 Speech Analysis — `IN_PROGRESS / EXTERNALLY BLOCKED`

**Last accepted roadmap stage:** Stage 3 / B03 at implementation SHA `8d64eb9766fd69618960af0b279ae94484618d17`

**Last verified:** 2026-08-26

---

## Corrective recovery completed

The recovery branch was cut from the existing P07 infrastructure state without changing the accepted Stage-2 or Stage-3 branches. The objective was to repair the real product experience and missing runtime semantics before continuing speech-provider work.

### Student experience

- Rebuilt the child-facing landing page and student journey dashboard using the approved Himma identity and static approved character assets.
- Restored canonical interaction semantics from the approved 105-item catalog instead of flattening activities into generic multiple-choice buttons.
- Assessment and learning runtime now support image choice, listen+image, choose-many, sequence/path/memory sequence, build-word and read-aloud/timed-read-aloud interaction families.
- Approved education images/audio are served from the real asset package; media routing is regression-tested with real bytes.
- Reading tasks provide recording/re-record/send states without claiming calibrated automatic pronunciation scoring.
- Declared source media gaps remain explicit and academically neutral; no invented audio is substituted.
- Adaptive reinforcement gaps now produce a calm student hold state and resume after a documented supervisor assignment.

### Supervisor experience

- `/admin` is protected and unauthenticated users are redirected to login before dashboard data is rendered.
- Product-facing terminology uses **المشرف**; the legacy internal role value `researcher` remains only for schema/JWT/API compatibility.
- Supervisor settings support username update, password change, listing supervisors and creating an additional supervisor.
- Student creation supports secure auto-generated six-digit numeric codes or manual six-digit codes.
- Student management supports name/status edits, access-code change/regeneration, adaptation override, post-test gate and reinforcement resolution.
- Reinforcement resolution exposes only approved unused same-level reinforcement activities, requires a written reason, and records audit evidence.
- Dashboard, audio review and reports are wired into the tested end-to-end path.

### Quality evidence

GitHub Actions #171 (`32928214424`) passed:

- frontend TypeScript, ESLint, unit tests and production Next.js build;
- backend approved catalog validation, reversible migrations/drift check, idempotent seed and backend tests;
- integration PostgreSQL + Redis + pinned/checksummed MinIO + FastAPI + Next.js + Chromium;
- Playwright full journey from public page through supervisor/student lifecycle, 30-item pre-test, real image media, recording/manual audio review, adaptive learning, reinforcement review/resume and live reports.

The Playwright artifact contains 17 screenshots, including real image-choice media, reading/recording UI, adaptive hold, supervisor reinforcement assignment and resumed student reinforcement.

## P07 speech analysis remains NOT accepted

The recovery work does **not** resolve the real-ASR external gates. The following remain blocked until representative recordings/provider decisions are supplied:

- production ASR provider selection and approval;
- privacy/retention/cost/recording-transfer decision;
- representative Arabic child-reading accuracy evaluation;
- calibrated confidence threshold/version;
- real provider adapter through private storage → worker → ASR → alignment;
- any phoneme/haraka automatic scoring claim not proven by calibration.

Manual supervisor audio review remains authoritative. No fake production ASR fallback is enabled.

## Preserved accepted checkpoints

- B00: `recovery/codex-baseline@e5fafe757bd57f8bdce35a8f8d0f3bbcc0784c2d`
- B01: `b01/content-source-of-truth@26d25e081b0c7c66f5d6b09b8b1750e67c745b41`
- B02 lifecycle: `b02/student-assessment-lifecycle@6a5293879fb25555dc2992ee0cf2b6f7c7441afa`
- Stage 2 closure: `b02/stage2-closure@38a1b8d1a03a56f08aa3afdf9404593351e05a87`
- Stage 3 / B03: `b03/adaptive-learning-engine@8d64eb9766fd69618960af0b279ae94484618d17`

## Next action

Run the final closure gate on the documentation head of this recovery branch. After recovery closure, resume P07 only when the external provider/recording/calibration inputs are available; do not represent P07 as accepted before those gates are satisfied.
