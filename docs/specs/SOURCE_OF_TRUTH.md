# خريطة مصدر الحقيقة — منصة هِمّة

**آخر تحديث تنفيذي:** 2026-09-17  
**المستودع:** `7eaur/himma-`  
**فرع التنفيذ:** `audit/comprehensive-repository-review-2026-09-10`  
**الحالة:** `A00–A09 CLOSED; W1–W5 GREEN; W6 FINAL RELEASE READINESS IN PROGRESS`

تهدف هذه الخريطة إلى منع أي محادثة أو وكيل من اختيار ملف قديم لمجرد أن اسمه يبدو رسميًا. التاريخ محفوظ، لكن الحقيقة التنفيذية الحالية تُحسم بالأدلة الحية.

## 1) ترتيب القوة العام

عند التعارض، استخدم الترتيب التالي:

1. **الكود الحي على فرع التنفيذ + PostgreSQL schema/Alembic migrations**.
2. **Executable tests + exact-SHA GitHub Actions** على نفس الكود.
3. **العقود الكانونية والقرارات المعتمدة والمؤرخة** للمحتوى/الصوت/الميديا/المكافآت والمنطق الأكاديمي.
4. **حالة المشروع الحالية**: `START_HERE_AR.md`, `docs/ops/RESUME_HERE.md`, `docs/ops/STATUS.md`, `docs/ops/progress.json`, `NEXT_CONVERSATION_PROMPT.md`, وأحدث Master Continuity Handoff.
5. المواصفات الحالية داخل `docs/specs/` وسجلات التنفيذ الحالية داخل `docs/maintenance/`.
6. الأصول/manifests داخل `assets/`.
7. الوثائق الأصلية داخل `reference/original/`.
8. النسخ المشتقة داخل `reference/derived/` والنماذج/الـprototype بوصفها مراجع بصرية أو تاريخية فقط.

الوثيقة وحدها لا تغلق Gap. الإغلاق يتطلب السلوك الصحيح + executable evidence على exact SHA متى كان ذلك مطلوبًا.

## 2) نقطة الاستئناف الحالية

الحالة التنفيذية الحالية ليست W4 ولا recovery القديمة.

- A00–A09: CLOSED AUDIT.
- W1–W5: GREEN.
- W6: IN PROGRESS.

آخر functional candidate مثبت قبل أحدث docs-only descendants:

`565ba4092c4312c55e7e57a8c45e32f8997afd8d`

على هذا SHA:

- Quality Gate #885 / Run `35136617396` = SUCCESS.
- M04 Responsive #347 / Run `35136619472` = SUCCESS.
- M09 Release Readiness #207 / Run `35136619488` = FAILURE.

الـblocker الحالي هو M09 backend product regression الذي يبدأ قبل schema migration/bootstrap المطلوب، فتفشل اختبارات account lockout بسبب عدم وجود `account_lockout_states`. راجع `NEXT_CONVERSATION_PROMPT.md` وأحدث handoff للحالة الدقيقة.

## 3) خريطة المصادر التنفيذية حسب المجال

| المجال | المصدر التنفيذي الحالي | دور المصادر الأخرى |
|---|---|---|
| الحالة والاستئناف | live branch + `START_HERE_AR.md` + `docs/ops/RESUME_HERE.md` + `docs/ops/STATUS.md` + `docs/ops/progress.json` + `NEXT_CONVERSATION_PROMPT.md` + أحدث Master Continuity Handoff | الـhandoffs/checkpoints الأقدم chronology فقط. |
| سجل الفجوات | `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md` للfinding/root cause + أحدث execution/status overlay لحالة التنفيذ | لا يُعاد كتابة تاريخ التدقيق كلما تغير status. |
| خطة التصحيح | `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md` مع overrides والحالة التنفيذية الأحدث | الخطة لا تتقدم على live code/exact-SHA evidence. |
| اسم المنتج والهوية | `.agents/rules/00-himma-core.md` + manifests المعتمدة داخل `assets/` | دليل الهوية والمراجع الأصلية للشرح والتاريخ. |
| منطق المنتج | current code + tests + القرارات الفعالة في `docs/ops/DECISIONS.md` + specs الحالية | المواصفات القديمة لا تتجاوز كودًا/اختبارًا/قرارًا أحدث. |
| المحتوى التعليمي | `services/api/content_approval_contract_2026_09_08.py` + canonical compiler/release/publisher + executable release/projection tests | المصادر الأصلية تمد السياق التاريخي، ولا تتجاوز approvals/overrides الحالية. |
| publication/runtime content | canonical release/publisher → PostgreSQL runtime | seed/correction/projection scripts التاريخية ليست authority تلقائيًا. |
| Placement | `services/api/placement_scoring.py` + current tests/ADR الفعال | لا تعاد readiness gates تاريخية أُلغي اعتمادها. |
| Adaptation | `services/api/adaptation.py` / `adaptation_runtime.py` + canonical tests | Placement منفصل عن learning adaptation. |
| Completion/Promotion | `services/api/level_completion.py` + journey/reward consumers + tests | UI fields وحدها لا تثبت completion تاريخيًا. |
| التسجيل الصوتي والمراجعة | `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md` + current audio/review code + W1/W2 tests | Human Supervisor Review authority؛ machine analysis advisory. |
| Production ASR | `services/api/asr_governance.py` + `AUD-A03-008` boundary | env/config أو experimental code لا يعني production approval. |
| الأصول الصوتية | `assets/audio/HIMMA_AUDIO_V1/manifest.csv` + current tests/contracts | أرقام الحزم القديمة تاريخية. |
| الصور التعليمية | `assets/education/ASSET_MANIFEST.json` + `assets/education/developer/asset-map.json` + canonical media contracts/tests | الوثائق تشرح الاستخدام ولا تستبدل asset identity. |
| Media semantic role | canonical media contract + W4 owner/client approvals + final-release tests | tuples التاريخية inputs فقط إذا تجاوزها قرار أحدث معتمد. |
| W4 lexical media | `docs/ops/HIMMA_W4_OWNER_CLIENT_APPROVAL_2026-09-14.md` + current semantics/tests | **W4 CLOSED GREEN**؛ لا تعِد طلب الموافقة أو إعادة stale Sep-08 expectation. |
| المكافآت والشارات | `services/api/reward_catalog.py` + Reward API + asset manifests + W6 lifecycle E2E | لا hardcoded parallel reward map في Student/Admin. |
| تجربة الواجهة | current Next.js app + shared design/accessibility components + E2E | `reference/ui-prototype/` مرجع بصري فقط. |
| الأمن | current config/middleware + Security tests + Quality Gate | deployed-header verification خارج W6/A11-only. |
| الأداء | current services/query tests + W5 acceptance | audit finding يشرح المشكلة؛ الاختبار يثبت الإغلاق. |
| الوصولية | current components + Axe/keyboard/RTL/reduced-motion/contrast/progress tests | automated portion منفذ؛ manual human screen-reader غير مدعى. |
| CI/release readiness | `.github/workflows/ci.yml`, `.github/workflows/m09-release-readiness.yml`, `apps/web/tests/TEST_OWNERSHIP.md` + exact-SHA run evidence | `browser-flow.spec.ts` legacy/debug وليس release evidence. |

