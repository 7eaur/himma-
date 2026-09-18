# Agent entry point — Himma

Before any project action, start with exactly:

1. START_HERE_AR.md
2. fetch live stage/02-content HEAD
3. docs/ops/STATUS.md
4. docs/ops/progress.json
5. docs/specs/SOURCE_OF_TRUTH.md
6. docs/specs/SYSTEM_SPEC.md
7. .agents/rules/00-himma-core.md
8. .agents/rules/10-delivery-protocol.md
9. .agents/rules/20-security-quality.md
10. follow the additional reading order listed in START_HERE_AR.md only as needed

Do not start from an old continuity handoff, audit checkpoint, recovery status, or dated UX handoff. Those are historical evidence unless docs/ops/DOCUMENTATION_INDEX.md marks them Current.

Always:
- compare live HEAD with the documented functional SHA;
- distinguish docs-only descendants from functional changes;
- verify current GitHub Actions before claims;
- verify Railway for production claims;
- preserve closed work unless regression evidence exists;
- keep reference/ read-only;
- never weaken tests to satisfy stale historical expectations.

Production ASR/provider branches are outside the current delivery and must not be merged without a separate owner assignment.
