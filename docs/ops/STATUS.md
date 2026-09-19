# STATUS — Himma Platform

**Last synchronized:** 2026-09-19  
**Repository:** 7eaur/himma-  
**Official branch:** stage/02-content  
**Functional release SHA:** 512f0a550eb098f0ce904ec4ed526d9e28098a6a  
**State:** PRODUCTION_GREEN / CURRENT UX MERGED AND DEPLOYED
**Current-state candidate SHA:** 5de29b71b9ab8d7df5c6c723136810f5ed56b213 — READY_FOR_FAST_FORWARD


## Current truth

آخر دفعة UX التي شملت Student Dashboard، Question System، Admin Dashboard، Audio Review، Student Profile، Add Student، Content Preview وfeedback/toasts أصبحت ضمن الفرع الرسمي ونُشرت على Railway.

لا تستخدم handoffs القديمة التي تقول إن UX لم تُدمج أو لم تُنشر.

## Current-state exact-head evidence

- QG #943 / Run 35403341210: SUCCESS — Backend 894 passed, 5 warnings; Integration Playwright 23 passed (3.8m); artifact 10571581856.
- M04 #361 / Run 35403341212: SUCCESS — responsive smoke 2 passed; artifact 10571297880; digest sha256:3498fc96ea6f555b884bca91016048cbb0459e5354d9b76af5709160383b8518.
- M09 #226 / Run 35403341199: SUCCESS — Backend 894 passed, 5 warnings; browser 23 passed (3.7m); 125 items / 44 skills; PostgreSQL restore PASS; object-store restore 35; readiness all ok; audio bypass absent.

Latest Functional SHA remains 512f0a550eb098f0ce904ec4ed526d9e28098a6a because the descendant contains docs/workflow/QA-test changes only.

## Functional baseline evidence

- Quality Gate #933 / Run 35301572062: SUCCESS.
  - Security: SUCCESS.
  - Frontend: SUCCESS.
  - Backend: 894 passed, 5 warnings.
  - Integration Playwright: 20 passed (3.6m).
  - Playwright artifact: 10530208479.
- M04 #359 / Run 35299593387: SUCCESS.
  - responsive screenshots artifact: 10529103623.
- M09 #224 / Run 35299593312: SUCCESS.
  - Backend regression: 894 passed, 5 warnings.
  - Browser regression: 20 passed.
  - readiness: all checks ok.
  - PostgreSQL restore: PASS.
  - Object storage restore: 35 objects.
  - bypass route: absent.

## Production

Railway project: friendly-dream / production.

- himma-api deployment 283feef7-ce46-41c1-84a1-f714e508405e: SUCCESS.
- himma-web deployment 629571e4-8188-4b91-bfe5-79fe5e1ecae1: SUCCESS.
- Postgres: SUCCESS.
- Redis: SUCCESS.
- himma-audio bucket: present.
- API /ready healthcheck during deployment: 200.
- Runtime content: 125 items / 44 skills.

## Canonical product state

- 30 Pretest.
- 30 Posttest.
- 30 Core.
- 35 Reinforcement runtime.
- 44 skills.
- 50 student default capacity.
- Human Supervisor Review is current audio authority.
- Pending reading audio does not block remaining unanswered questions; finalization waits for required review.
- Rerecord is explicit and history-preserving.
- No student audio bypass.

## Branch reconciliation

All non-provider branches were compared with official. No missing relevant non-audio work remains outside stage/02-content. The only diverged non-audio branch is deployment/platform-sandbox; its 9 unique commits describe an obsolete experimental deployment topology and are intentionally not merged.

See docs/maintenance/HIMMA_BRANCH_INVENTORY_2026-09-18_AR.md.

## Remaining boundaries

Only external/later items remain:
- production ASR/provider/calibration/governance;
- final retention policy for child recordings/data before a real study;
- research-session parameters not yet owner-approved;
- manual human screen-reader acceptance;
- optional custom domain/entity branding details.

## Current action

Current-state candidate is green and ready for fast-forward. After the official ref moves, verify Railway auto-deploy, /ready, production smoke, and synchronize final deployment evidence.

Entry point: START_HERE_AR.md.
