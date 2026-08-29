# STATUS — Himma Platform

**Last updated:** 2026-08-29  
**Repository:** `7eaur/himma-`  
**Current branch:** `recovery/ui-media-admin-overhaul`  
**Current program:** Full Maintenance M00→M09  
**Current slice:** **M07 — Research Reports — ACTIVE**

## Latest accepted implementation evidence

Current accepted implementation HEAD before this documentation-only update:

`654c9946b4b5b6e254817b2611fdf6494aa2a65e`

Main Quality Gate #363 / `33222592452`:

- Backend ✅
- Frontend ✅
- Integration / Playwright ✅
- Main E2E gate now explicitly includes `media-fidelity.spec.ts` in addition to the vertical slice and accessibility integration suites.

Responsive Visual Gate #28 / `33222592468`: **SUCCESS**.

Generated-sequence visual evidence is captured in the Quality Gate artifact at:

`playwright-report/screenshots/generated-sequence-assets.png`

The screenshot was reviewed after the successful run and confirms the ten approved 4:3 sequence scenes render through the real `/api/media/{asset_id}` path.

## Maintenance stage status

- M00 Restore Green — CLOSED.
- M01 Placement Scoring/Gates — CLOSED.
- M02 Adaptation State Machine — CLOSED.
- **M03 Reinforcement System — CLOSED for the previously identified content gaps.**
- M04 Student Product UI — CLOSED baseline.
- M05 Supervisor Product UX — CLOSED baseline.
- M06 Responsive/Accessibility/Design QA — CLOSED.
- **M07 Research Reports — ACTIVE.**
- M08 Real Speech Analysis — PENDING / EXTERNAL-GATED.
- M09 Release/UAT — PENDING.

## Current academic/runtime truth

- Original approved content remains 105 items and is not rewritten.
- Maintenance reinforcement v1 adds 18 activities.
- The approved 2026-08-29 gap-closure release adds 2 L3 reinforcement activities.
- Full runtime catalog = **125 items**.
- Reinforcement activities = **35 total**.
- Skills = 44.
- The previous three reinforcement gaps are closed as follows:
  - L2 `sukoon_word_reading` → approved existing `L2-REIN-02`.
  - L3 `literal_comprehension` → new `L3-REIN-11` with five rounds.
  - L3 `sentence_building` → new `L3-REIN-12` with five rounds.
- Placement determines starting level only.
- Journey ascends to L3 before Posttest.
- Activity bands remain: >=80 pass; 70–<80 guided retry; <70 reinforcement path.
- No promotion before 10/10 core and no unresolved reinforcement cycle.
- Recent mastery 50/30/20 is skill evidence, not a level-completion bypass.
- Automatic Demotion remains an OPEN decision; do not change silently.

## Visual educational content

**OI-15 is closed.**

- Existing approved Himma image-kit assets are reused first.
- Ten previously missing sequence scenes are checked in under the generated educational asset namespace.
- Generated manifest: `assets/education/developer/generated-sequence-map.json`.
- Generated IDs: `HIMMA-GEN-SEQ-001..010`.
- Runtime visual mapping: `packages/content/src/visual_asset_plan_v1.json`.
- `generate` is now empty in the visual plan.
- The canonical shorthand values `ذهب / لعب / نظف` in `L3-REIN-10` are explicitly bound to the approved beach sequence scenes rather than relying on fuzzy matching.
- Backend regression tests verify file presence, WebP signature, dimensions, SHA-256, runtime projection, and media serving.
- Main Playwright now requests all ten generated assets through the web proxy, verifies browser decode/natural dimensions, and captures a contact-sheet screenshot.

## Audio / Speech

- Fixed audio assets present: 50.
- Missing confirmed fixed audio: `موز`, `سَا`.
- Target fixed assets: 52.
- These two assets remain open and must not be faked or substituted (`موزة` is not `موز`).
- `HIMMA_TEMP_AUDIO_SKIP` remains temporary and academically neutral.
- Reference-Guided Arabic Reading Analysis remains the target speech architecture.
- Real provider/calibration/privacy/retention remain M08 work and are not claimed complete.

## M07 implementation status

Implemented and green on the accepted lineage:

- persisted Pre/Post comparison without recalculating placement;
- absolute improvement;
- relative improvement only when mathematically defined;
- start/current/final level;
- assessment and learning time;
- attempts/completed attempts;
- reinforcement-cycle summary;
- cohort summary;
- Excel multi-sheet export;
- PDF individual export;
- PDF cohort export;
- export audit logging;
- supervisor UI wired to persisted research data and export endpoints;
- speech-derived metrics remain explicitly unavailable until calibrated evidence exists.

Remaining M07 closure item:

- add a **supported per-skill summary from persisted graded response evidence only** and carry it consistently into the report/export layer. This must remain descriptive evidence and must not become a silent new mastery/scoring rule.

## Next action

Complete the supported per-skill M07 evidence summary with regression tests and export/UI consistency, restore a fully green Quality Gate for that HEAD, then close M07 documentation. After M07, continue M09 release/UAT preparation while M08 remains the separate externally gated speech stream.

## Mandatory continuity files

Start from `docs/handoff/READ_FIRST_2026-08-28_AR.md` and `docs/ops/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-08-28_AR.md`.
