# منصة هِمّة — A10 / W3 Execution Checkpoint

**التاريخ:** 2026-09-12  
**المستودع:** `7eaur/himma-`  
**فرع التنفيذ:** `audit/comprehensive-repository-review-2026-09-10`  
**الموجة:** `A10/W3 — Admin / Student UX / Accessibility / Web Reliability`  
**الحالة:** `ACTIVE — CI RED — NO MERGE / NO DEPLOY`

> هذا هو checkpoint العملي الحالي. لا تُعِد A00–A09 ولا W1/W2. اجلب HEAD الحالي أولًا لأن commits توثيقية أو إصلاحات لاحقة قد تكون فوق نقطة الكود المذكورة هنا.

---

## 1. آخر Code-bearing checkpoint قبل التوثيق

`3962d101b2c1ba4c5294235dfac797687209cbfb`

Commit: `fix(admin): align audio review with shared admin component contracts`

هذا SHA متقدم عن W2 Green SHA `77ac72174a9e21163f6341ea8e0fcc172269eac3` بـ19 commits تخص W3. commits التوثيق اللاحقة تحرك HEAD؛ لذلك `3962...` هو code-bearing checkpoint وليس بالضرورة branch HEAD الحالي.

---

## 2. CI الحالي لـ W3 — Exact evidence

Verification helper: `stage/a10-w3-ci` — CI pointer فقط ولا يُدمج.

- Workflow: `Himma CI — Quality Gate`
- Run number: `829`
- Run ID: `34703574228`
- Exact SHA: `3962d101b2c1ba4c5294235dfac797687209cbfb`

النتيجة النهائية:

- **Security: PASS**.
- **Backend: PASS**، بما في ذلك PostgreSQL native setup، canonical validation، Alembic upgrade→downgrade→upgrade، model drift، seed idempotency وfull backend tests.
- **Frontend TypeScript: PASS**.
- **Frontend ESLint: PASS**.
- **Frontend unit tests: FAIL** — اختبار واحد في BFF cache policy.
- Frontend Build: skipped بعد فشل unit test.
- Integration / Playwright: skipped لأن Frontend لم تنجح.

إذن **W3 ليست Green** ولا يوجد release claim.

---

## 3. أول Root Cause يجب إصلاحه عند الاستكمال

الاختبار الفاشل: `apps/web/src/app/api/[...path]/route.test.ts`.

الحالة: path تحت `media/`، GET، upstream successful، وupstream يصرح `Cache-Control: private, no-store`.

Expected: `private, no-store`  
Actual: `public, max-age=86400`

السبب في `apps/web/src/app/api/[...path]/cachePolicy.ts`: الدالة `responseCacheControl()` تسقط إلى public fallback حتى عندما upstream منع التخزين صراحة.

### Root fix الصحيح

لا تغيّر الاختبار ليقبل السلوك الخطأ:

1. أي route ليست approved-media GET/HEAD، أو response غير ناجحة، أو تحمل Set-Cookie → `private, no-store`.
2. إذا upstream Cache-Control موجود ويحتوي `private` أو `no-store` → احترم المنع وأرجع `private, no-store`.
3. إذا upstream policy صريح وآمن `public` ولا يحتوي منعًا → مرره.
4. `public, max-age=86400` fallback يستخدم فقط عند غياب upstream cache header في approved successful media GET/HEAD دون Set-Cookie.
5. Commit root fix على فرع audit.
6. Move `stage/a10-w3-ci` إلى SHA الجديد.
7. شغّل full Quality Gate exact SHA، ولا تستخدم rerun قديم كدليل SHA جديد.

هذه هي **أول مهمة تنفيذية** للمحادثة الجديدة إذا لم يوجد commit أحدث أصلحها.

---

## 4. ما نُفذ في W3 حتى نقطة التوقف

### AUD-A04-006 — Shared accessible dialog lifecycle

أضيف `apps/web/src/hooks/useAccessibleDialog.ts` مع initial focus، Tab/Shift+Tab trap، Escape close، return focus، وbody scroll lock، مع `apps/web/src/hooks/useAccessibleDialog.test.tsx`. Admin mobile menu يستخدمه مع `role="dialog"`, `aria-modal="true"`, trigger semantics وlabels.

