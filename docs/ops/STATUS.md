# STATUS — Himma Platform

**Branch:** `b03/adaptive-learning-engine`

**Stage:** Stage 3 / B03 — `ACCEPTED`

**Accepted implementation SHA:** `8d64eb9766fd69618960af0b279ae94484618d17`

**Authoritative implementation gate:** GitHub Actions #83 — run `32800935038`

**Last verified:** 2026-08-25

---

## Stage 3 adaptive learning — ACCEPTED

Stage 3 extends the accepted Stage-2 learning path without rewriting the Stage-2 checkpoint. The adaptive engine, reinforcement routing, rewards and researcher controls are implemented on `b03/adaptive-learning-engine` and verified against PostgreSQL and the remote CI gate.

### Delivered and verified

- Moving mastery uses exactly the newest three valid attempts with weights `50/30/20` (newest → oldest).
- Invalid academic evidence is neutral rather than punitive: incomplete attempts, rerecord-required audio, unresolved/low-confidence audio and declared missing-media-only evidence are excluded.
- `<50%` triggers support first. A one-level demotion can occur only after a second consecutive low automatic decision, never below level 1.
- `>=80%` may promote one level only when required skill coverage exists and no required skill is below `60%`; promotion never exceeds level 3.
- The `50–<80` stability band stays at the current level.
- Reinforcement is selected only from the approved catalog and must match the weakest skill exactly. If no unused exact mapping exists, the runtime blocks rather than substituting unrelated content.
- Adaptive decisions are durable/idempotent snapshots and preserve their evidence and explanation.
- Researcher manual override requires a documented reason, is recorded as a separate decision, and does not erase automatic history.
- Rewards are event-backed: stars/badges require valid completed learning evidence and use durable reward keys to prevent duplicate rewards on refresh/retry.
- Researcher student detail shows stars/badges, latest adaptive decision, moving mastery, level transition, reason, targeted recommendation, manual override and decision history.
- Stage-2 guarantees remain intact: approved catalog, ten core activities, reload resume, timing/idempotency, researcher 10/10 progress and posttest gating.

### Acceptance evidence

| Gate | Result |
|---|---|
| Adaptive boundary/unit tests | PASS — 50/30/20, 50/80 thresholds, 60 skill floor, level floor/ceiling, support-before-demotion, manual override history |
| Valid-evidence filtering | PASS — unresolved/invalid evidence is excluded rather than treated as failure |
| Reinforcement routing | PASS — exact weakest-skill mapping from approved content only |
| Rewards | PASS — valid event-backed stars/badges with duplicate protection |
| PostgreSQL/Alembic | PASS — upgrade → downgrade → upgrade and `alembic check` |
| Catalog/seed | PASS — approved catalog validation and idempotent seed |
| Backend | PASS |
| TypeScript | PASS |
| ESLint | PASS |
| Frontend unit tests | PASS |
| Next.js production build | PASS |
| Browser integration | PASS |
| GitHub Actions | PASS — backend, frontend and integration all green in run #83 (`32800935038`) |
| Visual evidence | PASS — Playwright artifact `9546598013`, digest `sha256:18fdf5f93421abb2c22e22cc196a81fc5bca9614fa841820546bee2c328ea2c2` |

The full-page researcher screenshot `04-researcher-progress-10-of-10.png` from the accepted B03 run visibly contains the adaptive panel, event-backed stars, 10/10 core progress, moving mastery, current/target level, manual-override controls and saved decision history.

### Accepted checkpoints

- B00: `recovery/codex-baseline@e5fafe757bd57f8bdce35a8f8d0f3bbcc0784c2d`
- B01: `b01/content-source-of-truth@26d25e081b0c7c66f5d6b09b8b1750e67c745b41`
- B02 lifecycle: `b02/student-assessment-lifecycle@6a5293879fb25555dc2992ee0cf2b6f7c7441afa`
- Stage 2 closure: `b02/stage2-closure@38a1b8d1a03a56f08aa3afdf9404593351e05a87`
- Stage 3 / B03 implementation: `b03/adaptive-learning-engine@8d64eb9766fd69618960af0b279ae94484618d17`

## Next phase

Stage 3 is closed. The next roadmap boundary is Stage 4 / P07 speech processing (ASR). A real provider must be selected and documented before automatic ASR/alignment/confidence logic is integrated. Research reporting/export and final release hardening remain later stages and must not be silently mixed into the ASR slice.
