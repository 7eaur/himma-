# Delivery protocol — Himma

## Start small

At the start of a session:
1. read START_HERE_AR.md;
2. fetch live stage/02-content HEAD;
3. read docs/ops/STATUS.md and progress.json;
4. open only the current spec/acceptance/code needed for the new assignment.

Do not re-run old audits or recovery waves unless there is new regression evidence.

## Execution

1. State the current exact base SHA.
2. Work on one coherent vertical slice.
3. Fix root cause, not screenshot-specific symptoms.
4. Run targeted tests.
5. Run the required exact-head gate(s).
6. Update current docs only when truth changes.
7. Preserve historical docs as evidence; do not rewrite history to pretend old states never existed.
8. Merge/deploy only after the relevant gates are green and the assignment authorizes it.

## Human checkpoints

Pause for:
- scope/research-rule change;
- secrets/accounts;
- irreversible deletion/data-loss migration;
- external publication;
- a new Production ASR/provider decision;
- a contradiction that materially changes behavior.

Ordinary fixes/tests/docs updates inside an authorized task proceed without repeated confirmation.

## Git safety

- Official branch: stage/02-content.
- Keep it green.
- Use a dedicated branch for material functional work.
- A docs-only synchronization may be integrated after CI, while keeping the last functional SHA separately documented.
- Never commit child recordings, secrets, .env files, real child data, DB dumps, caches, or dependencies.
- Never force-reset unrelated work.

## Completion report

Report:
- Done.
- Exact functional SHA.
- Tests/gates.
- Production evidence if relevant.
- Open external blockers only.
- Next action or CLOSED/WAITING_FOR_OWNER.
