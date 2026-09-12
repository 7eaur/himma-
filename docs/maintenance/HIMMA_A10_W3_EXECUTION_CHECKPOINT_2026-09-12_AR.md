# منصة هِمّة — A10 / W3 Execution Checkpoint

**التاريخ:** 2026-09-12  
**المستودع:** `7eaur/himma-`  
**فرع التنفيذ:** `audit/comprehensive-repository-review-2026-09-10`  
**الموجة:** `A10/W3 — Admin / Student UX / Accessibility / Web Reliability`  
**الحالة:** `ACTIVE — NOT GREEN — NO MERGE / NO DEPLOY`  

> هذا checkpoint هو نقطة الاستكمال العملية لـ W3. لا تُعِد A00–A09 ولا W1/W2. ابدأ دائمًا بجلب HEAD الحالي، ثم قارن بما هو موثق هنا لأن commits توثيقية أو إصلاحات لاحقة قد تكون أضيفت.

---

## 1. نقطة الكود الحالية قبل commits التوثيق

آخر code-bearing SHA مؤكد عند إنشاء هذا checkpoint:

`3962d101b2c1ba4c5294235dfac797687209cbfb`

Commit:

`fix(admin): align audio review with shared admin component contracts`

الفرع أصبح متقدمًا عن W2 Green SHA (`77ac721...`) بمقدار 19 commits، مع تغييرات W3 في Admin, BFF, accessibility, journey projection, review filtering والاختبارات.

> commits التوثيق التي تنشئ هذا الملف ستجعل HEAD أعلى من SHA أعلاه؛ لذلك SHA `3962...` هو **code-bearing checkpoint** وليس بالضرورة final branch HEAD بعد التوثيق.

---

## 2. CI الحالي لـ W3

Verification helper branch:

`stage/a10-w3-ci`

هذه branch مؤقتة للتحقق فقط ولا تُدمج.

تم تحريكها إلى exact code SHA:

`3962d101b2c1ba4c5294235dfac797687209cbfb`

Quality Gate:

- Workflow: `Himma CI — Quality Gate`
- Run number: `829`
- Run ID: `34703574228`
- Exact SHA: `3962d101b2c1ba4c5294235dfac797687209cbfb`

الحالة عند كتابة هذا checkpoint:

- Security: **PASS**.
- Frontend TypeScript: **PASS**.
- Frontend ESLint: **PASS**.
- Frontend unit tests: **FAIL**.
- Frontend build: skipped بسبب فشل unit test.
- Backend: كان ما يزال داخل full backend tests في آخر poll؛ لا يوجد claim نهائي له داخل هذا checkpoint حتى اكتمال run.
- Integration/Playwright: لن يكون Green في هذا run لأن Frontend فشل.

**W3 ليست Green.**

---

## 3. الفشل الحالي المحدد Root Cause

الاختبار الفاشل:

`apps/web/src/app/api/[...path]/route.test.ts`

Scenario:

- approved media-looking path
- GET
- upstream response successful
- upstream explicitly returns `Cache-Control: private, no-store`

Expected:

`private, no-store`

Current implementation returned:

`public, max-age=86400`

Root cause في:

`apps/web/src/app/api/[...path]/cachePolicy.ts`

المنطق الحالي يسمح fallback public عند عدم تحقق شرط "explicitly safe public"، حتى لو كان upstream قد صرّح صراحة `private/no-store`.

### الإصلاح الصحيح التالي

لا تُضعف الاختبار.

يجب تعديل `responseCacheControl()` بحيث:

1. أي response غير media GET/HEAD أو غير successful أو يحمل Set-Cookie → `private, no-store`.
2. إذا كان upstream Cache-Control موجودًا ويحتوي `private` أو `no-store` → **احترام الحظر** وإرجاع `private, no-store`.
3. إذا كان upstream policy موجودًا وهو explicit safe `public` → يمكن تمريره.
4. fallback `public, max-age=86400` يستخدم فقط لقراءة media approved الناجحة عندما يكون upstream cache header **غائبًا**، وليس عندما يمنع upstream التخزين صراحة.
5. بعد الإصلاح: commit على فرع audit، تحريك `stage/a10-w3-ci` إلى SHA الجديد، وتشغيل Quality Gate كامل exact-SHA.

