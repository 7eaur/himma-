# EVIDENCE INDEX — Himma

**Updated:** 2026-09-24

## Production functional baseline

- SHA: `4ecb27590f7c19cbe7823804b9919d91000415ef`.
- M04 Responsive Gate #403 / Run `35551846252`: `SUCCESS`.
- M09 Release Readiness #268 / Run `35551846250`: `SUCCESS`.
- QG Run `35551846194`: Frontend and Backend succeeded; Security failed only on three false-positive Railway deployment identifiers in documentation.
- The false-positive cause was fixed on the improvement branch without weakening Gitleaks or allowlisting whole files.

## Improvement branch full gate

- Evidence SHA: `186307b35cab1ad214b61f2eea601bc66240d4f8`.
- Himma CI — Quality Gate #1062.
- Run: `35660961118`.
- Conclusion: `SUCCESS`.
- Security and dependency audits: `SUCCESS`.
- Frontend type-check, ESLint, unit tests and build: `SUCCESS`.
- Backend migrations, drift check, canonical seed and tests: `906 passed, 5 warnings`.
- Integration Playwright: `23 passed (3.8m)`.
- Playwright artifact ID: `10666828583`.

## Canonical publication

- Version: `HIMMA-CONTENT-APPROVAL-2026-09-08`.
- Runtime items: 125.
- Skills: 44.
- Canonical digest: `e6c749add3652ca8aa896065218673eaac8a07cd0cbca1e92710f35f14f5a904`.
- Projection digest: `e1d14b0b6102f635820aa7f9a9b074e4f7afd68a02006d0a8ee8a3f29f99670e`.

## Railway production verification

- Verified: 2026-09-24.
- Project/environment: `friendly-dream / production`.
- Deployed SHA: `4ecb27590f7c19cbe7823804b9919d91000415ef`.
- Backend service deployment: `e9ae4753-bff0-46ce-8133-a330b18b0b34` — `SUCCESS`.
- Web service deployment: `55dff3b1-a2e3-41de-9416-edc9bc7757b0` — `SUCCESS`.
- PostgreSQL and Redis: `SUCCESS`.
- `himma-audio` bucket: present.

Later documentation-only descendants do not replace the production functional SHA until they are merged and deployed deliberately.
