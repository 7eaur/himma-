# CHANGELOG

## [Reading Content Policy + Admin Approved Content Review] — 2026-09-21

**Current functional/gate/production SHA:** `0bf1390bdbc0a19330c807d82d646424490b5a2b`  
**Official branch:** `stage/02-content`  
**State:** CLOSED + QG/M04/M09 GREEN + RAILWAY DEPLOYED

### Reading/content

- Added final-release reading-text policy: single-token letters/syllables/words preserve approved diacritics; multi-word phrases/sentences/passages remove optional marks while retaining shadda.
- Added 92-record training corpus at `packages/content/training/himma_reading_training_corpus_v2026_09_21.jsonl`.
- Added regression tests that match the corpus to the final canonical release.
- Canonical SHA is now `e6c749add3652ca8aa896065218673eaac8a07cd0cbca1e92710f35f14f5a904`.

### Admin content review

- Retired the student-interface simulation concept from `/admin/content-preview`.
- Rebuilt it as read-only **المحتوى المعتمد** from approved PostgreSQL content.
- Exposes questions, instructions, hints, options, correct answers, ordered answers, recording targets, images and audio to the supervisor.
- Added full-text search, filters and linked reinforcement candidates.
- Preserved answer-safe Student serializers and verified the admin page writes no student progress.

### Evidence

- QG #976 / Run `35541791265`: SUCCESS — Backend 902 passed; Frontend unit 40 passed; Playwright 23 passed.
- M04 #387 / Run `35541791302`: SUCCESS.
- M09 #252 / Run `35541791274`: SUCCESS.
- Railway API `f160b611-c157-4a53-9d37-cfae289cfb07`: SUCCESS.
- Railway Web `7f6fec27-3f38-4e21-afd6-c9b62729b168`: SUCCESS.
- /ready = 200.

---

## [Current-State Closure / Gate Hardening + Production Verification] — 2026-09-19

**Latest Functional SHA:** `512f0a550eb098f0ce904ec4ed526d9e28098a6a`  
**Latest verified operational/gate SHA:** `81006dcf09a544b1b54f42de4a0a57c1deb44bfd`  
**Official branch:** `stage/02-content`  
**State:** CLOSED + QG/M04/M09 GREEN + RAILWAY DEPLOYED + READY

### Closure evidence

- Fast-forwarded the current-state descendant into the official branch without force.
- QG #945 / Run `35410973050`: SUCCESS — Backend 894 passed, 5 warnings; Integration Playwright 23 passed (3.7m).
- M04 #362 / Run `35410973052`: SUCCESS — responsive smoke 2 passed; artifact `10574142637`.
- M09 #227 / Run `35410973045`: SUCCESS — runtime 125 items / 44 skills; PostgreSQL restore PASS; object-store restore 35; readiness all ok; Student Audio Skip absent.
- Railway API deployment `85e73822-a71b-4c2e-afef-ec08a4c6bc1b`: SUCCESS.
- Railway Web deployment `d5a7f586-c93c-4a50-8faf-1e1d42cbeae1`: SUCCESS.
- Production API /ready returned HTTP 200 during deployment.
- Functional runtime remains `512f0a5...`; the operational descendant contains documentation/workflow/QA-test hardening only.

### Remaining external boundaries

Production ASR/provider/calibration/governance, child-data retention before a real study, final research-session parameters if not owner-approved, manual human screen-reader acceptance, and optional custom-domain/entity branding remain outside this delivery.

---

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