## 4) العقود الأكاديمية الحالية

- Placement: `<50 → L1`, `50..<80 → L2`, `80..100 → L3`.
- Learning activity: `>=80` success, `70..<80` guided retry, `<70` targeted reinforcement.
- L1/L2 early promotion يمكن بعد >=6 Core عند استيفاء mastery/critical evidence الكانونية.
- L3 يتطلب 10 Core.
- No automatic demotion.
- Manual override لا يعني completion ولا badge.
- latest three valid active-session Core evidences تستخدم 50/30/20 weighting.
- pending/uploaded learning audio محايد أكاديميًا حتى human review حيث يتطلب العقد ذلك.
- rerecord append-only والقديم immutable، والـlatest submission هو active.

## 5) المحتوى الكانوني الحالي

Approval version:

`HIMMA-CONTENT-APPROVAL-2026-09-08`

Canonical runtime:

- 30 Pretest
- 30 Posttest
- 30 Core
- 35 Reinforcement
- total 125 items
- 44 skills

المسار المعتمد:

`approved/versioned contracts → canonical compile/release → deterministic publication → PostgreSQL runtime → structured APIs → deterministic UI`

يُمنع تحويل runtime patch/overlay أو seeder تاريخي إلى owner جديد للحقيقة.

## 6) العقود الصوتية الحالية

- لا Student Audio Skip.
- latest AudioSubmission active؛ القديم immutable.
- rerecord append-only.
- Human Supervisor Review هي السلطة الأكاديمية الحالية.
- SpeechAnalysis/ASR الآلي advisory فقط.
- Production ASR غير معتمد؛ `AUD-A03-008` يبقى blocked حتى provider/calibration/privacy/cost/governance approval.

## 7) W6 acceptance ownership

أثبت Quality Gate #885 على exact functional SHA الحالي:

- Security + Frontend + Backend + Integration/Playwright.
- reward lifecycle E2E.
- deterministic same-student pretest/posttest journey.
- responsive matrices including 320/360/390/430/768/Desktop.
- Axe/keyboard/RTL/reduced-motion/contrast/progress semantics.
- test ownership contract.

لا تعاد إصلاحات W6 القديمة إلا بدليل regression جديد.

W6 **ليست GREEN بعد** لأن `AUD-A08-003` يحتاج full M09 Release Readiness إلى النهاية، بما فيه backend regression + canonical/migration/readiness + release Playwright + PostgreSQL backup/restore + object-storage backup/restore على نفس exact SHA مع Quality Gate.

## 8) الحدود الخارجية/اللاحقة

- `AUD-A03-008` Production ASR: external approval blocked.
- `AUD-SEC-006` deployed-header verification: A11/later only.
- `AUD-A11Y-005` manual human screen-reader verification: غير منفذ وغير مدعى.
- `AUD-GIT-001` final merge/release-branch governance: خارج current no-final-merge boundary.
- Deploy/Railway/Production/A11: غير مصرح بها ضمن A10 الحالي.

## 9) قاعدة التعارض والتحديث

عند وجود تعارض:

1. Fetch live HEAD أولًا.
2. حدد owner الصحيح للحقيقة من الترتيب أعلاه.
3. فرّق بين functional/tested SHA وبين docs-only descendants.
4. أصلح root cause في المسار الصحيح، لا الاختبار لإخفاء المشكلة.
5. احتفظ بالمرجع التاريخي بدل حذفه، لكن حدّث current status overlays/entrypoints حتى لا يعيد جلسة جديدة إلى نقطة قديمة.
6. لا `skip`/`xfail`/weaken ولا runtime repair overlay بدل إصلاح السبب.
7. لا PASS/CLOSED بلا exact-SHA evidence عندما تكون البوابة executable.

## 10) Stop rule الحالي

أكمل فقط W6 final readiness.

عندما ينجح **Quality Gate كامل + M09 Release Readiness كامل على نفس exact SHA**، حدّث W6 closure/STATUS/progress/gap overlay/continuity docs، ثم **STOP**.

لا تبدأ A11 ولا deploy ولا final merge دون تكليف صريح جديد.