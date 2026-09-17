# STATUS — Himma Platform

**Last updated:** 2026-09-17  
**Repository:** `7eaur/himma-`  
**Official branch:** `stage/02-content`  
**Active UX branch:** `fix/ux-system-rebuild-2026-09-17`

## Current state

The previous W1–W6 audit/release sequence is closed. The platform has since been merged and deployed to Railway, and a new UX-system rebuild is now active on a separate branch.

### Official / Production baseline

Official branch SHA currently verified before this UX batch:

`765c42d769624ad13683798f68177f6597f2149f`

Evidence:

- Integration Quality Gate #911 / Run `35241996615`: SUCCESS.
- M09 #215 / Run `35241996654`: SUCCESS.
- Official Quality Gate #912 / Run `35243714139`: SUCCESS.
- Railway deployed the same official SHA for `himma-api` and `himma-web`.
- PostgreSQL, Redis and `himma-audio` object storage were present and healthy at the verified deployment checkpoint.
- Production `/api/health` returned 200.
- Production `/api/ready` returned 200 with config/database/content/approved_audio/storage/redis/security_mode checks healthy.
- Canonical runtime remained 125 items / 44 skills.

This production baseline remains the currently published version until the UX branch is merged and redeployed.

## Active UX rebuild

Branch:

`fix/ux-system-rebuild-2026-09-17`

Latest exact **functional** SHA tested before documentation-only continuation commits:

`09be49102d1aab8f09cf1a3267ccd073c46c7397`

Quality Gate #917 / Run `35261495545`: **SUCCESS**.

All four jobs passed on that exact SHA:

- Security: SUCCESS.
- Frontend: SUCCESS (TypeScript, ESLint, unit tests, Next.js build).
- Backend: SUCCESS (PostgreSQL, canonical validation, Alembic roundtrip/drift, seed idempotency, backend tests).
- Integration: SUCCESS, including Playwright.

Playwright report artifact:

- Artifact ID `10515801114`.
- Digest `sha256:12ce698a4bda93921eec73414b15f59efb24050c648a9a02d90ef370df145a74`.

## UX batch scope approved from owner screenshots/review

The current work is not a set of screenshot-specific patches. It is split into five root-cause batches:

### A — Student Question System

- Responsive stimulus typography/container sizing.
- Smaller mobile question title.
- Image-option cards that follow image/content rather than creating tall empty boxes.
- Compact ordered/sequence image interaction.
- Preserve rapid audio switching/race-condition fixes.
- Apply the same visual rules to Assessment, Activity and Admin Content Preview.

### B — Student Dashboard & Journey

- Dashboard is a journey surface, not equal-weight cards.
- Identity/current level/current state first.
- Primary next action second.
- Pretest → learning level → activities/reinforcement → posttest journey hierarchy.
- Real progress/results/stars/badges only.
- Pending Audio and explicit Rerecord remain visible without hijacking unrelated current work.

### C — Admin Audio Review Workflow

- Compact queue layout on mobile/desktop.
- Clear listen/start-review actions.
- Decision-first review form: approve or request rerecord, then relevant evidence fields.
- Reduce empty space and oversized buttons/forms.

### D — Admin Dashboard & Notifications

- Do not repeat one dashboard card for every pending recording.
- Dashboard shows aggregate operational counts.
- Individual events remain in Notification Center / Review Queue.

### E — Remaining Admin UX

- Student profile mobile tabs/layout.
- Add Student flow.
- Content Preview fidelity.
- Unified transient feedback/toast behavior.

## Audio journey contract — must not regress

- Submitted assessment recording does **not** block later unanswered questions.
- Academic finalization remains blocked while required recordings are pending supervisor review.
- Rerecord is an explicit task; it does not automatically hijack the current question/activity.
- Previous recordings remain historical evidence.
- Human Supervisor Review remains the academic authority while production ASR provider approval is pending.
- No Fake ASR, Student Audio Skip, Temporary Audio Skip or bypass.

## Current boundary / what remains

The UX candidate is **not merged and not deployed** yet.

Required before merge/release:

1. Review Playwright screenshots/visual evidence on phone + tablet + desktop against the owner-reported screenshots and A–E contracts.
2. Fix any visual mismatch found; rerun exact-head Quality Gate if code changes.
3. Run M09 Release Readiness on the final UX functional SHA.
4. Only after QG + M09 + Visual QA are green, fast-forward/merge to `stage/02-content`.
5. Run official exact-head CI after merge if the SHA changes.
6. Deploy Railway and verify deployed SHA, `/health`, `/ready`, login, Student Dashboard, question sizing, Audio Review, Pending Audio and Rerecord on Production.
7. Update final release evidence docs.

Do not mark this UX batch CLOSED before those steps complete.

## Persistent open/external items

- Production ASR provider approval remains external/deferred.
- Manual human screen-reader acceptance remains not claimed.

## Hard constraints

No fake ASR. No Student/Temporary Audio Skip. No history deletion. No Speech/Pronunciation Lab merge. No weakened tests, skip/xfail, retry-based masking, or runtime repair overlays. No PASS/CLOSED claim without exact-SHA evidence.