هذه هي **أول مهمة تنفيذية** للمحادثة الجديدة إذا لم يكن قد أُضيف إصلاح لاحق.

---

## 4. ما تم تنفيذه فعليًا داخل W3 حتى الآن

### 4.1 Shared accessible dialog lifecycle — AUD-A04-006

أضيف:

`apps/web/src/hooks/useAccessibleDialog.ts`

ويغطي:

- نقل focus داخل dialog عند الفتح.
- Tab / Shift+Tab focus trap.
- Escape close.
- إعادة focus للزر الذي فتح dialog.
- body scroll lock أثناء dialog.

واختبار:

`apps/web/src/hooks/useAccessibleDialog.test.tsx`

Admin mobile menu يستخدم هذا الـhook فعليًا في:

`apps/web/src/app/admin/(dashboard)/layout.tsx`

مع:

- `role="dialog"`
- `aria-modal="true"`
- label واضح
- trigger مع `aria-haspopup="dialog"` و`aria-expanded`.

### 4.2 Settings keyboard/ARIA tabs — AUD-A04-007

`apps/web/src/app/admin/(dashboard)/settings/page.tsx`

تم إضافة:

- `role="tablist"`
- `role="tab"`
- `aria-selected`
- `aria-controls`
- roving `tabIndex`
- ArrowLeft / ArrowRight
- Home / End
- `role="tabpanel"` + `aria-labelledby`.

ما زال توحيد presentation/tokens الكامل مع AdminUI جزءًا من W3 ولا يعتبر مغلقًا لمجرد ARIA tabs.

### 4.3 Canonical supervisor Journey — AUD-A04-003 W3 side

أضيف:

`services/api/researcher_journey.py`

Endpoint:

`GET /researcher/students/{student_id}/journey`

هذا endpoint لا يختلق منطقًا أكاديميًا جديدًا؛ يفوض إلى:

`journey.build_journey_summary`

حتى تعرض لوحة المشرف نفس canonical Journey ولا تستنتج أن `level < current_level` يعني completed.

اختبار:

`services/api/test_researcher_journey_w3.py`

### 4.4 Student Detail source truth — AUD-A04-002 / A04-003

في:

`apps/web/src/app/admin/(dashboard)/students/[id]/page.tsx`

تم:

- استهلاك canonical Journey projection.
- فصل حالة history/rewards/journey إلى loading / loaded / error.
- منع تفسير failure كقائمة فارغة أو `0` مضلل.
- refresh للـJourney بعد mutations التي قد تغير المسار.
- عرض per-level states من source canonical بدل inference من current-level pointer.

### 4.5 Student-context-preserving audio review — AUD-A04-008

Backend:

`services/api/review.py`

`GET /pending-audio` يدعم optional:

`student_id`

الفلتر supervisor view فقط ولا يغير eligibility أو academic state.

Frontend:

`apps/web/src/app/admin/(dashboard)/audio-review/page.tsx`

تم الحفاظ على سياق الطالب عند الانتقال من ملفه إلى قائمة التسجيلات، مع مسار لإزالة الفلتر والعودة لعرض الجميع.

آخر commit `3962...` أصلح توافق الصفحة مع contracts الفعلية لـ shared Admin components، ولذلك TypeScript وESLint أصبحا PASS في run #829.

### 4.6 BFF media/private cache boundary — AUD-PERF-001

أضيف:

`apps/web/src/app/api/[...path]/cachePolicy.ts`

واختبار:

`apps/web/src/app/api/[...path]/route.test.ts`

وتم ربطه بـ:

`apps/web/src/app/api/[...path]/route.ts`

المقصد الصحيح:

- approved immutable media يمكن أن تستفيد من public cache.
- private student/supervisor JSON يبقى no-store.
- Set-Cookie يبقى private.

لكن implementation لا يزال يحتوي bug موضح في القسم 3، ولذلك هذا البند **غير مغلق بعد**.

---

## 5. W3 — المتبقي كاملًا قبل الإغلاق

### AUD-A04-001 — Admin presentation unification

- استكمال توحيد Student Details / Settings / Account وما يتبقى على shared AdminUI/tokens.
- page-local CSS يبقى فقط للأنماط الفريدة فعليًا.
- لا إعادة تصميم عشوائي؛ الهدف consistency + maintainability + responsive behavior.

