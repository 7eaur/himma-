# EVIDENCE INDEX — Himma Current Production

**Updated:** 2026-09-21  
**Exact functional/gate/production SHA:** `0bf1390bdbc0a19330c807d82d646424490b5a2b`

## Quality Gate

Himma CI — Quality Gate #976  
Run: `35541791265`  
Conclusion: SUCCESS

- Security: SUCCESS.
- Frontend TypeScript/ESLint/build: SUCCESS.
- Frontend unit tests: 40 passed.
- Backend: 902 passed, 5 warnings.
- migrations/drift/canonical seed idempotency: SUCCESS.
- Integration Playwright: 23 passed (3.7m).

## Responsive Visual Gate

M04 #387  
Run: `35541791302`  
Conclusion: SUCCESS

- responsive smoke: 2 passed.
- artifact ID: `10615031736`.
- artifact digest: `sha256:843fd55e673cdb93d51cfcd0c109d5f15beab7aa07bca926296a9b9338da7930`.

## Release Readiness

M09 #252  
Run: `35541791274`  
Conclusion: SUCCESS

- Backend regression: 902 passed, 5 warnings.
- Browser product regression: 23 passed (3.5m).
- PostgreSQL restore: PASS.
- restored skills: 44.
- restored content_items: 125.
- object store restore: 35 objects verified.
- readiness checks: all green.

## Canonical publication

- version: `HIMMA-CONTENT-APPROVAL-2026-09-08`.
- runtime items: 125.
- canonical SHA: `e6c749add3652ca8aa896065218673eaac8a07cd0cbca1e92710f35f14f5a904`.
- projection SHA: `e1d14b0b6102f635820aa7f9a9b074e4f7afd68a02006d0a8ee8a3f29f99670e`.

## Production Railway

Project: `friendly-dream`  
Environment: `production`

- himma-api deployment `f160b611-c157-4a53-9d37-cfae289cfb07`: SUCCESS.
- himma-web deployment `7f6fec27-3f38-4e21-afd6-c9b62729b168`: SUCCESS.
- deployed SHA: `0bf1390bdbc0a19330c807d82d646424490b5a2b`.
- PostgreSQL: SUCCESS.
- Redis: SUCCESS.
- himma-audio bucket: present.
- Alembic predeploy: PASS.
- /ready: HTTP 200.

## Interpretation

هذا SHA يحتوي تغييرات وظيفية فعلية في سياسة نصوص القراءة وفي Admin Content Review، لذلك يحل محل functional SHA القديم في التوثيق الحالي.
