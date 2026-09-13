# HIMMA — Master Continuity Handoff — A10 / W3 / AUD-A04-001 ACTIVE

**Repository:** `7eaur/himma-`  
**Execution branch:** `audit/comprehensive-repository-review-2026-09-10`  
**Date:** 2026-09-13

## Source of Truth
Repository code + PostgreSQL migrations + executable tests/CI + canonical contracts.

## Closed evidence before current batch
- W1 CLOSED GREEN — `ea132c9afbe152d0afa5ae581c058ce3248a0c48` — Run #813 / ID `34467329988`.
- W2 CLOSED GREEN — `77ac72174a9e21163f6341ea8e0fcc172269eac3` — Run #822 / ID `34548388760`.
- `AUD-A04-008` CLOSED GREEN — `562b4eb3ef831cf7b8b51bd7d5e33145917cb382` — Run #842 / ID `34723513642`.
- `AUD-PERF-004` CLOSED GREEN — exact code SHA `33263107047447ae758ca2092209100ab541efdd` — Quality Gate #845 / Run ID `34725817618`.

## Run #845 exact evidence
Run #845 completed `success` on exact SHA `33263107047447ae758ca2092209100ab541efdd`.
- Security: SUCCESS.
- Frontend: SUCCESS — TypeScript, ESLint, unit tests, Next.js build.
- Backend: SUCCESS — native PostgreSQL, canonical validation, Alembic upgrade→downgrade→upgrade, model drift, canonical seed idempotency, full backend tests.
- Integration: SUCCESS — native PostgreSQL/Redis, pinned MinIO, migrations + full runtime seed, FastAPI + Next.js, Playwright E2E.

This closes `AUD-PERF-004`: Arabic typography is build-time/self-hosted through Next font handling and the executable runtime-network regression remains intact; no runtime Google Fonts browser dependency is accepted.

## Current W3 batch
`AUD-A04-001` only — Admin presentation unification where ownership is proven.

The current source inspection shows `AdminUI.tsx` / `AdminUI.module.css` already own shared Admin page/header/action/panel/stat/toolbar patterns, while Student Detail still carries parallel page/header/panel/action/stat presentation CSS in `student-detail.module.css`. The current task is to migrate only proven shared presentation ownership to AdminUI/global tokens while retaining page-local CSS for genuinely unique Student Detail patterns and preserving all canonical academic/data behavior.

## Mandatory continuation
1. Re-fetch audit HEAD before every write and verify no newer active CI/batch conflicts.
2. Keep current work limited to `AUD-A04-001` until an exact-SHA gate resolves it.
3. Do not change Journey/reward/audio academic truth, status semantics, or history behavior while refactoring presentation.
4. Do not weaken existing responsive/accessibility/partial-failure tests.
5. After code change, move `stage/a10-w3-ci` to the exact code SHA and run the full Quality Gate; document exact SHA, Run ID, gates, and remaining W3 work.
6. Do not start W4 until W3 is fully Green.

## Fixed prohibitions
No Docker, fake ASR, Temporary Audio Skip, history deletion, Speech/Pronunciation Lab merge, final merge, A11, Deploy, Railway, or Production.
