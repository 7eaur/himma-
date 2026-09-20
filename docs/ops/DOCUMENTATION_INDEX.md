# فهرس التوثيق القانوني — هِمّة

**Updated:** 2026-09-21

## نقطة الدخول

1. `START_HERE_AR.md` — نقطة الدخول الرسمية.
2. `docs/handoff/HIMMA_MASTER_HANDOFF_2026-09-21_AR.md` — التسليم الكامل الحالي للمحادثة التالية.
3. `NEXT_CONVERSATION_PROMPT.md` — برومبت قصير لبدء محادثة جديدة.

## CURRENT / AUTHORITATIVE

- `docs/ops/STATUS.md`
- `docs/ops/progress.json`
- `docs/ops/RESUME_HERE.md`
- `docs/ops/PROJECT_STATE.md`
- `docs/ops/ROADMAP.md`
- `docs/ops/CHANGELOG.md`
- `docs/ops/EVIDENCE_INDEX.md`
- `docs/ops/RELEASE_DEPLOYMENT_CURRENT_AR.md`
- `docs/ops/OPEN_ITEMS.md`
- `docs/specs/SOURCE_OF_TRUTH.md`
- `docs/specs/SYSTEM_SPEC.md`
- `docs/specs/ARCHITECTURE_BASELINE.md`
- `.agents/rules/00-himma-core.md`
- `.agents/rules/10-delivery-protocol.md`
- `.agents/rules/20-security-quality.md`
- `docs/ops/DECISIONS.md`
- `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_CURRENT_AR.md`
- `docs/maintenance/HIMMA_BRANCH_INVENTORY_2026-09-18_AR.md`
- `VERSION.md`

## CURRENT code/contracts that matter for the latest batch

Reading/content:
- `services/api/canonical_release.py`
- `services/api/reading_text_policy_2026_09_21.py`
- `services/api/test_reading_text_policy_2026_09_21.py`
- `packages/content/training/himma_reading_training_corpus_v2026_09_21.jsonl`

Admin content review:
- `services/api/content_preview.py`
- `apps/web/src/app/admin/(dashboard)/content-preview/page.tsx`
- `services/api/test_content_surface_parity.py`

## Historical rule

أي handoff/checkpoint/audit/prompt مؤرخ غير مذكور أعلاه يُعامل كـ HISTORICAL / REFERENCE ONLY. لا يفتح مرحلة مغلقة ولا يتغلب على live code أو exact-SHA evidence.
