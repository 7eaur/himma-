# ابدأ من هنا — مستودع هِمّة

هذه نقطة الدخول التنفيذية لأي محادثة أو وكيل جديد يعمل على منصة **هِمّة**.

> لا تعتمد على ذاكرة المحادثات أو SHA قديم. ابدأ دائمًا من المستودع الحي ثم استخدم التوثيق الحالي لتحديد نقطة الاستئناف.

## 1) المستودع والفروع

- Repository: `7eaur/himma-`
- Default branch: `stage/02-content`
- Execution branch: `audit/comprehensive-repository-review-2026-09-10`
- Current phase: `A10`
- Current wave: `W6 / Final Exact-SHA Acceptance`
- Current state: `W1–W5 GREEN; W6 Quality Gate GREEN but M09 blocked at deterministic Playwright; NO A11 / NO MERGE / NO DEPLOY`

قد يكون live HEAD أحدث من آخر functional candidate بسبب commits توثيق فقط. لا تعتبر docs-only SHA دليل اختبار.

## 2) ترتيب القراءة الإلزامي

1. `NEXT_CONVERSATION_PROMPT.md`
2. `docs/ops/STATUS.md`
3. `docs/ops/progress.json`
4. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-17_A10_W6_PLAYWRIGHT_BLOCKER_AR.md`
5. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_STATUS_UPDATE_2026-09-16_AR.md`
6. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
7. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_EXECUTION_ADDENDUM_2026-09-12_AR.md`
8. `docs/specs/SOURCE_OF_TRUTH.md`
9. `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md`
10. `AGENTS.md` ثم `.agents/rules/00-himma-core.md`, `.agents/rules/10-delivery-protocol.md`, `.agents/rules/20-security-quality.md`.

الـhandoff القديم الخاص بـPostgreSQL/account-lockout يبقى history فقط؛ blockerه تم حله.

## 3) Source of Truth

`live code → PostgreSQL schema/Alembic migrations → executable tests + exact-SHA CI → canonical contracts/approved decisions → current STATUS/progress/handoff → historical audit docs`

لا تعلن PASS/CLOSED اعتمادًا على وثيقة فقط.

## 4) الحالة الحالية المثبتة

- A00–A09: CLOSED AUDIT؛ لا تعاد.
- W1–W5: GREEN؛ لا تعاد بدون regression evidence جديد.
- W6: **IN PROGRESS — final M09 Release Readiness blocker only**.

آخر functional candidate مثبت:

`c67aaadf004b8dbadac6f3849719e5ccdcbcf6f2`

Commit:

`ci(w6): build pinned MinIO for M09 readiness`

على نفس SHA:

- Quality Gate #894 / Run `35167788906` = **SUCCESS**.
- M09 Release Readiness #210 / Run `35167789050` = **FAILURE**.
- M09 job `105032657002`.

## 5) ما تم حله ولا يعاد

- PostgreSQL/account-lockout bootstrap/order blocker: **RESOLVED**.
- Backend regression أصبح يمر على PostgreSQL migrated schema بدون weakening للtests.
- protected `trial` runtime controls عُزلت عن backend product regression بشكل متعمد، بينما runtime readiness بقي protected/trial.
- MinIO archive HTTP 410 blocker: **RESOLVED** عبر pinned source-build، بدون Docker.

في M09 #210 كل ما قبل browser regression وصل ونجح، بما يشمل migrations/backend regression/canonical publication/idempotency/MinIO/runtime/frontend/readiness/security/origin checks.

## 6) نقطة التوقف الدقيقة الآن

الـblocker الحالي داخل `AUD-A08-003` هو step:

`Run deterministic browser product regression`

في M09 #210 / Run `35167789050` / job `105032657002`.

لا يوجد في هذا التوثيق ادعاء بسبب Playwright أدق من ذلك. يجب على المنفذ التالي استخراج **exact failure** من logs/artifacts لنفس الـRun ثم تتبع الاختبار والكود/route/API المرتبط إلى root cause.

بسبب هذا الفشل لم يصل M09 إلى proof كامل لـ:

- PostgreSQL backup/restore.
- object-storage backup/restore.

لذلك W6 ليست GREEN بعد.

## 7) أول عمل عند الاستئناف

1. Fetch live HEAD وصنّف أي descendants بعد `c67aaad...` إلى docs-only أو functional.
2. افحص M09 #210 / Run `35167789050`, job `105032657002` logs/artifacts.
3. استخرج failing Playwright test + exact assertion/locator/request/error وأول application failure حقيقي.
4. افحص `.github/workflows/m09-release-readiness.yml`, `.github/workflows/ci.yml`, `apps/web/tests/TEST_OWNERSHIP.md` والملفات التي يشير إليها failure فقط.
5. أصلح root cause بدون skip/xfail/xpass/retries/weakened assertions/runtime overlays.
6. أي code/workflow change = functional SHA جديد.
7. اطلب **full Quality Gate + full M09 على نفس exact new SHA**.
8. لا تغلق W6 إلا بعد مرور declared Playwright release suite وPostgreSQL backup/restore وobject-storage backup/restore أيضًا.
9. عند GREEN الكامل فقط: W6 closure + STATUS/progress/gap/continuity update، مع فصل exact tested SHA عن docs-only commits.
10. **STOP؛ لا تنتقل إلى A11.**

## 8) عقود المنتج الأساسية

- Placement: `<50 → L1`, `50..<80 → L2`, `80..100 → L3`.
- Activity: `>=80 success`, `70..<80 guided retry`, `<70 reinforcement`.
- L1/L2 early promotion بعد >=6 Core فقط مع canonical mastery/critical evidence.
- L3 requires 10 Core.
- No automatic demotion.
- Manual override ≠ completion/badge.
- Latest three valid active-session Core evidences تستخدم 50/30/20.

Canonical approval: `HIMMA-CONTENT-APPROVAL-2026-09-08`.

Runtime: `125 items = 30 Pretest + 30 Posttest + 30 Core + 35 Reinforcement`, `44 skills`.

المسار الصحيح:

`approved/versioned contracts → canonical compile/release → deterministic publication → PostgreSQL runtime → structured APIs → deterministic UI`

Audio: لا Student Audio Skip؛ submissions append-only؛ latest active؛ Human Supervisor Review هي authority؛ ASR automated advisory فقط؛ Production ASR `AUD-A03-008` يبقى external-approval blocked.

## 9) القيود الثابتة

No Docker. No fake ASR. No Temporary Audio Skip. No history deletion. No Speech/Pronunciation Lab merge. No final merge. No weakened tests. No runtime repair overlays. No PASS/CLOSED without exact-SHA evidence. No A11 / Deploy / Railway / Production ضمن هذا الجدول. Manual human screen-reader غير منفذ. Deployed-header verification يبقى A11.

## 10) شرط الإغلاق

`same exact functional SHA: Quality Gate GREEN + full M09 GREEN including deterministic Playwright + PostgreSQL restore + object-storage restore → document W6 GREEN → STOP.`