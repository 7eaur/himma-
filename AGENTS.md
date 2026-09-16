# Agent entry point — Himma

Project instructions live in `.agents/`, but resumable execution state is maintained in the current continuity files.

Before any project action, read in this order:

1. `.agents/rules/00-himma-core.md`
2. `.agents/rules/10-delivery-protocol.md`
3. `.agents/rules/20-security-quality.md`
4. `docs/specs/SOURCE_OF_TRUTH.md`
5. `NEXT_CONVERSATION_PROMPT.md`
6. `docs/ops/STATUS.md`
7. `docs/ops/progress.json`
8. the `continuity_handoff` path named by `docs/ops/progress.json`
9. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
10. the current gap-status overlay named by `docs/ops/progress.json`.

Then fetch the live execution-branch HEAD and live GitHub Actions state before making claims or edits. A SHA stored in documentation is evidence/history, not permission to assume the branch has not moved.

Use the Master Gap Register and historical A00–A09/W1–W4 checkpoints to understand root causes and chronology, but do not redo closed audit/execution work without new regression evidence.

Treat `reference/` as read-only. Preserve history. Do not weaken tests to match stale historical expectations; reconcile the correct owner of truth and prove it on an exact-SHA gate.
