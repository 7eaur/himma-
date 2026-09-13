# HIMMA MASTER CONTINUITY HANDOFF — A10 / W4 / AUD-BADGE-008 ACTIVE

**Date:** 2026-09-13

## Source of Truth
Repository code + PostgreSQL migrations + executable tests/CI + canonical contracts. Do not substitute memory or prior chat summaries.

## Closed waves
- W1 GREEN — `ea132c9afbe152d0afa5ae581c058ce3248a0c48`, Run #813 / `34467329988`.
- W2 GREEN — `77ac72174a9e21163f6341ea8e0fcc172269eac3`, Run #822 / `34548388760`.
- W3 GREEN — `62e34b151e46b406cf3936201f80010abbe9d8d1`, Run #848 / `34729450663`; Security/Frontend/Backend/Integration-Playwright SUCCESS.

## Current wave
W4 `REWARDS_BADGES_MEDIA` is ACTIVE. Current batch only: `AUD-BADGE-008`.

The dependency order was chosen from the Master Gap Register: BADGE-003 and BADGE-004 depend on a canonical Reward Catalog/API, so BADGE-008 is the first root slice.

## Verified root evidence
- Persistence: `db.adaptation_models.RewardEvent` stores `reward_type`, `reward_key`, stars, persisted label and details.
- Current `adaptation.py` still contains local `BADGE_BY_LEVEL`, including old L3 wording `قارئ متميز`, and `/rewards` serializes persisted fields without catalog version/asset identity.
- Approved asset map `assets/characters/developer/asset-map.json` defines six reward identities: `BDG-01..BDG-06`; `BDG-06` slug `comprehension-star`, approved Arabic title `شارة نجم الفهم`.
- Existing reward creation already fails closed for unresolved/pending audio through `_attempt_signal`; this batch does not weaken that behavior.

## Implemented batch
Exact code gate SHA: `57495fb804d4f52f684aded176474155dace07d9`.
Tree SHA: `ec345b3be56312e9db8a7dd28e16f2e92ca7a9b0`.

Files:
- `services/api/reward_catalog.py`
- `services/api/reward_catalog_api.py`
- `services/api/main.py`
- `services/api/test_reward_catalog.py`

Contract:
- `HIMMA_REWARD_CATALOG_1.0.0`.
- stable star identities `BDG-01..03`.
- stable level-badge identities `BDG-04..06`.
- authenticated `GET /reward-catalog` exposing catalog keys, reward matching metadata, labels, asset IDs/slugs and version.
- historical persisted labels remain readable via `recorded_label`; canonical presentation resolver maps known historical level reward keys to current catalog label/asset identity; unknown legacy rewards remain readable without fabricated asset identity.

## Active CI
Quality Gate #850 / Run ID `34731134319` is the authoritative exact-SHA gate and is currently ACTIVE/QUEUED on `stage/a10-w4-ci`.

A duplicate predecessor #849 / `34731112994` was emitted by initial staging-branch creation on the same code tree. It is not a parallel implementation. Do not start further code while either is still active.

## Exact resume instruction
Fetch current HEAD and #850 first. If #850 is ACTIVE/QUEUED, inspect only and stop without code. If FAILURE, fix the first true failure inside AUD-BADGE-008 and re-gate. If SUCCESS including Integration/Playwright, close AUD-BADGE-008 with exact evidence and only then choose one next W4 gap from the Master Gap Register/dependency order.

Do not execute A11, Deploy, Railway, Production or final merge. No Docker, fake ASR, Temporary Audio Skip, history deletion or Speech/Pronunciation Lab merge. Continue W4 -> W5 -> W6; stop when W6 is Green.