### AUD-A04-007 — Settings tabs semantics

`apps/web/src/app/admin/(dashboard)/settings/page.tsx` أصبح يملك tablist/tab/tabpanel roles، aria-selected/controls/labelledby، roving tabIndex، وArrowLeft/ArrowRight/Home/End keyboard navigation. يبقى توحيد presentation/tokens النهائي ضمن W3.

### AUD-A04-003 — Canonical Journey للمشرف

أضيف `services/api/researcher_journey.py` مع `GET /researcher/students/{student_id}/journey` ويعتمد `journey.build_journey_summary()` نفسه؛ Admin لا يعيد استنتاج completion من `current_level`. الاختبار: `services/api/test_researcher_journey_w3.py`.

### AUD-A04-002 / A04-003 — Student Detail truth states

`apps/web/src/app/admin/(dashboard)/students/[id]/page.tsx` أصبح يستهلك canonical Journey projection، ويفرق بين loading/loaded/error لـJourney/history/rewards، ولا يحول failure إلى empty/zero مضلل، ويعرض per-level state من canonical source، ويحدث Journey بعد mutations ذات الصلة.

### AUD-A04-008 — Student-context-preserving Audio Review

Backend `services/api/review.py`: `GET /pending-audio` يقبل optional `student_id` كفلتر عرض للمشرف فقط دون تغيير review eligibility أو academic state. Frontend `audio-review/page.tsx` يحافظ على student context ويدعم filtered view والعودة لعرض الكل. Commit `3962...` أصلح contracts الفعلية لـshared Admin components؛ TypeScript وESLint نجحا في run #829.

### AUD-PERF-001 — BFF cache boundary

أضيف `cachePolicy.ts` و`route.test.ts` ورُبطت policy بـ`route.ts`. الهدف: approved media يمكن caching بشكل آمن، بينما private JSON وSet-Cookie يبقيان no-store. التنفيذ غير مغلق بسبب bug القسم 3.

---

## 5. W3 — الأعمال المتبقية كاملًا قبل Green

- **AUD-A04-001:** استكمال Admin presentation unification على shared AdminUI/tokens؛ local CSS فقط للأنماط الفريدة.
- **AUD-A04-002:** تثبيت tests لـhistory/rewards/journey partial failures وretry، ومنع zero/empty misleading state.
- **AUD-A04-003:** verify canonical Journey rendering للـoverride 1→3، skipped، early promotion، active/ready/locked/completed.
- **AUD-A04-005:** responsive Student Detail matrix عند 320/360/390/430/768/Desktop مع no-overflow/touch/forms/tabs/Arabic wrapping/images/progress.
- **AUD-A04-006:** final keyboard-only dialog regression على exact gate.
- **AUD-A04-007:** Settings shared tokens + final ARIA/keyboard verification.
- **AUD-A04-008:** Student Detail → recordings → filtered review → pending/graded/rerecord → back/context flow.
- **AUD-PERF-001:** إصلاح BFF cache bug الحالي ثم rerun.
- **AUD-PERF-004:** إزالة runtime Google Fonts dependency من `globals.css` واعتماد local/build-time typography strategy مع layout stability.
- **AUD-A11Y-001:** global `prefers-reduced-motion` policy بدون تغيير content/state logic.
- **AUD-A11Y-002:** semantic accessible text/action colors مع الحفاظ على brand colors.
- **AUD-A11Y-003:** progress الفعلي يملك `role="progressbar"` + min/max/now/label، ولا يوجد progressbar زائف للحالات النصية.
- **Scenario integrity:** skipped ≠ completed؛ manual override ≠ completion/badge؛ pending learning audio لا يصنع false completion ولا يجمد same-level support؛ irreversible promotion/L3 completion ينتظر unresolved audio؛ rerecord لا يمسح history؛ partial failure لا يصبح success/zero؛ mobile/keyboard لا يغيران الحقيقة الأكاديمية.

---

## 6. W4 — الملاحظات المثبتة من مراجعة الشارات/النجوم/الصور

