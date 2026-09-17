# هِمّة — Continuity Handoff — A10 / W6 Playwright Readiness Blocker

**التاريخ:** 2026-09-17  
**Repository:** `7eaur/himma-`  
**Execution branch:** `audit/comprehensive-repository-review-2026-09-10`  
**Phase:** `A10`  
**Wave:** `W6 / Final Exact-SHA Acceptance`  
**State:** `IN PROGRESS — Quality Gate GREEN, M09 blocked at deterministic browser regression`

> هذا الملف هو أحدث handoff لـW6. يجب دائمًا Fetch للـlive branch HEAD أولًا. قد يكون HEAD الحالي docs-only descendant؛ لا تخلط بينه وبين exact functional SHA الذي عليه دليل الاختبارات.

## 1) Source of Truth

عند التعارض:

`live code → PostgreSQL schema/Alembic migrations → executable tests + exact-SHA CI → canonical contracts/approved decisions → current STATUS/progress/handoff → historical audit docs`

لا تعتمد على ذاكرة المحادثات السابقة كبديل عن المستودع.

## 2) ما هو مغلق ولا يعاد

- A00–A09: CLOSED AUDIT.
- W1–W5: GREEN.
- لا تعِد أي عمل مغلق بدون regression evidence جديد.

## 3) آخر functional candidate مثبت

Exact functional/code SHA:

`c67aaadf004b8dbadac6f3849719e5ccdcbcf6f2`

Commit:

`ci(w6): build pinned MinIO for M09 readiness`

على هذا SHA نفسه:

- Quality Gate #894 / Run `35167788906` = **SUCCESS**.
- M09 Release Readiness #210 / Run `35167789050` = **FAILURE**.
- M09 job: `105032657002`.

هذه هي functional evidence الحالية. أي commit توثيق لاحق ليس بديلًا عنها ولا يُسمى tested code SHA.

## 4) ما تم إصلاحه قبل blocker الحالي

### Account lockout / PostgreSQL bootstrap — RESOLVED

كان M09 يشغّل backend regression قبل schema migration، ما أدى إلى غياب `account_lockout_states`. تم إصلاح ترتيب/bootstrap قاعدة البيانات من الجذر ثم عزل backend product regression عن protected trial runtime controls. لم يتم skip/xpass أو إضعاف الاختبارات.

في M09 #209 على SHA `cce46ab41d236037702e100227778555f7582825` أصبح backend regression أخضر:

`890 passed, 5 warnings`

### MinIO archived binary 410 — RESOLVED

M09 #209 توقف لأن رابط MinIO archive المثبت أعاد HTTP 410. تم استبدال acquisition بمسار pinned source-build المتوافق مع Quality Gate، بدون Docker.

الإصلاح الحالي موجود في:

`c67aaadf004b8dbadac6f3849719e5ccdcbcf6f2`

## 5) blocker الحالي الدقيق

في M09 #210 / Run `35167789050` / job `105032657002`:

- خطوات setup للـNode/Python/Go وMinIO source build نجحت.
- PostgreSQL + Redis نجحا.
- migrations/drift/backend regression نجحت.
- reset DB + canonical content/release + deterministic publication/idempotency نجحت.
- MinIO private test bucket نجح.
- deterministic runtime database/frontend build/API/Web/runtime readiness/security/origin checks نجحت.
- الفشل حدث عند step:

`Run deterministic browser product regression`

إذًا **current blocker = deterministic Playwright/browser product regression** داخل M09.

لا تدّعِ root cause أدق قبل استخراج الخطأ الفعلي من logs/artifacts للـRun نفسه ثم ربطه بالاختبار والكود/route/API المعني.

## 6) ما لم يُثبت بعد بسبب الفشل

لأن M09 توقف عند Playwright، لم تصل السلسلة إلى دليل كامل للآتي:

- PostgreSQL backup/restore.
- private object-storage backup/restore.

لذلك W6 **ليست GREEN** حتى لو كان Quality Gate #894 ناجحًا.

## 7) المهمة التنفيذية التالية

