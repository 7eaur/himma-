# RESUME HERE — Stage 4 / P07 Infrastructure

**Last updated:** 2026-08-25

**Current branch:** `b04/asr-pipeline`

**Base checkpoint:** `53666a0a67d19586ed1ea792b93d5c102dcb7883`

**Last accepted stage:** Stage 3 / B03, implementation SHA `8d64eb9766fd69618960af0b279ae94484618d17`

## Current status: P07 IN_PROGRESS

The provider-neutral speech-analysis infrastructure is implemented on the Stage-4 branch. P07 must not be marked accepted until a real ASR provider and representative recordings satisfy OI-02/OI-03.

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
10. Added unit tests for Arabic alignment, provider absence, calibration behavior, retry and dead-letter.

## Hard safety/academic boundaries

- Manual researcher review remains authoritative until calibration is approved.
- Provider failure or low/unresolved confidence does not become an academic error.
- No fake/mock production ASR adapter.
- No phoneme/haraka conclusions before sample-based evidence.
- Do not alter accepted B03 adaptation rules in this stage.

## Pending from client / external decision

- Representative Arabic reading recordings.
- OI-02: production provider, contract/privacy, cost and recording-transfer policy.
- OI-03: confidence threshold calibrated from representative samples.
- OI-05 retention policy before real child data is stored in production.

## Next action

Complete the remote GitHub Actions gate for the provider-neutral infrastructure. After recordings arrive: benchmark candidate provider(s) on the supplied known reference texts, document the decision, add the real adapter, calibrate confidence, then run an integration gate covering private MinIO audio -> worker -> ASR -> alignment -> persisted result -> researcher review.

P08 reports/exports and P09 release hardening remain separate later stages.
