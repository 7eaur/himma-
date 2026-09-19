# Railway Production — Himma Current Release

**Updated:** 2026-09-19

## Functional release

Branch: stage/02-content  
Functional SHA: 512f0a550eb098f0ce904ec4ed526d9e28098a6a  
Latest verified operational/gate SHA: 81006dcf09a544b1b54f42de4a0a57c1deb44bfd

الـOperational SHA descendant توثيقي/بوابات/QA deterministic من الـFunctional SHA ولا يغيّر Product Runtime أو العقود الأكاديمية.

## Official exact-head gates

- QG #945 / Run 35410973050: SUCCESS.
- M04 #362 / Run 35410973052: SUCCESS.
- M09 #227 / Run 35410973045: SUCCESS.

Evidence summary:
- Backend: 894 passed, 5 warnings.
- Integration/browser: 23 passed.
- M04 responsive smoke: 2 passed.
- readiness: all checks ok.
- PostgreSQL restore: PASS.
- restored content_items: 125.
- restored skills: 44.
- object-store restore: 35 objects verified.
- Student audio bypass route: absent.

## Railway

Project: friendly-dream  
Environment: production

Services:
- himma-api
- himma-web
- PostgreSQL
- Redis
- himma-audio bucket

Activation deployments for operational SHA 81006dcf09a544b1b54f42de4a0a57c1deb44bfd:
- API 85e73822-a71b-4c2e-afef-ec08a4c6bc1b: SUCCESS.
- Web d5a7f586-c93c-4a50-8faf-1e1d42cbeae1: SUCCESS.

Runtime checks:
- Alembic predeploy: PASS.
- canonical content publication: 125 items.
- account seed: PASS.
- API healthcheck /ready: HTTP 200.
- Postgres/Redis: SUCCESS.
- audio bucket present.

Web domain:
himma-web-production.up.railway.app

## Important SHA rule

A later documentation-only closure commit may become the live branch HEAD and may trigger a no-functional-change Railway redeploy. That does not replace:
- Latest Functional SHA = 512f0a550eb098f0ce904ec4ed526d9e28098a6a.
- Latest verified operational/gate SHA = 81006dcf09a544b1b54f42de4a0a57c1deb44bfd.

Any later functional code change requires fresh QG/M04/M09 evidence as applicable.
