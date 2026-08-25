# RESUME HERE — Stage 2 Closure Recovery

**Last updated:** 2026-08-25

**Branch:** `b02/stage2-closure`

**Base:** `b02/student-assessment-lifecycle@6a5293879fb25555dc2992ee0cf2b6f7c7441afa`

**Last accepted remote checkpoint:** B02 lifecycle gate, GitHub Actions #32 green.

## Current status: IN PROGRESS — RECONSTRUCTING UNPUSHED STAGE 2 CLOSURE WORK

A detailed cross-check of the Work-session handoff against GitHub established that the later activity/UI work described after B02 was not pushed to any repository branch. The green B02 branch remains intact and is not being rewritten.

The recovery branch `b02/stage2-closure` was created from the exact B02 green checkpoint. The governing recovery note is `docs/ops/stages/B02_STAGE2_CLOSURE_RECOVERY.md`.

## What is already remotely verified

- B00 trusted recovery accepted.
- B01 content source-of-truth accepted: 105 items, 44 skills, 264 rounds, exact 30/30 assessments and 30 core + 15 reinforcement activities.
- B02 student/assessment lifecycle accepted: maximum 15 grade-three students, pseudonymous access codes, pre/post lifecycle, exact resume, durable timing, idempotency, MinIO audio upload, human review, researcher-enabled posttest.
- Initial assessment level assignment already exists in backend finish logic: `<50 => level 1`, `<80 => level 2`, otherwise level 3.

## Verified gap that must be closed now

Remote GitHub still contains a placeholder student activity page and the student home disables the learning action. Therefore Stage 2 is not yet remotely closed even though a later local Work session reported implementing the activity runner.

## Current slice

Reconstruct and finish the Stage 2 learning path on this branch only:

1. Execute exactly ten core activities for the student’s assigned level.
2. Support the approved catalog interaction values rather than flattening them to generic multiple choice.
3. Render approved images/audio/icons/brand assets and preserve the two declared media gaps without fake replacements or penalties.
4. Persist activity progress/timing safely and resume after reload without duplicate submissions.
5. Expose progress to the researcher.
6. Keep posttest unavailable until the required core path is complete and then require researcher enablement.
7. Run PostgreSQL/Alembic, catalog/media, backend, frontend, build and full browser gate remotely.

## Do not do yet

- Do not start or label B03/Stage 3 accepted.
- Do not implement automatic ASR.
- Do not add adaptive 50/30/20 mastery decisions or automatic reinforcement routing in this closure slice.
- Do not alter the accepted B02 branch.

## Next action

Implement the missing activity execution path on `b02/stage2-closure`, then push evidence through GitHub Actions. Stage 3 begins only after Stage 2 closure is remotely green and documented.
