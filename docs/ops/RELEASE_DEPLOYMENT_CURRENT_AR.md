# Railway Production — Himma Current Release

**Updated:** 2026-09-21

## Current release

Branch: `stage/02-content`  
Exact deployed SHA: `0bf1390bdbc0a19330c807d82d646424490b5a2b`

هذا هو functional SHA الحالي، وليس docs-only descendant.

## Exact-head gates

- QG #976 / Run `35541791265`: SUCCESS.
- M04 #387 / Run `35541791302`: SUCCESS.
- M09 #252 / Run `35541791274`: SUCCESS.

Evidence:
- Backend 902 passed, 5 warnings.
- Frontend unit 40 passed.
- Integration Playwright 23 passed.
- responsive smoke 2 passed.
- PostgreSQL restore PASS.
- content_items 125 / skills 44.
- object-store restore 35.

## Railway

Project: `friendly-dream`  
Environment: `production`

- Backend service deployment: `f160b611-c157-4a53-9d37-cfae289cfb07` — SUCCESS.
- Web deployment: `7f6fec27-3f38-4e21-afd6-c9b62729b168` — SUCCESS.
- Postgres: SUCCESS.
- Redis: SUCCESS.
- himma-audio bucket: present.
- /ready: 200.

Canonical publication during API deploy:
- 125 runtime items.
- canonical release SHA: `e6c749add3652ca8aa896065218673eaac8a07cd0cbca1e92710f35f14f5a904`.
- projection SHA: `e1d14b0b6102f635820aa7f9a9b074e4f7afd68a02006d0a8ee8a3f29f99670e`.

Any later functional change requires fresh exact-head gate evidence.
