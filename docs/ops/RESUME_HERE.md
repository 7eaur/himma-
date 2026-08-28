# RESUME HERE — Stage 4 / P07 Speech Analysis

**Last updated:** 2026-08-28

**Current branch:** `b04/asr-pipeline`

**Current implementation checkpoint before this documentation update:** `d4bf7fff33bacf7ac02f4e0e81a72c659bf1a2ce`

**Last accepted stage:** Stage 3 / B03, implementation SHA `8d64eb9766fd69618960af0b279ae94484618d17`

## Current status: P07 IN_PROGRESS — infrastructure gate green, external ASR decision pending

The provider-neutral speech-analysis infrastructure is implemented and its remote GitHub Actions gate is green. P07 must not be marked accepted until a real ASR provider and representative recordings satisfy OI-02/OI-03.

## Remote gate verified

GitHub Actions **Himma CI — Quality Gate**, run **#102** (`32806215309`) on `b04/asr-pipeline` at SHA `d4bf7fff33bacf7ac02f4e0e81a72c659bf1a2ce` completed successfully.

All three jobs passed:

- `backend` — success
- `frontend` — success
- `integration` — success, including Playwright E2E

The CI gate used PostgreSQL, MinIO and the required integration services remotely. No local Docker requirement is introduced by this result.

## Implemented now

1. `speech_analysis_jobs` durable DB queue.
2. `speech_analyses` durable machine-result table.
3. Alembic `0007_speech_analysis_pipeline` with downgrade.
4. Replaceable `SpeechProvider` contract; no approved provider means explicit `blocked_provider` and no fake result.
5. Asynchronous `speech_worker.py` with uploaded-audio discovery, retries, backoff and dead-letter.
6. Reference-guided Arabic alignment with correct/deletion/insertion/substitution classification.
7. Optional provider word timing/confidence preservation.
8. Researcher speech queue/status/retry endpoints.
9. Calibration gate: no configured threshold/version => `review_required`.
10. Unit tests for Arabic alignment, provider absence, calibration behavior, retry and dead-letter.

## Hard safety/academic boundaries

- Manual researcher review remains authoritative until calibration is approved.
- Provider failure or low/unresolved confidence does not become an academic error.
- No fake/mock production ASR adapter.
- No phoneme/haraka conclusions before sample-based evidence.
- Do not alter accepted B03 adaptation rules in this stage.

## Pending from client / external decision

- Representative Arabic child-reading recordings on known Himma reference texts.
- OI-02: production ASR provider, contract/privacy, cost and recording-transfer policy.
- OI-03: confidence threshold calibrated from representative samples.
- OI-05 retention policy before real child data is stored in production.

Static platform audio inventory is a separate matter from representative child-reading recordings. The current content/audio review confirms the fixed audio library is nearly complete, but those fixed prompts cannot replace the calibration sample required for P07.

## Next action

Do **not** repeat the infrastructure CI gate; it is already green. The next executable P07 action starts when representative reading recordings are available: benchmark candidate ASR provider(s) against the exact known reference texts, document OI-02, add the approved real adapter, calibrate OI-03, then run the private MinIO -> worker -> ASR -> alignment -> persisted result -> researcher review integration gate.

P08 reports/exports and P09 release hardening remain separate later stages unless P07 is explicitly deferred by a documented decision while manual review remains authoritative.