1. Fetch للـlive execution HEAD وحدد إن كان descendant بعد `c67aaad...` docs-only أم functional.
2. افتح M09 #210 / Run `35167789050`, job `105032657002` واستخرج **exact Playwright failure** من logs/artifacts.
3. حدّد test file + failing assertion/locator/request/route/API + أول application error حقيقي، ولا تكتفِ بعرض symptom نهائي.
4. افحص workflow/test/source المرتبط فقط بقدر ما يلزم للوصول إلى root cause.
5. أصلح root cause بدون:
   - skip/xfail/xpass؛
   - retries لإخفاء deterministic failure؛
   - weakened assertions؛
   - runtime repair overlay؛
   - حذف release coverage.
6. أي تعديل code/workflow ينتج functional candidate SHA جديدًا.
7. شغّل/انتظر **full Quality Gate + full M09 Release Readiness على نفس exact new SHA**.
8. لا تغلق W6 إلا إذا مر M09 حتى النهاية وشمل بنجاح:
   - backend product regression؛
   - canonical release/migrations/readiness/idempotency؛
   - runtime readiness؛
   - deterministic declared Playwright release suite؛
   - PostgreSQL backup/restore؛
   - object-storage backup/restore.
9. بعد نجاح Quality Gate وM09 على نفس exact SHA فقط: أنشئ W6 GREEN closure وحدّث continuity/status/progress/gap docs مع Run IDs وexact tested SHA منفصلًا عن أي docs-only SHA.
10. **STOP بعد W6 GREEN. لا تنتقل إلى A11.**

## 8) الملفات المرجعية الأولى

اقرأ بالترتيب:

1. `START_HERE_AR.md`
2. `docs/ops/RESUME_HERE.md`
3. `docs/ops/STATUS.md`
4. `docs/ops/progress.json`
5. هذا الملف
6. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_STATUS_UPDATE_2026-09-16_AR.md`
7. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
8. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_EXECUTION_ADDENDUM_2026-09-12_AR.md`
9. `docs/specs/SOURCE_OF_TRUTH.md`
10. `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md`
11. `AGENTS.md`
12. `.agents/rules/00-himma-core.md`
13. `.agents/rules/10-delivery-protocol.md`
14. `.agents/rules/20-security-quality.md`

ثم افحص تحديدًا:

- `.github/workflows/m09-release-readiness.yml`
- `.github/workflows/ci.yml`
- `apps/web/tests/TEST_OWNERSHIP.md`
- الـPlaywright test/source الفعلي الذي تشير إليه logs الحالية.

## 9) عقود المنتج التي لا يجوز كسرها

- Placement: `<50 → L1`, `50..<80 → L2`, `80..100 → L3`.
- Activity: `>=80 success`, `70..<80 guided retry`, `<70 reinforcement`.
- L1/L2 early promotion بعد >=6 Core فقط مع canonical mastery/critical evidence.
- L3 requires 10 Core.
- No automatic demotion.
- Manual override ≠ completion/badge.
- Latest three valid active-session Core evidences تستخدم weights 50/30/20.

Canonical content approval:

`HIMMA-CONTENT-APPROVAL-2026-09-08`

Runtime content:

`125 = 30 Pretest + 30 Posttest + 30 Core + 35 Reinforcement`, مع `44 skills`.

المسار الوحيد الصحيح للمحتوى:

`approved/versioned contracts → canonical compile/release → deterministic publication → PostgreSQL runtime → structured APIs → deterministic UI`

Audio:

- no Student Audio Skip؛
- submissions append-only؛
- latest submission active؛
- Human Supervisor Review هي السلطة الأكاديمية؛
- automated ASR advisory only؛
- Production ASR `AUD-A03-008` يبقى BLOCKED حتى external provider/calibration/privacy/cost/governance approval.

## 10) الحدود الثابتة

- No Docker.
- No fake ASR.
- No Temporary Audio Skip.
- No history deletion.
- No Speech/Pronunciation Lab merge.
- No final merge.
- No weakened tests / skip / xpass.
- No runtime repair overlays.
- No PASS/CLOSED without exact-SHA evidence.
- `AUD-SEC-006` deployed-header verification = A11 لاحقًا.
- `AUD-A11Y-005` manual human screen-reader = غير منفذ ولا يُدّعى.
- `AUD-GIT-001` final merge = غير منفذ.
- No A11 / Deploy / Railway / Production ضمن هذا الجدول.

## 11) شرط الإغلاق

الشرط الوحيد:

`same exact functional SHA: full Quality Gate GREEN + full M09 Release Readiness GREEN (including Playwright + PostgreSQL restore + object-storage restore) → document W6 GREEN → STOP.`