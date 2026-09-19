# EVIDENCE INDEX — Himma Current Production

**Updated:** 2026-09-19  
**Functional release SHA:** 512f0a550eb098f0ce904ec4ed526d9e28098a6a  
**Latest verified operational/gate SHA:** 81006dcf09a544b1b54f42de4a0a57c1deb44bfd

## Official exact-head gates

### Quality Gate

Himma CI — Quality Gate #945  
Run: 35410973050  
Conclusion: SUCCESS

- Security: SUCCESS.
- Frontend: SUCCESS.
- Backend: 894 passed, 5 warnings.
- Migrations upgrade/downgrade/upgrade + drift: SUCCESS.
- canonical validation + seed idempotency: SUCCESS.
- Integration Playwright: 23 passed (3.7m).
- Playwright artifact: 10573957731.
- artifact digest: sha256:e7b63865ca425d91c0343b22ff72e8a03414713b36b963c1ffb50773a845714f.

### Responsive Visual Gate

M04 #362  
Run: 35410973052  
Conclusion: SUCCESS

- responsive smoke: 2 passed.
- artifact ID: 10574142637.
- artifact name: m04-responsive-screenshots.
- digest: sha256:888a88d92db0971a67f65983dec522532462280cc31fd6f7478111c889eababb.

### Release Readiness

M09 #227  
Run: 35410973045  
Conclusion: SUCCESS

- Backend regression: 894 passed, 5 warnings.
- Canonical catalog: 105 baseline items / 44 canonical skills.
- Canonical runtime publication: 125 items.
- Deleted student audio bypass route: absent.
- readiness: config/database/content/approved_audio/storage/redis/security_mode all ok.
- browser product regression: 23 passed (3.7m).
- PostgreSQL restore: PASS.
- restored skills: 44.
- restored content_items: 125.
- object store restore: 35 objects verified.
- backup artifacts stayed ephemeral in CI.

## Production Railway evidence

Project: friendly-dream  
Environment: production  
Branch: stage/02-content

Operational/deployment SHA:
81006dcf09a544b1b54f42de4a0a57c1deb44bfd

Functional SHA represented by that descendant:
512f0a550eb098f0ce904ec4ed526d9e28098a6a

- himma-api deployment 85e73822-a71b-4c2e-afef-ec08a4c6bc1b: SUCCESS.
- himma-web deployment d5a7f586-c93c-4a50-8faf-1e1d42cbeae1: SUCCESS.
- Postgres deployment: SUCCESS.
- Redis deployment: SUCCESS.
- himma-audio bucket: present.
- API predeploy Alembic: PASS.
- canonical publication: 125.
- account seed: PASS.
- Railway /ready healthcheck: 200.

## Branch evidence

All non-provider branches were compared against the official line. See:
docs/maintenance/HIMMA_BRANCH_INVENTORY_2026-09-18_AR.md

No relevant non-audio feature remains unmerged. deployment/platform-sandbox remains intentionally excluded as an obsolete diverged deployment experiment. Provider/speech-lab branches remain excluded by owner decision.

## Evidence interpretation

A later documentation-only closure commit may become the branch HEAD. Fetch live HEAD and compare changed paths. Documentation-only descendants do not invalidate the functional or operational exact-SHA evidence above.

Any new functional change requires new exact-SHA evidence.
