# STATUS — Himma Platform

**Last synchronized:** 2026-09-19  
**Repository:** 7eaur/himma-  
**Official branch:** stage/02-content  
**Functional release SHA:** 512f0a550eb098f0ce904ec4ed526d9e28098a6a  
**Latest verified operational/gate SHA:** 81006dcf09a544b1b54f42de4a0a57c1deb44bfd  
**State:** CLOSED / PRODUCTION_GREEN

## Current truth

آخر دفعة UX وتشديد البوابات والتوثيق الموحّد أصبحت ضمن الفرع الرسمي. لا تستخدم handoffs القديمة التي تقول إن UX أو current-state candidate لم تُدمج أو لم تُنشر.

الـOperational SHA أعلاه descendant من Functional SHA ويغيّر التوثيق/Workflows/QA test logic فقط؛ لا يغيّر قواعد المنتج أو المحتوى الأكاديمي.

## Exact official evidence

- QG #945 / Run 35410973050: SUCCESS.
  - Security: SUCCESS.
  - Frontend: SUCCESS.
  - Backend: 894 passed, 5 warnings.
  - Integration Playwright: 23 passed (3.7m).
  - Playwright artifact: 10573957731.
- M04 #362 / Run 35410973052: SUCCESS.
  - responsive smoke: 2 passed.
  - screenshots artifact: 10574142637.
  - digest: sha256:888a88d92db0971a67f65983dec522532462280cc31fd6f7478111c889eababb.
- M09 #227 / Run 35410973045: SUCCESS.
  - Backend regression: 894 passed, 5 warnings.
  - Browser regression: 23 passed (3.7m).
  - readiness: config/database/content/approved_audio/storage/redis/security_mode all ok.
  - PostgreSQL restore: PASS.
  - restored skills: 44.
  - restored content_items: 125.
  - Object storage restore: 35 objects.
  - Student audio bypass route: absent.

## Production

Railway project: friendly-dream / production.

- himma-api deployment 85e73822-a71b-4c2e-afef-ec08a4c6bc1b: SUCCESS.
- himma-web deployment d5a7f586-c93c-4a50-8faf-1e1d42cbeae1: SUCCESS.
- deployment commit: 81006dcf09a544b1b54f42de4a0a57c1deb44bfd.
- branch: stage/02-content.
- Postgres: SUCCESS.
- Redis: SUCCESS.
- himma-audio bucket: present.
- API predeploy Alembic: PASS.
- canonical publication: 125 runtime items.
- API /ready: HTTP 200.

## Canonical product state

- 30 Pretest.
- 30 Posttest.
- 30 Core.
- 35 Reinforcement runtime.
- 44 skills.
- 50 student default capacity.
- Human Supervisor Review is current audio authority.
- Pending reading audio is academically neutral and does not block remaining unanswered questions.
- Assessment finalization waits for required reviews.
- Rerecord is an explicit task; previous recording history is preserved.
- No Student Audio Skip.
- No Temporary Audio Skip.
- No fake ASR.
- No automatic demotion.

## Branch reconciliation

All non-provider branches were rechecked against the official line. No missing relevant non-audio implementation remains outside stage/02-content.

deployment/platform-sandbox remains the only diverged non-audio branch; its 9 unique commits are an obsolete deployment experiment and are intentionally not merged.

Provider/speech-lab branches remain excluded by owner decision.

See docs/maintenance/HIMMA_BRANCH_INVENTORY_2026-09-18_AR.md.

## Remaining boundaries

Only external/owner items remain:
- production ASR/provider/calibration/privacy/governance;
- final retention policy for child recordings/data before a real study;
- final research-session parameters if not owner-approved;
- manual human screen-reader acceptance;
- optional custom domain/entity branding details.

## Current action

No hidden implementation task remains in the current delivery. Wait for a new owner assignment or verified regression.

Entry point: START_HERE_AR.md.