### AUD-A04-002 — Explicit partial-source states

- الموجود في Student Detail يحتاج final exact-SHA verification.
- أضف/ثبت tests لحالات history 500 / rewards 500 / journey 500 / retry وعدم تحويلها إلى empty/zero misleading UI.

### AUD-A04-003 — Canonical Journey render

- implementation موجود؛ يحتاج final UI + API regression وexact-SHA verification.
- scenarios: override 1→3، early promotion، skipped level، active level، completed level.

### AUD-A04-005 — Deterministic responsive Student Detail

إضافة/تثبيت viewport matrix:

- 320
- 360
- 390
- 430
- 768
- Desktop

التحقق من:

- no horizontal overflow.
- touch targets.
- tabs/actions/forms.
- long Arabic text wrapping.
- cards/images/progress.

### AUD-A04-006 — Accessible dialog

implementation موجود ويحتاج دمجه في final W3 exact-green gate، مع keyboard-only regression.

### AUD-A04-007 — Settings tabs/Admin tokens

ARIA/keyboard موجودة؛ استكمال shared presentation/tokens وإغلاق tests.

### AUD-A04-008 — Student filtered review

implementation موجود؛ أضف/ثبت flow test:

Student Detail → recordings → filtered review → pending/graded/rerecord states → back navigation/context.

### AUD-PERF-001 — BFF media cache

**الحاجز الحالي.** أصلح explicit upstream private/no-store كما في القسم 3 ثم rerun.

### AUD-PERF-004 — Runtime Google Fonts dependency

`globals.css` لا يزال يحتوي runtime Google Fonts import.

المطلوب:

- local/build-time typography strategy.
- الحفاظ على Arabic rendering والهوية.
- عدم الاعتماد على network runtime لتحميل الخط الأساسي.
- اختبار offline/network failure + layout stability.

### AUD-A11Y-001 — Reduced motion

اعتماد global policy لـ `prefers-reduced-motion`:

- تعطيل decorative motion.
- عدم فرض smooth scrolling.
- عدم إخفاء محتوى أو تغيير منطق التطبيق.

### AUD-A11Y-002 — Accessible semantic colors

- لا تغيّر brand palette بلا داعٍ.
- أضف semantic text/action variants ذات contrast مناسب.
- اختبر الاستخدام الفعلي، لا hex منفصل فقط.

### AUD-A11Y-003 — Progress semantics

- progress visual يجب أن يملك `role="progressbar"` عند كونه تقدمًا فعليًا.
- `aria-valuemin/max/now` واسم مفهوم.
- الحالات النصية غير الرقمية لا تُجبر على progressbar زائف.

### W3 scenario integrity pass

قبل الإغلاق راجع منطقيًا وE2E:

- skipped ≠ completed.
- manual override ≠ academic completion.
- pending audio لا يصنع false completion.
- same-level learning لا يتجمد بسبب pending learning audio.
- irreversible promotion/L3 completion ينتظر unresolved audio.
- rerecord لا يمسح history.
- partial API failure لا يتحول إلى success/zero.
- mobile/keyboard paths لا تختلف أكاديميًا عن desktop.

---

## 6. W4 — المهام التي تم تثبيتها من مراجعة الشارات/النجوم/الصور

بعد W3 Green انتقل إلى W4، ولا تخلطها مع W3 لإخفاء status الحالي.

### Reward / Badge Catalog

- `AUD-BADGE-001`: Student Home يجلب badges لكنه لا يعرض canonical badge assets كاملًا.
- `AUD-BADGE-002`: Admin Student Detail يعرض badge كنص أكثر من كونه shared reward presentation.
- `AUD-BADGE-003`: دمج approved badge assets في canonical runtime catalog.
- `AUD-BADGE-004`: توحيد L3 الحالي `قارئ متميز` مع approved catalog `نجم الفهم` بطريقة migration/history-compatible.
- `AUD-BADGE-005`: completion owner أصبح canonical في W1؛ W4 يضمن أن presentation/catalog يستخدمه ولا يعيد بناء قواعد 10/10 منفصلة.
- `AUD-BADGE-007`: reward API failure يجب أن يظهر unavailable/error وليس `0` نجوم مضلل.
- `AUD-BADGE-008`: reward API يحتاج stable catalog identity/version + asset identity.

Approved visual mapping المطلوب المحافظة عليه:

- `BDG-01` = نجمة واحدة.
- `BDG-02` = نجمتان.
- `BDG-03` = ثلاث نجوم.
- `BDG-04` = مستكشف الحروف.
- `BDG-05` = بطل الكلمات.
- `BDG-06` = نجم الفهم.

لا تولد شارات بديلة إذا كانت الأصول المعتمدة موجودة.

### Star logic gap المكتشف

منطق النجوم الحالي:

- 3: completed without help/retry.
- 2: hint used without retry.
- 1: completed after retries.

لكن `_stars_for_attempt` يعتمد حاليًا على structured step retries/hints، وقد لا يعتبر **audio rerecord** retry. لذلك يمكن نظريًا أن يعاد التسجيل ثم يحصل الطالب على 3 نجوم.

Root fix المطلوب في W4:

- ربط latest/append-only audio submission history بمنطق reward effort بدون كسر academic evidence.
- rerecord الفعلي يجب أن يدخل retry semantics.
- pending/ungraded audio لا يمنح reward مبكرًا.
- unique RewardEvent يظل idempotent.
- إضافة regression للسلسلة التراكمية، مثل 3 ثم +2 ثم +1 = 6، بدون duplicate event.

### Media semantics

`AUD-MEDIA-002` يحتاج **Academic Review** قبل تغيير الأصول؛ لا تستبدل صورة لمجرد أن validator أو مبرمج يظنها أقرب.

الصور يجب أن تحافظ على:

- semantic role.
- no distortion.
- responsive sizing.
- meaningful alt عندما الصورة تحمل معلومة، وalt فارغ للزخرفي.

---

## 7. W5 / W6 / A11 بعد W4

### W5 — Historical cleanup / Performance / Test ownership

يشمل:

- BE runtime ownership generations وتصنيف القديم قبل الحذف.
- old seeds/repair layers: migration/test/dead classification فقط بعد dependency proof.
- legacy 105-world test ownership منفصل عن canonical 125.
- Student list N+1 performance.
- notification GET mutation/polling contract.
- duplicate `/admin/account` بعد proof.
- Reward history cascade risk قبل أي destructive cleanup.
- unused/duplicate media لا يُحذف لمجرد أنه غير referenced نصيًا.

### W6 — Final exact-SHA gates

لا إغلاق للمشروع قبل:

- full Security.
- Frontend TS/Lint/Unit/Build.
- Backend full tests.
- migrations/drift/seed/canonical gates.
- Integration/Playwright.
- deterministic responsive/accessibility scenarios.
- reward award→asset→Student/Admin→refresh/idempotency E2E.

### A11 — Deployment/Railway

Blocked until W6 Green.

لا Docker، ولا deploy قبل الإذن وحدود release.

---

## 8. External decisions المفتوحة وليست bugs محلية

- Production ASR provider/model/calibration/privacy/cost/governance.
- intervention/session duration قبل study activation.
- child-recording retention policy قبل real-child production data.
- domain/hosting/deployment settings.
- supervising organization details/logo قبل final report signoff.
- production credential rotation إذا وُجد تاريخ exposure.

لا تخترع قرارًا لهذه العناصر من الكود.

---

## 9. بروتوكول الاستكمال للمحادثة الجديدة

ابدأ بالترتيب:

1. Fetch HEAD لـ `audit/comprehensive-repository-review-2026-09-10`.
2. اقرأ:
   - `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-12_A10_W3_ACTIVE_AR.md`
   - هذا checkpoint.
   - `docs/ops/STATUS.md`
   - `docs/ops/progress.json`
   - `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
3. لا تعِد A00–A09.
4. لا تعِد W1/W2؛ كلاهما exact-green.
5. تحقق هل يوجد commit بعد `3962...` أصلح BFF cache failure.
6. إذا لم يوجد: أصلح `cachePolicy.ts` من root cause كما في القسم 3.
7. انقل helper `stage/a10-w3-ci` إلى code SHA الجديد وشغل full Quality Gate.
8. لا تقل W3 Green حتى Security + Frontend + Backend + Integration/Playwright كلها PASS على exact SHA نفسه.
9. أكمل بقية W3؛ ثم W4؛ ثم W5؛ ثم W6.
10. لا Merge/Deploy/Railway/Docker قبل الحدود الموثقة.