بعد W3 Green فقط انتقل W4.

### Reward / Badge gaps

- `AUD-BADGE-001`: Student Home يجلب rewards لكنه لا يعرض canonical badge assets كاملًا.
- `AUD-BADGE-002`: Admin badge presentation ما زال نصيًا أكثر من shared visual catalog.
- `AUD-BADGE-003`: دمج approved SVG assets مع stable IDs/metadata.
- `AUD-BADGE-004`: L3 backend label الحالي `قارئ متميز` مقابل approved `نجم الفهم`؛ الحل migration/history-compatible.
- `AUD-BADGE-005`: completion owner canonical من W1؛ لا تعيد قاعدة badge مستقلة 10/10.
- `AUD-BADGE-007`: reward API failure يجب أن يظهر unavailable/error لا zero.
- `AUD-BADGE-008`: Reward API يحتاج catalog/version/asset identity مستقرة.

Approved mapping:

- `BDG-01` نجمة واحدة.
- `BDG-02` نجمتان.
- `BDG-03` ثلاث نجوم.
- `BDG-04` مستكشف الحروف.
- `BDG-05` بطل الكلمات.
- `BDG-06` نجم الفهم.

### Star logic gap

الحالي: 3 بلا structured retry/hint، 2 مع hint بلا retry، 1 مع structured retry. الفجوة: audio rerecord لا يدخل بوضوح في `_stars_for_attempt()`؛ يمكن نظريًا منح 3 نجوم بعد rerecord.

Root fix W4: rerecord الحقيقي يدخل effort/retry semantics؛ history append-only يبقى؛ pending/ungraded audio لا يمنح reward مبكرًا؛ unique RewardEvent/idempotency يبقى؛ أضف regression لتسلسل/تراكم النجوم وعدم duplicate award.

### Media semantics

`AUD-MEDIA-002` يحتاج Academic Review؛ لا تغير lexical stimulus assets آليًا. تحقق من no distortion، responsive images، semantic roles، meaningful alt للدلالي وempty alt للزخرفي.

---

## 7. W5 / W6 / A11

### W5 — Historical cleanup / Performance / Test ownership

runtime service generations classification؛ old seeds/repair scripts classification؛ legacy 105-world test ownership منفصل عن canonical 125؛ Reward history cascade risk قبل cleanup/reset؛ unused/duplicate media لا يُحذف بلا dependency/runtime proof؛ researcher students N+1؛ notifications GET mutation؛ duplicate `/admin/account` فقط بعد proof.

### W6 — Final exact-SHA gate

مطلوب SHA واحد ينجح فيه Security + TS/Lint/Unit/Build + Backend + migrations/drift/seed/canonical + Integration/Playwright + responsive/accessibility + full reward lifecycle E2E.

### A11 — Deployment

Blocked until W6 Green. لا Docker ولا deploy/Railway قبل ذلك.

---

## 8. External decisions المفتوحة

Production ASR provider/model/calibration/privacy/cost/governance؛ intervention/session duration قبل study activation؛ child-recording retention policy؛ domain/hosting/deployment settings؛ supervising organization details/logo؛ production credential rotation إذا ثبت historical exposure. لا تخترع أي قرار منها من الكود.

---

## 9. بروتوكول المحادثة الجديدة

1. Fetch HEAD للفرع audit.
2. اقرأ `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-12_A10_W3_ACTIVE_AR.md` ثم هذا checkpoint وSTATUS/progress/Gap Register.
3. لا تعِد A00–A09 أو W1/W2.
4. تحقق هل يوجد code SHA بعد `3962...` أصلح BFF cache bug.
5. إن لم يوجد، أصلح `cachePolicy.ts` من root cause في القسم 3.
6. Move `stage/a10-w3-ci` إلى SHA الجديد وشغّل full Quality Gate.
7. لا تقل W3 Green إلا عند Security+Frontend+Backend+Integration/Playwright PASS على exact SHA نفسه.
8. أكمل كل W3، ثم W4، W5، W6.
9. لا Merge/Deploy/Railway/Docker قبل الحدود الموثقة.
