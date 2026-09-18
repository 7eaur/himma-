# Railway Production — Himma Current Release

**Updated:** 2026-09-18

## Functional release

Branch: stage/02-content  
SHA: 512f0a550eb098f0ce904ec4ed526d9e28098a6a

هذا هو آخر SHA وظيفي مثبت قبل دفعة مزامنة التوثيق.

## Gates

- QG #933 / 35301572062: SUCCESS.
- M04 #359 / 35299593387: SUCCESS.
- M09 #224 / 35299593312: SUCCESS.

## Railway

Project: friendly-dream  
Environment: production

Services:
- himma-api
- himma-web
- PostgreSQL
- Redis
- himma-audio bucket

Deployments:
- API 283feef7-ce46-41c1-84a1-f714e508405e: SUCCESS.
- Web 629571e4-8188-4b91-bfe5-79fe5e1ecae1: SUCCESS.

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

A documentation-only commit after the functional release may trigger a new Railway deployment and therefore show a newer commit hash. Treat that as a docs-only descendant unless functional paths changed.

Any later functional code change requires new QG/M04/M09 evidence as applicable.
