# منصة هِمّة — Master Continuity Handoff

**الإصدار:** 2026-09-12 — A10/W3 Active  
**المستودع:** `7eaur/himma-`  
**فرع التنفيذ:** `audit/comprehensive-repository-review-2026-09-10`  
**الحالة:** `A00–A09 CLOSED — W1 GREEN — W2 GREEN — W3 ACTIVE — RUN #833 QUEUED — NO MERGE / NO DEPLOY`

هذا هو مرجع الاستكمال الرئيسي. اجلب HEAD الحالي دائمًا قبل العمل، لأن documentation commits قد تكون بعد آخر code-bearing SHA.

## Source of Truth

`repository code + migrations + executable tests/CI + canonical content contracts`

المعمارية الأكاديمية الحالية:
`approved/versioned source → deterministic structured projection → PostgreSQL runtime → structured API → deterministic renderer`

Canonical/runtime: 125 إجمالي، Pretest 30، Posttest 30، Learning 65، Reinforcement 35، Skills 44، projection=`structured_db_runtime_v1`.

ثوابت أكاديمية مختصرة:
- placement: `<50` L1، `50..<80` L2، `80..100` L3.
- activity: `>=80` success، `70..<80` guided retry، `<70` reinforcement.
- L1/L2 early promotion يبدأ من 6 Core مع mastery/critical/blocker gates.
- L3 يحتاج 10 Core.
- `current_level` pointer وليس completion evidence.
- manual override لا يعني completion أو badge.
- pending/uploaded learning audio محايد أكاديميًا؛ irreversible boundary ينتظر unresolved audio.
- rerecord append-only، latest submission هو active state، Human Supervisor Review هو السلطة الأكاديمية.
- Production ASR غير معتمد.

## Closed history

### W1 — CLOSED GREEN
SHA `ea132c9afbe152d0afa5ae581c058ce3248a0c48`, Run #813 / ID `34467329988`.

### W2 — CLOSED GREEN
SHA `77ac72174a9e21163f6341ea8e0fcc172269eac3`, Run #822 / ID `34548388760`.

لا تعِد W1/W2 ولا A00–A09.

## W3 — ACTIVE

### آخر gate مكتمل
Run #832 / ID `34707136263` على exact SHA `82e0bd216ab3d4f3af9d5737b5e29d2102254843` = **SUCCESS**.

هذا أغلق blocker السابق في `vertical-slice.spec.ts` الناتج عن locator ambiguity (`5 من 10` مقابل `5 من 10 أساسي`). لم يتم تغيير حقيقة المنتج أو تخفيف assertion؛ تم جعل selector exact.

### الـbatch الحالي — AUD-A11Y-001

تم تنفيذ global reduced-motion policy:
- `apps/web/src/app/reduced-motion.css`
- `apps/web/src/app/layout.tsx`

العقد:
- `prefers-reduced-motion: reduce` يعطل smooth scrolling.
- decorative animations/transitions تصبح شبه فورية وغير متكررة.
- scroll-reveal content يبقى ظاهرًا فورًا ولا يختفي بسبب تعطيل الحركة.
- لا تغيير في content/state/academic logic.

Code commits:
- `b16a37742b7563f8f17d17b72c1a66ed37a62af8`
- `79f154f9a3cdee51a713459790d1695aba08d6d7`

Latest code-bearing SHA: `79f154f9a3cdee51a713459790d1695aba08d6d7`.

`stage/a10-w3-ci` يشير إلى هذا الـSHA للتحقق فقط.

Quality Gate الحالي:
- Run #833
- Run ID `34708600408`
- exact SHA `79f154f9a3cdee51a713459790d1695aba08d6d7`
- الحالة عند آخر checkpoint: `QUEUED`.

## أول إجراء للمهمة التالية

اقرأ أولًا:
`docs/maintenance/HIMMA_A10_W3_AUTOMATION_CHECKPOINT_2026-09-12_RUN833_AR.md`

ثم افحص Run #833 قبل أي تعديل:
- QUEUED/IN_PROGRESS → لا batch موازية.
- FAIL → أصلح أول failure حقيقي من root cause، لا تضعف الاختبارات.
- SUCCESS → وثّق exact-SHA evidence، أغلق AUD-A11Y-001، ثم أكمل أول W3 gap غير مغلق فقط.

## W3 المتبقي

ما لم يثبت إغلاقه:
- AUD-A04-001 AdminUI/presentation unification.
- AUD-A04-002 partial-source failure/retry regressions.
- AUD-A04-003 canonical Journey UI scenarios.
- AUD-A04-005 viewport matrix 320/360/390/430/768/Desktop.
- AUD-A04-006 final keyboard/dialog regression.
- AUD-A04-007 Settings shared tokens/presentation verification.
- AUD-A04-008 Student Detail → filtered audio review context E2E.
- AUD-PERF-004 إزالة runtime Google Fonts dependency واعتماد local/build-time typography.
- AUD-A11Y-002 semantic accessible colors/contrast.
- AUD-A11Y-003 progressbar semantics.
- cross-device scenario integrity.
- final exact-SHA W3 Green gate.

W3 لا تصبح Green حتى تغلق البنود المطلوبة ويصبح Security + Frontend + Backend + Integration/Playwright PASS على exact SHA واحد.

## بعد W3

W4 = Rewards / Badges / Media semantics.  
W5 = Historical cleanup / Performance / Test ownership مع no destructive cleanup بلا dependency proof.  
W6 = Final exact-SHA product gate ويشمل Security, Frontend, Backend, migrations/drift/seed/canonical, Integration/Playwright, responsive/accessibility, reward lifecycle/full student journey.

**A11 / Deploy / Railway / Production / final merge خارج هذه الجدولة وممنوعة.**

## قيود ثابتة

- لا Docker.
- لا fake ASR.
- لا Temporary Audio Skip.
- لا حذف academic/audio/reward history.
- Speech/Pronunciation Lab branches = research only / EXCLUDE FROM MERGE.
- `deployment/platform-sandbox` = reference only.
- لا PASS claim دون exact-SHA evidence.
- لا تغيّر الاختبارات لإخفاء bug حقيقي.
- إذا CI/batch سابق ما يزال active، لا تنشئ مسار عمل متعارضًا.
