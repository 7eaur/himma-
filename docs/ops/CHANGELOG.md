# CHANGELOG

## [Current Production / UX + Audio Review Closure] — 2026-09-18

**Official functional release:** `512f0a550eb098f0ce904ec4ed526d9e28098a6a`  
**Official branch:** `stage/02-content`  
**State:** MERGED + QG/M04/M09 GREEN + RAILWAY DEPLOYED

### Closed in the current release

- Unified the Student Dashboard around the learning journey and primary next action.
- Rebuilt the shared Student Question System for responsive text, image options and ordered/sequence interactions.
- Rebuilt Admin Audio Review into a clear flow: listen → decision → evaluation/notes → save.
- Clarified the evaluation fields: total units, deletions, substitutions and insertions.
- Kept pending audio academically neutral; students continue remaining unanswered assessment questions while finalization waits for required reviews.
- Made rerecord an explicit task without hijacking the current learner task, while preserving previous recordings.
- Aggregated pending recordings on Admin Dashboard instead of duplicating one attention card per recording.
- Improved Student Profile mobile layout, Add Student, Content Preview and transient feedback/toasts.
- Preserved the canonical runtime at 125 items / 44 skills and the approved static audio package at 54 IDs / 108 binaries.
- Removed stale documentation authority by introducing `START_HERE_AR.md`, the current documentation index, branch inventory, production evidence and current audio contract.

### Evidence

- QG #933 / Run `35301572062`: SUCCESS.
- M04 #359 / Run `35299593387`: SUCCESS.
- M09 #224 / Run `35299593312`: SUCCESS.
- Railway deployed API/Web from the same functional SHA successfully.

### External/deferred

Production ASR provider/calibration/governance remains outside this release. Manual human screen-reader acceptance and final study-retention/protocol decisions remain separate owner/ethics boundaries.

---


## [Corrective Recovery — UI / Media / Supervisor / Student] — 2026-08-26

**Branch:** `recovery/ui-media-admin-overhaul`  
**Implementation checkpoint:** `7dbc52bcc70a5768c81cd04065be00f1949c429d`  
**Evidence run:** GitHub Actions #171 / `32928214424` — Backend ✅ Frontend ✅ Integration/Playwright ✅

### Recovered

- Restored approved canonical assessment/activity interaction semantics instead of generic multiple-choice rendering.
- Connected real approved education images/audio and fixed media-package path resolution; added byte-level regression checks.
- Rebuilt assessment UI for image/listen/sequence/build-word/read-aloud families.
- Rebuilt student journey/dashboard and child-focused public landing.
- Added recording/re-record/send and manual audio-review states without false calibrated-ASR claims.
- Protected supervisor routes and standardized visible terminology to `المشرف` while preserving the legacy internal `researcher` identifier for compatibility.
- Added supervisor profile/password/add-supervisor settings.
- Added secure six-digit numeric student-code create/manual/edit/regenerate workflows and student name/status management.
- Added adaptive reinforcement mapping-gap recovery: student hold state, approved same-level supervisor options, written reason, audit logging, and student resume.
- Fixed adaptation/reinforcement concurrency behavior so duplicate creation conflicts do not roll back prior adaptive state.
- Preserved approved content gaps as neutral; no replacement audio is invented.
- Added full Chromium Playwright path with screenshots through reinforcement assignment/resume and live reports.
- Visual review found and fixed the adaptive-hold state so it is a real scoped full-screen dialog instead of an unstyled block leaking the underlying activity.

### Remaining external blockers

This recovery does not close P07 speech analysis. Real provider approval, representative recordings, confidence calibration, child-audio retention policy, and approved missing source audio remain open as recorded in `OPEN_ITEMS.md`.

---

## [P01 Audit] — 2026-08-17

### المرحلة: P01 (AUDIT_ONLY)

**الحكم على Stage 02:** REJECTED

**السبب:**
- `STAGE_02_REVIEW.md` ادّعى نجاح E2E وMinIO لكن:
  - `vertical-slice.spec.ts` يفشل بـ Timeout 30s
  - `storage.py` يستخدم mock-s3-bucket.local
  - CI لا يشغل PostgreSQL حقيقياً

**التوثيق المُنشأ:**
- `docs/ops/stages/P01/CURRENT_STATE_AUDIT.md`
- `docs/ops/stages/P01/BASELINE_SNAPSHOT.json`
- `docs/ops/stages/P01/TRACEABILITY_MATRIX.md`
- `docs/ops/stages/P01/GAP_REGISTER.md`
- `docs/ops/stages/P01/EVIDENCE_INDEX.md`
- `docs/ops/stages/P01/RECOVERY_RECOMMENDATION.md`
- `docs/ops/RESUME_HERE.md` (محدَّث)
- `docs/ops/STATUS.md` (محدَّث)
- `docs/ops/progress.json` (محدَّث)

---

## [Stage 01] — 2026-08-10

**الحكم:** ACCEPTED  
**Commit:** `ac3cae2`  
**التفاصيل:** إغلاق بوابة المرحلة الأولى (النواة والأمن) عبر gate-stage-01.md

---

## [Stage 02] — 2026-08-11 → مرفوضة

**HEAD عند الإغلاق المزعوم:** `88c0e71`  
**الحكم الفعلي:** REJECTED  
**السبب:** أدلة وهمية — انظر P01 GAP_REGISTER
