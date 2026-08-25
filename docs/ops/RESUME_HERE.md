# RESUME HERE — Stage 3 Accepted / Stage 4 Ready

**Last updated:** 2026-08-25

**Current branch:** `b03/adaptive-learning-engine`

**Accepted B03 implementation SHA:** `8d64eb9766fd69618960af0b279ae94484618d17`

**Authoritative implementation gate:** GitHub Actions #83 (`32800935038`) — backend, frontend and integration all PASS.

## Current status: STAGE 3 / B03 ACCEPTED

Stage 2 remains preserved as the accepted learning-path baseline. Stage 3 adds the adaptive-learning engine, approved reinforcement routing, event-backed rewards and researcher decision controls without rewriting the accepted Stage-2 branch.

## Verified adaptive behavior

1. Only valid completed learning evidence enters adaptive scoring. Missing-media-only rounds, incomplete attempts and unresolved/rerecord audio are academically neutral.
2. The newest three valid attempts are weighted `50/30/20`.
3. `<50%` gives support first; a second consecutive low automatic decision may demote exactly one level, never below level 1.
4. `50–<80%` stays in the current level.
5. `>=80%` can promote one level only with required-skill coverage and no required skill below `60%`, never above level 3.
6. Reinforcement uses an unused approved activity matching the weakest skill exactly; no unrelated fallback is allowed.
7. Decisions are durable/idempotent snapshots with saved explanations and history.
8. Researcher override requires a reason and is appended as a separate manual decision rather than deleting automated history.
9. Stars and badges are created only by valid real completion events and are duplicate-safe.
10. Researcher UI exposes adaptive state, moving mastery, transition, rewards, manual controls and decision history.

## Remote evidence

- Implementation: `b03/adaptive-learning-engine@8d64eb9766fd69618960af0b279ae94484618d17`
- GitHub Actions: run #83 / `32800935038`
- Backend: PASS
- Frontend: PASS
- Integration / Playwright: PASS
- Playwright artifact: `9546598013` (`playwright-report`)
- Artifact digest: `sha256:18fdf5f93421abb2c22e22cc196a81fc5bca9614fa841820546bee2c328ea2c2`
- Adaptive visual evidence: `screenshots/04-researcher-progress-10-of-10.png` shows 12 event-backed stars, level 3, 10/10 core completion, adaptive decision, 100.0% moving mastery, level 3 → 3, manual override controls and saved decision history.

## Do not reopen

- Do not rewrite B00/B01/B02 or accepted Stage-2 closure branches.
- Do not replace approved reinforcement content with invented fallback activities.
- Do not treat missing media or unresolved audio as an incorrect academic response.
- Do not change the 50/30/20, 50/80 and 60% skill-floor rules without an explicit requirements decision.

## Next boundary — Stage 4 / P07 ASR

Before writing automatic speech scoring code, select and document a real ASR provider and its integration contract. The ASR slice must then cover private audio retrieval, normalization, transcription, alignment/error extraction, confidence handling, human-review fallback and auditability while preserving the existing manual-review lifecycle.

Automatic ASR is **not** considered delivered by B03. Research dashboards/exports and final release hardening also remain separate later stages.

## Next action

Create the Stage-4/P07 branch from the final accepted B03 documentation checkpoint, record the ASR provider decision, then implement the speech pipeline behind its own backend/frontend/integration quality gate.
