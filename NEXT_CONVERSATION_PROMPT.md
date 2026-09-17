# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت الآن المسؤول الهندسي والمنتجي الكامل عن منصة **هِمّة** في:

- Repository: `7eaur/himma-`
- Execution branch: `audit/comprehensive-repository-review-2026-09-10`

لا تعتمد على ذاكرة محادثات سابقة. ابدأ من المستودع الحي مباشرة.

## أول شيء إلزامي

1. Fetch للـlive execution branch HEAD. لا تفترض أن HEAD الحالي هو exact tested code SHA؛ قد توجد docs-only commits أحدث.
2. اقرأ بالترتيب:
   - `START_HERE_AR.md`
   - `docs/ops/RESUME_HERE.md`
   - `docs/ops/STATUS.md`
   - `docs/ops/progress.json`
   - `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-17_A10_W6_PLAYWRIGHT_BLOCKER_AR.md`
   - `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_STATUS_UPDATE_2026-09-16_AR.md`
   - `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
   - `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_EXECUTION_ADDENDUM_2026-09-12_AR.md`
   - `docs/specs/SOURCE_OF_TRUTH.md`
   - `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md`
   - `AGENTS.md`
   - `.agents/rules/00-himma-core.md`
   - `.agents/rules/10-delivery-protocol.md`
   - `.agents/rules/20-security-quality.md`
3. Source of Truth:
   `live code → PostgreSQL schema/Alembic migrations → executable tests/CI → canonical contracts/approved decisions → current STATUS/progress/handoff → historical docs`.
4. لا تعِد A00–A09 أو W1–W5.

## الحالة المثبتة الحالية

A00–A09 CLOSED AUDIT. W1–W5 GREEN. W6 ما تزال **IN PROGRESS**.

آخر functional/code candidate مثبت:

`c67aaadf004b8dbadac6f3849719e5ccdcbcf6f2`

Commit:

`ci(w6): build pinned MinIO for M09 readiness`

على هذا exact SHA:

- Quality Gate #894 / Run `35167788906` = **SUCCESS**.
- M09 Release Readiness #210 / Run `35167789050` = **FAILURE**.
- M09 job `105032657002`.

أي docs-only SHA بعد ذلك لا يُستخدم كدليل Gate.

## ما تم حله ولا تعِده

- PostgreSQL/account-lockout migration/bootstrap order blocker: RESOLVED.
- backend regression/trial runtime-control interference: RESOLVED دون weakening tests.
- MinIO archived binary HTTP 410: RESOLVED عبر pinned source-build، no Docker.

M09 #210 وصل بعد هذه الإصلاحات إلى browser product regression، وكانت الخطوات السابقة ناجحة: schema/migrations, backend regression, canonical release/publication/idempotency, MinIO, runtime DB, frontend/API/Web readiness, security/origin checks.

## نقطة التوقف الدقيقة

M09 #210 فشل عند:

`Run deterministic browser product regression`

**لا يوجد root cause أدق مثبت في التوثيق بعد.** مهمتك الأولى هي استخراجه من نفس الـRun/job، لا تخمينه.

بسبب هذا الفشل لم يتم إثبات كامل:

- PostgreSQL backup/restore.
- object-storage backup/restore.

لذلك Quality Gate الأخضر وحده لا يغلق W6.

## المهمة التنفيذية

1. تحقق من live HEAD وصنّف descendants بعد `c67aaad...` إلى docs-only أو functional.
2. افتح M09 #210 / Run `35167789050` / job `105032657002` واقرأ logs/artifacts كاملة حول step `Run deterministic browser product regression`.
3. استخرج:
   - exact failing Playwright test/spec؛
   - exact assertion/locator/request/response/error؛
   - trace/screenshot/report إن وُجد؛
   - أول application failure حقيقي قبل symptom النهائي.
4. اقرأ بعد ذلك فقط ما يلزم من:
   - `.github/workflows/m09-release-readiness.yml`
   - `.github/workflows/ci.yml`
   - `apps/web/tests/TEST_OWNERSHIP.md`
   - failing Playwright spec/fixture
   - frontend route/component/state
   - backend API/service/schema المرتبط إن كان failure يعبر الشبكة.
5. حدّد root cause المدعوم بالأدلة وأصلحه من الجذر.
6. ممنوع skip/xfail/xpass، retries لإخفاء deterministic failure، weaker assertions، حذف release coverage، runtime repair overlays، أو تغيير عقود المنتج لكي يمر الاختبار.
7. أي code/workflow fix ينشئ functional SHA جديدًا.
8. شغّل/انتظر full Quality Gate وfull M09 Release Readiness على **نفس exact functional SHA**.
9. M09 يجب أن يمر حتى النهاية ويثبت على الأقل: backend regression + canonical/migration/readiness/idempotency + runtime readiness + deterministic declared Playwright suite + PostgreSQL backup/restore + object-storage backup/restore.
10. إذا فشل جزء آخر، افحص root cause وأصلحه، ثم أعد exact-SHA gates على SHA الجديد.
11. فقط عندما يكون Quality Gate وM09 كاملين GREEN على نفس exact SHA: أنشئ W6 GREEN closure وحدّث `docs/ops/STATUS.md`, `docs/ops/progress.json`, gap overlay, `START_HERE_AR.md`, `docs/ops/RESUME_HERE.md`, `NEXT_CONVERSATION_PROMPT.md`, وأحدث continuity handoff. سجّل exact passing code SHA + Run IDs منفصلة بوضوح عن docs-only descendants.
12. **STOP بعد W6 GREEN. لا تنتقل إلى A11 أو Deploy أو Railway أو Production أو final merge.**

## عقود المنتج الثابتة

- Placement: `<50=L1`, `50..<80=L2`, `80..100=L3`.
- Activity: `>=80 success`, `70..<80 guided retry`, `<70 reinforcement`.
- L1/L2 early promotion بعد >=6 Core فقط مع canonical mastery/critical evidence.
- L3 requires 10 Core.
- No automatic demotion.
- Manual override ≠ completion/badge.
- Latest three valid active-session Core evidences use 50/30/20 weights.
- Canonical approval: `HIMMA-CONTENT-APPROVAL-2026-09-08`.
- Runtime: 125 items = 30 Pretest + 30 Posttest + 30 Core + 35 Reinforcement; 44 skills.
- Canonical content path only: approved/versioned contracts → canonical compile/release → deterministic publication → PostgreSQL runtime → structured APIs → deterministic UI.
- No Student Audio Skip; submissions append-only; latest active; Human Supervisor Review authority; automated ASR advisory only; Production ASR `AUD-A03-008` remains external-approval blocked.

## حدود ثابتة

No Docker. No fake ASR. No Temporary Audio Skip. No history deletion. No Speech/Pronunciation Lab merge. No final merge. No weakened tests. No runtime repair overlays. No PASS/CLOSED without exact-SHA evidence. `AUD-SEC-006` deployed-header verification later/A11. `AUD-A11Y-005` manual human screen-reader unclaimed. `AUD-GIT-001` final merge unexecuted.

لا تكتفِ بتقرير. نفّذ root-cause fix وواصل exact-SHA gates حتى W6 GREEN أو حتى يظهر blocker خارجي حقيقي، ثم توقف.