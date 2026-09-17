# RESUME HERE — Himma UX System Rebuild

**Last updated:** 2026-09-17  
**Repository:** `7eaur/himma-`  
**Official branch:** `stage/02-content`  
**Active branch:** `fix/ux-system-rebuild-2026-09-17`

## Read first

1. `docs/ops/HIMMA_UX_SYSTEM_REBUILD_HANDOFF_2026-09-17_AR.md`
2. `docs/ops/STATUS.md`
3. `docs/ops/UX_SYSTEM_REBUILD_2026-09-17_AR.md`
4. `docs/ops/UX_SYSTEM_REBUILD_PROGRESS_2026-09-17_AR.md`
5. `docs/ops/progress.json`
6. `docs/ops/UX_AUDIO_REVIEW_CORRECTIONS_2026-09-17_AR.md`
7. `docs/specs/SOURCE_OF_TRUTH.md`

Always fetch live HEADs first. Do not assume the SHAs below remain current if newer commits exist.

## Official Production baseline

Official branch baseline:

`765c42d769624ad13683798f68177f6597f2149f`

Verified release evidence:

- Integration QG #911 / Run `35241996615`: SUCCESS.
- M09 #215 / Run `35241996654`: SUCCESS.
- Official QG #912 / Run `35243714139`: SUCCESS.
- Railway was verified on the same official SHA at the baseline checkpoint.
- `/api/health` and `/api/ready` were 200.
- Canonical runtime: 125 items / 44 skills.

## Current UX candidate

Latest exact functional SHA tested before documentation-only commits:

`09be49102d1aab8f09cf1a3267ccd073c46c7397`

Quality Gate #917 / Run `35261495545`: SUCCESS.

- Security: SUCCESS.
- Frontend: SUCCESS.
- Backend: SUCCESS.
- Integration: SUCCESS.
- Playwright report artifact ID: `10515801114`.

The active branch is ahead of the official baseline and **has not been merged or deployed** for this UX batch.

## What the owner asked to fix from latest screenshots

The work is intentionally split into five batches:

- **A — Student Question System:** responsive text/stimulus container, mobile question title, image choices, image ordering/sequence, preserve robust audio switching.
- **B — Student Dashboard & Journey:** rebuild hierarchy so it reads as a real learning journey, not conflicting equal-weight cards.
- **C — Admin Audio Review:** compact queue, balanced buttons, decision-first approval/rerecord form, remove excessive empty space.
- **D — Admin Dashboard & Notifications:** aggregate pending recordings on dashboard; individual events stay in Review/Notifications.
- **E — Remaining Admin UX:** student profile mobile tabs/layout, Add Student, Content Preview fidelity, transient Toast behavior.

## Current implementation state

- Shared `question-system.css` exists and is loaded for student routes.
- Shared `dashboard-system.css` exists and reorders Student Dashboard hierarchy.
- Shared `admin-workflow.css` exists and is loaded by Admin Dashboard layout.
- Shared `AdminFeedbackToast` implements auto-dismiss, click/pointer dismiss and explicit close.
- Admin Dashboard aggregates pending audio instead of repeating each recording card.
- Student Profile responsive CSS has been tightened for narrow screens.
- Add Student now exposes the real server-generated access code after creation rather than a fake preview.
- Content Preview has real Assessment/Learning payload rendering and the new visual-density hooks.
- Responsive Playwright coverage captures student home + assessment from 320px through desktop.

## Audio contract — do not regress

- Pending audio submission does not block remaining unanswered assessment questions.
- Academic finalization is blocked until required Human Supervisor Review completes.
- Rerecord is an explicit task and does not automatically hijack the learner's current question/activity.
- Previous recording evidence stays historical.
- No fake ASR / no Student Audio Skip / no Temporary Audio Skip.

## Next action — this is where the next conversation continues

1. Fetch live `stage/02-content` and `fix/ux-system-rebuild-2026-09-17` HEADs.
2. Confirm the latest tested functional SHA/evidence and identify any docs-only descendants.
3. Review Playwright artifact/screenshots visually against the owner screenshots and A–E contracts.
4. If a visual issue remains, fix Root Cause on the UX branch and rerun exact-head Quality Gate.
5. Run M09 Release Readiness on the final UX functional SHA.
6. Only after Visual QA + QG + M09 are green, merge/fast-forward to `stage/02-content`.
7. Verify official exact-head CI, deploy Railway, and run Production QA.
8. Update final release/closure evidence. Do not claim CLOSED before that.

## Still open / deferred

- Visual QA for the current UX candidate.
- M09 for the final UX candidate.
- UX branch merge/deployment/Production QA.
- Production ASR provider approval remains external/deferred.
- Manual human screen-reader verification remains not claimed.
