# Himma V2 — instructions for project agents


> **Branch-specific owner authorization (2026-11-02):** You are on `feature/v2-native-speech-engine-rebuild-20261102`, a dedicated feature-rebuild branch created by explicit owner request, **not** an ad-hoc preview environment. This branch's SINGLE canonical task and handoff is [`docs/v2/agent-ops/HIMMA_V2_NATIVE_SPEECH_ENGINE_MASTER_HANDOFF_20261102_AR.md`](docs/v2/agent-ops/HIMMA_V2_NATIVE_SPEECH_ENGINE_MASTER_HANDOFF_20261102_AR.md). Read it BEFORE changing any reading/review code. Rebuild the voice evaluation and staff review flows completely **inside this original repository**, using existing Railway Web/API/DB/storage; preserve production and student records until full acceptance, and do not deploy partial phases.


> Active development and delivery branch: `v2/01-learning-foundation-20261007`.
> The GitHub default branch `stage/02-content` is historical and MUST NOT be treated as the active V2 code or production source.

## Start here
1. Read `START_HERE_AR.md`.
2. Read the live HEAD and relevant source code on the V2 branch; do not use stale handoff snapshots as a substitute.
3. Read `docs/v2/agent-ops/HIMMA_V2_MASTER_STATUS_GAPS_REMAINING_WORK_HANDOFF_20261028_AR.md`.
4. For current student acceptance, read `docs/v2/agent-ops/HIMMA_V2_R12_STUDENT_PAGE_BY_PAGE_UX_MATRIX_AR.md`.
5. For repository cleanup, read `docs/v2/agent-ops/REPOSITORY_CLEANUP_AUDIT_20261102_AR.md`.
6. Verify GitHub CI/M04/M09 on the exact functional SHA and check the actual Web/API production source and state on Railway before claiming release parity.

## Non-negotiable rules
- V2 is the only intended student/admin product. V1 source, routes, media, and data compatibility must be audited before deletion.
- Preserve student data, recordings, safe migration guards, and approved media; never treat a directory or file named V1 as automatically unused.
- No ad-hoc preview branch, additional Railway service, production test student, or unapproved migration. No force-push.
- Keep scheduled A/B/C agents disabled (see `docs/v2/agent-ops/CONTROL.json`); manual user-initiated work is permitted.
- Prefer root-cause fixes, stable UX, RTL/mobile support, clear Arabic feedback, and safe error handling.
- Never claim tests passed, production was deployed, or cleanup is complete without direct evidence.
- `reference/` and historical Git commits are evidence, not an alternative runtime or active delivery plan.
- Do not merge older PRs/branches into V2 without checking current code, data contracts, and test coverage.

## Source-of-truth priority
Running source and migrations + live production settings > exact-SHA test evidence > latest V2 handoff > historical documentation.
