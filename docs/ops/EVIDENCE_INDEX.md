# EVIDENCE INDEX — Himma Current Production

**Updated:** 2026-09-18  
**Functional release SHA:** 512f0a550eb098f0ce904ec4ed526d9e28098a6a

## Quality Gate

Himma CI — Quality Gate #933  
Run: 35301572062  
Conclusion: SUCCESS

- Security: SUCCESS.
- Frontend: TypeScript + ESLint + unit + Next build = SUCCESS.
- Backend: 894 passed, 5 warnings.
- Migrations upgrade/downgrade/upgrade + drift = SUCCESS.
- canonical validation + seed idempotency = SUCCESS.
- Integration Playwright: 20 passed (3.6m).
- Playwright report artifact: 10530208479.

## Responsive Visual Gate

M04 #359  
Run: 35299593387  
Conclusion: SUCCESS

Artifact:
- ID 10529103623
- name m04-responsive-screenshots
- digest sha256:04a0b08ac2e25e27405ab24b2ec85bc1229b67909c47eb558c69bd859cd2826b

## Release Readiness

M09 #224  
Run: 35299593312  
Conclusion: SUCCESS

- Backend regression: 894 passed, 5 warnings.
- Canonical publication: 125 items.
- Deleted audio bypass route: absent.
- readiness: config/database/content/approved_audio/storage/redis/security_mode all ok.
- browser product regression: 20 passed (3.6m).
- PostgreSQL restore: PASS.
- restored: 44 skills, 125 content_items, 358 content_steps, 824 options, 265 asset links.
- object store restore: 35 objects verified.
- backup artifacts stayed ephemeral in CI.

## Production Railway evidence

Project: friendly-dream  
Environment: production

Functional SHA deployed:
512f0a550eb098f0ce904ec4ed526d9e28098a6a

- himma-api deployment 283feef7-ce46-41c1-84a1-f714e508405e: SUCCESS.
- himma-web deployment 629571e4-8188-4b91-bfe5-79fe5e1ecae1: SUCCESS.
- Postgres deployment: SUCCESS.
- Redis deployment: SUCCESS.
- himma-audio bucket: present.
- API predeploy Alembic: PASS.
- canonical publication: 125.
- account seed: PASS.
- Railway /ready healthcheck: 200.

## Branch evidence

All non-provider branches were compared against official functional SHA. See:
docs/maintenance/HIMMA_BRANCH_INVENTORY_2026-09-18_AR.md

No relevant non-audio feature remains unmerged.

## Evidence interpretation

If the official branch receives docs-only commits after this functional SHA:
- fetch live HEAD;
- compare changed paths;
- do not discard the functional evidence above merely because HEAD differs;
- any new functional change requires new exact-SHA evidence.
