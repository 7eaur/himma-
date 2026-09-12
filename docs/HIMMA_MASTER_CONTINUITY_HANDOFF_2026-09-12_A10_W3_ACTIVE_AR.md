# منصة هِمّة — Master Continuity Handoff

**الإصدار:** 2026-09-12 — A10/W3 Active  
**المستودع:** `7eaur/himma-`  
**فرع التنفيذ:** `audit/comprehensive-repository-review-2026-09-10`  
**الحالة:** `A00–A09 CLOSED — W1 GREEN — W2 GREEN — W3 ACTIVE/CI RED — NO MERGE / NO DEPLOY`

> **هذا هو مرجع الاستكمال الرئيسي للمحادثات الجديدة.** handoff المؤرخ 2026-09-10 محفوظ كتاريخ فقط وقد تجاوزه التنفيذ. اجلب HEAD الحالي دائمًا قبل العمل لأن commits التوثيق قد تكون بعد آخر code-bearing SHA.

---

## 1. بروتوكول البدء في محادثة جديدة

نفّذ بالترتيب:

1. Fetch HEAD لـ`audit/comprehensive-repository-review-2026-09-10`.
2. اقرأ:
   - `NEXT_CONVERSATION_PROMPT.md`
   - هذا الملف.
   - `docs/maintenance/HIMMA_A10_W3_EXECUTION_CHECKPOINT_2026-09-12_AR.md`
   - `docs/ops/STATUS.md`
   - `docs/ops/progress.json`
   - `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
3. لا تعِد A00–A09.
4. لا تعِد W1/W2؛ كلاهما Closed Green.
5. حدد أحدث code-bearing commit، ولا تعتبر documentation commit code gate.
6. تابع من أول W3 gap غير مغلق، أصلح root cause، واختبر exact SHA.
7. لا Merge/Deploy/Docker/Railway قبل الحدود النهائية.

---

## 2. تعريف المشروع وSource of Truth

هِمّة منصة تعليمية عربية لقياس وتنمية القراءة، بمسار:

`دخول بكود → اختبار قبلي → تصنيف → تعلم المستوى → تقوية موجهة → ترقية/استكمال → اختبار بعدي → تقارير المشرف`

المعمارية المعتمدة للمحتوى:

`approved/versioned source → deterministic structured projection → PostgreSQL runtime → structured API → deterministic renderer`

Canonical compiler/publisher هو owner للمحتوى؛ ممنوع repair/overlay chains جديدة فوق runtime.

العقد الحالي:

- Canonical/runtime total = **125**.
- Pretest = 30.
- Posttest = 30.
- Learning runtime = 65.
- Reinforcement = 35.
- Skills = 44.
- Projection = `structured_db_runtime_v1`.

أي 105-world assumptions قديمة = historical test/migration context، وليست runtime truth الحالية.

---

## 3. العقد الأكاديمي

### Placement

- `<50%` → L1.
- `50..<80%` → L2.
- `80..100%` → L3.

### Adaptation V4

- `>=80` نجاح.
- `70..<80` guided retry.
- `<70` guided reinforcement.

### Promotion / Completion

L1/L2 early promotion فقط عند:

- >=6 Core.
- weighted mastery >=85.
- critical coverage.
- critical floor >=70.
- no unresolved reinforcement.
- no supervisor blocker.
- no unresolved learning audio عند irreversible boundary.

ثوابت:

- no automatic demotion.
- ترقية مستوى واحد فقط.
- L3 يحتاج 10 Core ولا يوجد L4.
- أحدث 3 evidences صالحة في active session بأوزان 50/30/20.
- `current_level` pointer وليس completion evidence.
- manual override لا يعني level completion ولا badge.

---

## 4. عقد الصوت والسلطة الأكاديمية

Static approved audio:

- IDs = 54.
- WAV = 54.
- MP3 = 54.

Student audio:

- uploaded/pending = academically neutral.
- pending learning audio لا يمنع same-level learning/support/navigation.
- unresolved learning audio يمنع irreversible promotion/L3 completion.
- assessment قد ينتظر Human Review وفق العقد الحالي.
- `rerecord_required` deferred حتى explicit learner open.
- rerecord append-only؛ كل إعادة = AudioSubmission جديد.
- previous submissions immutable history.
- latest AudioSubmission = active state.
- graded فقط يدخل academic evidence.
- AudioReview rubric رقمي ولا يتحول Boolean.
- Human Supervisor Review = academic authority.

Production ASR:

- **غير معتمد**.
- machine SpeechAnalysis = advisory.
- env threshold/model string لا يمنح approval.
- `AUD-A03-008` = BLOCKED EXTERNAL APPROVAL حتى provider + calibration + privacy + cost + governance approval.

---

## 5. قواعد التنفيذ والحوكمة

- لا Docker.
- لا blind merge.
- لا deploy/Railway قبل W6 Green/A11.
- لا fake ASR.
- لا Temporary Audio Skip.
- لا حذف academic/audio/reward history.
- Speech/Pronunciation Lab branches = research only / EXCLUDE FROM MERGE.
- `deployment/platform-sandbox` = reference only.
- CI helper branches = verification pointers only، لا تُدمج.
- كل PASS يحتاج exact SHA + actual executed gate.
- لا تغيّر test لإخفاء bug حقيقي.

---

## 6. A00–A09 — CLOSED AUDIT

لا تعاد. Master Gap Register هو خريطة التنفيذ:

`docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`

وملفات A03/A04/A05/A06/A07/A08/A09 تبقى أدلة تدقيق تاريخية عند الحاجة.

---

## 7. W1 — CLOSED GREEN

**Scope:** Academic / History Integrity.

- Exact SHA: `ea132c9afbe152d0afa5ae581c058ce3248a0c48`
- Run #813
- Run ID `34467329988`
- Security PASS.
- Frontend PASS.
- Backend PASS.
- Integration/Playwright PASS.

أغلق:

- latest AudioSubmission owner.
- append-only rerecord + explicit/deferred open.
- old submissions immutable.
- numeric rubric evidence 0.0/0.1/0.7/1.0.
- pending-audio aggregate مستقل عن navigation.
- canonical Level Completion owner.
- Journey/Rewards completion truth موحد.
- manual override ≠ completion/badge.
- L1/L2 early promotion 6–9 Core حسب gates.
- L3 10 Core.
- corrupt house WebP fixed دون تغيير Stable ID/دلالة `بيت`.

Checkpoint:

`docs/maintenance/HIMMA_A10_W1_EXECUTION_CHECKPOINT_2026-09-10_AR.md`

---

## 8. W2 — CLOSED GREEN

**Scope:** Security / Speech Boundaries.

- Exact SHA: `77ac72174a9e21163f6341ea8e0fcc172269eac3`
- Run #822
- Run ID `34548388760`
- Security PASS.
- Frontend PASS.
- Backend PASS — 852 tests.
- Integration/Playwright PASS.
- Alembic upgrade→downgrade→upgrade PASS.
- model drift PASS.
- canonical validation + seed idempotency PASS.

أغلق:

- Redis/HMAC auth rate limiting.
- revocable auth epoch بعد credential rotation.
- protected readiness + Secure cookies.
- recording pre-upload size/type boundary + completion recheck.
- sanitized storage errors.
- source-controlled ASR governance.
- machine advisory / human authority.
- durable worker leases/claim.
- bounded retry/dead-letter/manual audited recovery.
- request correlation API+BFF.
- privacy-safe auth failure signals.

`AUD-A03-008` يبقى external blocked.

Checkpoint:

`docs/maintenance/HIMMA_A10_W2_EXECUTION_CHECKPOINT_2026-09-12_AR.md`

---

## 9. W3 — ACTIVE / CI RED

**Scope:** Admin / Student UX / Accessibility / Web Reliability.

### آخر code-bearing checkpoint قبل التوثيق

`3962d101b2c1ba4c5294235dfac797687209cbfb`

Commit: `fix(admin): align audio review with shared admin component contracts`

W3 code من W2 إلى هذا SHA = 19 commits.

### ما تم تنفيذه

- `useAccessibleDialog` مشترك: focus entry/trap، Escape، return focus، scroll lock + unit test.
- Admin mobile dialog ARIA/focus lifecycle.
- Settings tablist/tab/tabpanel + roving tabindex + arrows/Home/End.
- `services/api/researcher_journey.py`: canonical supervisor Journey من `build_journey_summary()`.
- Student Detail: canonical per-level Journey + explicit loading/loaded/error لـjourney/history/rewards.
- `review.py`: optional `student_id` filter للمشرف دون تغيير academic/review state.
- Audio Review UI يحتفظ بسياق الطالب.
- BFF route-aware cache policy + tests أضيفت، لكنها ما زالت تحوي bug حقيقي.

### Exact CI stop point

Helper: `stage/a10-w3-ci` — verification only.

Run:

- Quality Gate #829
- Run ID `34703574228`
- Exact SHA `3962d101b2c1ba4c5294235dfac797687209cbfb`

النتيجة النهائية:

- Security PASS.
- Backend PASS، بما يشمل migrations/drift/canonical/seed/full tests.
- TypeScript PASS.
- ESLint PASS.
- Frontend unit tests **FAIL** باختبار واحد.
- Build skipped.
- Integration/Playwright skipped.

إذن W3 ليست Green.

### Current first blocker

الملفات:

- `apps/web/src/app/api/[...path]/cachePolicy.ts`
- `apps/web/src/app/api/[...path]/route.test.ts`

Bug:

approved media GET + successful upstream + explicit `Cache-Control: private, no-store` يعاد خطأ كـ`public, max-age=86400`.

Root fix:

- non-media/non-GET-HEAD/non-success/Set-Cookie → private no-store.
- explicit upstream private/no-store → private no-store.
- explicit safe public → preserve.
- public 86400 fallback فقط عند **غياب** upstream Cache-Control في approved successful media GET/HEAD.
- لا تضعف test.
- commit → move helper إلى exact SHA الجديد → full Quality Gate.

هذا هو **أول عمل** إذا لم يوجد commit أحدث أصلح المشكلة.

### W3 remaining بالكامل

- `AUD-A04-001`: AdminUI/presentation unification حيث ownership مثبت.
- `AUD-A04-002`: partial-source failure/retry tests؛ لا empty/zero misleading state.
- `AUD-A04-003`: canonical Journey UI scenarios: override/skipped/early-promotion/active/completed.
- `AUD-A04-005`: viewport matrix 320/360/390/430/768/Desktop.
- `AUD-A04-006`: final keyboard dialog regression.
- `AUD-A04-007`: Settings shared tokens/presentation + final semantics.
- `AUD-A04-008`: Student Detail→filtered review→pending/graded/rerecord→back context E2E.
- `AUD-PERF-001`: current cache root fix.
- `AUD-PERF-004`: إزالة runtime Google Fonts dependency؛ local/build-time typography.
- `AUD-A11Y-001`: global reduced motion.
- `AUD-A11Y-002`: semantic accessible colors/contrast.
- `AUD-A11Y-003`: progressbar semantics.
- scenario integrity across desktop/mobile/keyboard.
- exact-SHA Security+Frontend+Backend+Integration/Playwright Green.

تفاصيل التنفيذ:

`docs/maintenance/HIMMA_A10_W3_EXECUTION_CHECKPOINT_2026-09-12_AR.md`

---

## 10. W4 — Rewards / Badges / Media Semantics

هذه الملاحظات ثبتت في مراجعة المستخدم الأخيرة ولا تُنسى بعد W3.

### Approved badge catalog المطلوب

- `BDG-01` = نجمة واحدة.
- `BDG-02` = نجمتان.
- `BDG-03` = ثلاث نجوم.
- `BDG-04` = مستكشف الحروف.
- `BDG-05` = بطل الكلمات.
- `BDG-06` = نجم الفهم.

### الحالة الحالية الصحيحة جزئيًا

- RewardEvent لديه unique `(student_id, reward_key)` للـidempotency.
- badge eligibility تعتمد canonical `level_was_completed()`.
- early promotion L1/L2 يمكن أن يصنع completion-dependent badge.
- manual override وحده لا يصنع badge.
- L3 يحتاج 10 Core.
- pending/ungraded audio لا يجب أن ينتج reward evidence مبكرًا.
- Star logic الحالي: 3 بلا structured help/retry، 2 hint بلا retry، 1 structured retry.

### gaps المتبقية

- `AUD-BADGE-001`: Student Home لا يعرض canonical badge assets كاملًا.
- `AUD-BADGE-002`: Admin badge presentation يحتاج shared visual catalog.
- `AUD-BADGE-003`: approved assets يجب دمجها بـstable IDs/metadata.
- `AUD-BADGE-004`: L3 backend label الحالي `قارئ متميز` مقابل approved `نجم الفهم`؛ migration/history-compatible resolution.
- `AUD-BADGE-007`: reward API failure ≠ zero rewards.
- `AUD-BADGE-008`: stable catalog/version/asset identity في API.
- `AUD-BADGE-006`: full award→asset→Student/Admin→refresh/idempotency E2E في W6.

### Star logic gap مهم

`_stars_for_attempt()` يعتمد structured step retries/hints، ولا يحسب audio rerecord بوضوح كـretry. قد يحصل الطالب نظريًا على 3 نجوم رغم إعادة التسجيل.

Root fix W4:

- audio rerecord يدخل effort/retry semantics.
- لا حذف history.
- pending/ungraded audio لا يمنح نجومًا مبكرًا.
- idempotency يبقى.
- regression لتراكم وتسلسل النجوم وعدم duplicate reward.

### Media semantics

`AUD-MEDIA-002` = Academic Review Required. لا تستبدل lexical stimulus image آليًا دون اعتماد أكاديمي.

واجهة الصور النهائية يجب أن تحقق:

- no distortion.
- responsive sizing.
- semantic role صحيح.
- meaningful alt للدلالي.
- empty alt للزخرفي.

---

## 11. Typography / responsive / scenario quality

`globals.css` لا يزال يحمّل Google Fonts runtime (`Tajawal`, `IBM Plex Sans Arabic`)؛ W3 يجب أن يزيل الاعتماد الخارجي runtime ويثبت local/build-time strategy.

التحقق النهائي يشمل:

- Arabic wrapping بدون clipping.
- responsive type scale/rem/clamp عند الحاجة.
- images بنسبة صحيحة/object-fit مناسب.
- 320px إلى Desktop.
- keyboard/focus/contrast/reduced-motion.
- نفس الحقيقة الأكاديمية على كل viewport/input method.

---

## 12. W5 — Historical Cleanup / Performance / Test Ownership

بعد W4 فقط، وبدون cleanup أعمى:

- `AUD-BE-001`: runtime service generations classification قبل retire.
- `AUD-BE-002`: old seeds/repairs تصنيف runtime/migration/test/dead مع dependency proof.
- `AUD-BE-004`: legacy 105-world tests منفصلة عن canonical 125.
- `AUD-BADGE-009`: Reward history cascade risk قبل destructive reset/cleanup.
- media unused/duplicates لا تُحذف لمجرد textual no-reference.
- `AUD-PERF-002`: researcher students N+1.
- `AUD-PERF-003`: Notifications GET mutation/polling contract.
- duplicate `/admin/account` فقط بعد proof.

---

## 13. W6 — Final Exact-SHA Gates

لا release قبل SHA واحد ينجح فيه:

- Security.
- Frontend TS/Lint/Unit/Build.
- Backend full tests.
- Alembic upgrade/downgrade/upgrade.
- model drift.
- canonical validation + seed idempotency.
- Integration/Playwright.
- responsive matrix.
- accessibility regressions.
- full reward lifecycle E2E.
- scenario integrity.

---

## 14. A11 — Deployment/Railway

Blocked until W6 Green.

لا Docker ولا deployment finalization قبل ذلك. platform sandbox ليس production authority.

---

## 15. External decisions المفتوحة

لا تحل بالتخمين:

- Production ASR provider/model/calibration/privacy/cost/governance.
- intervention/session duration قبل study activation.
- child-recording retention policy قبل real-child production data.
- domain/hosting/deployment settings.
- supervising organization details/logo قبل final report signoff.
- credential rotation قبل production إذا ثبت historical exposure.

---

## 16. تعريف Done

المشروع لا يعتبر مكتملًا لأن UI يفتح أو بعض tests ناجحة. Done يعني:

- كل A10 gap = CLOSED evidence أو BLOCKED EXTERNAL موثق.
- Backend/UI/Reports/Rewards لا تتناقض أكاديميًا.
- no hidden bypasses.
- no misleading UX states.
- approved media/reward semantics صحيحة.
- accessibility/responsive/performance gates مثبتة.
- W6 exact-SHA Green.
- بعدها فقط release/deploy governance.

---

## 17. Exact resume instruction

Fetch audit HEAD → اقرأ W3 checkpoint/STATUS/progress → تحقق هل يوجد code commit بعد `3962...` أصلح BFF cache bug → إن لم يوجد أصلحه من root cause → commit → move `stage/a10-w3-ci` → full exact-SHA gate → أكمل كل W3 → W4 → W5 → W6 → A11 فقط بعد W6 Green.
