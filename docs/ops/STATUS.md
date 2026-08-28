# STATUS — Himma Platform

**Branch:** `b04/asr-pipeline`

**Stage:** Stage 4 / P07 — `IN_PROGRESS`

**Base checkpoint:** `53666a0a67d19586ed1ea792b93d5c102dcb7883`

**Last accepted stage:** Stage 3 / B03 at implementation SHA `8d64eb9766fd69618960af0b279ae94484618d17`

**Last verified:** 2026-08-28

---

## Stage 4 / P07 speech analysis — provider-neutral infrastructure

P07 remains open because the real ASR provider and sample-based calibration are not yet approved. The provider-neutral infrastructure itself is implemented and its remote CI gate is green.

### Implemented in the current slice

- Durable `speech_analysis_jobs` queue table with queued/processing/retry/dead-letter/blocked-provider/review states.
- Durable `speech_analyses` result table storing provider/model/request metadata, reference text, transcript, confidence, duration, alignment events and calibration version.
- Reversible Alembic migration `0007_speech_analysis_pipeline`.
- Replaceable `SpeechProvider` protocol/adapter boundary.
- Runtime fails closed when no approved provider exists; there is no fake production ASR fallback.
- DB-backed asynchronous worker that discovers uploaded recordings and processes due jobs outside the HTTP request path.
- Retry/backoff/dead-letter behavior for temporary provider failures.
- Reference-guided Arabic word alignment against the exact reading text shown to the student.
- Word-level `correct`, `deletion`, `insertion`, and `substitution` events.
- Provider word timing/confidence fields are preserved when an approved provider supplies them.
- Researcher API for queue status, enqueue/status lookup and explicit retry.
- Confidence policy is fail-closed: until a calibrated threshold and calibration version are configured, valid ASR output remains `review_required`.
- Speech processing does not mutate the student's academic score by itself.

### Remote gate

GitHub Actions **Himma CI — Quality Gate**, run **#102** (`32806215309`) at implementation SHA `d4bf7fff33bacf7ac02f4e0e81a72c659bf1a2ce`, completed successfully.

Passed jobs:

- backend — success
- frontend — success
- integration — success, including Playwright E2E

The previous action item "finish remote CI gate" is therefore closed.

### Tests already covered by the slice

- Arabic normalization and diacritic-insensitive lexical matching.
- Exact reading, deletion, insertion and substitution alignment cases.
- Provider-not-configured => blocked state and zero fake analyses.
- Valid provider output remains human-review-only before calibration.
- Calibrated threshold path is separately tested.
- Temporary provider errors retry and then dead-letter at the configured limit.

## P07 is NOT accepted yet

The approved roadmap requires OI-02/OI-03 to be resolved before the stage can close. The following remain blocked on external/sample evidence:

- production ASR provider selection/approval;
- vendor privacy/retention/cost/recording-transfer decision;
- Arabic child-reading accuracy evaluation on representative Himma material;
- production confidence threshold calibration (OI-03);
- real provider integration through private MinIO -> worker -> ASR -> alignment;
- any phoneme/haraka scoring not proven by calibration.

Until those gates are satisfied, manual researcher review remains authoritative and P07 stays `IN_PROGRESS` rather than `ACCEPTED`.

## Preserved accepted checkpoints

- B00: `recovery/codex-baseline@e5fafe757bd57f8bdce35a8f8d0f3bbcc0784c2d`
- B01: `b01/content-source-of-truth@26d25e081b0c7c66f5d6b09b8b1750e67c745b41`
- B02 lifecycle: `b02/student-assessment-lifecycle@6a5293879fb25555dc2992ee0cf2b6f7c7441afa`
- Stage 2 closure: `b02/stage2-closure@38a1b8d1a03a56f08aa3afdf9404593351e05a87`
- Stage 3 / B03: `b03/adaptive-learning-engine@8d64eb9766fd69618960af0b279ae94484618d17`

## Next action

Use representative Arabic child-reading recordings against known Himma reference texts to benchmark candidate ASR providers, resolve OI-02, calibrate OI-03, add the approved real provider adapter, and run the private MinIO -> worker -> ASR -> alignment -> persisted result -> researcher review integration gate.
