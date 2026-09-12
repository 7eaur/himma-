# STATUS — Himma Platform

**Last updated:** 2026-09-12  
**Repository:** `7eaur/himma-`  
**Active remediation branch:** `audit/comprehensive-repository-review-2026-09-10`  
**Current state:** `A00–A09 AUDIT CLOSED — A10/W1 GREEN — A10/W2 GREEN — A10/W3 ACTIVE/CI RED — NO MERGE / NO DEPLOY`

> هذا الملف يعكس نقطة التنفيذ الحالية. أي Recovery/Integration أقدم هو دليل تاريخي فقط وليس release authority.

## Current continuity sources

اقرأ بالترتيب عند بدء محادثة جديدة:

- `NEXT_CONVERSATION_PROMPT.md`
- `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-12_A10_W3_ACTIVE_AR.md`
- `docs/maintenance/HIMMA_A10_W3_EXECUTION_CHECKPOINT_2026-09-12_AR.md`
- `docs/ops/progress.json`
- `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A10_W1_EXECUTION_CHECKPOINT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A10_W2_EXECUTION_CHECKPOINT_2026-09-12_AR.md`

الـhandoff القديم `HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-10_A10_W1_FULL_AR.md` محفوظ للتاريخ فقط، وقد تم تجاوزه كنقطة استكمال.

---

## Audit status

A00–A09 مغلقة كتدقيق ولا تعاد من الصفر. A10 هو التنفيذ الجذري وفق Master Gap Register.

---

## A10 / W1 — CLOSED GREEN

W1 = Academic / History Integrity.

- Exact verified SHA: `ea132c9afbe152d0afa5ae581c058ce3248a0c48`
- Quality Gate: Run #813 / ID `34467329988`
- Security PASS.
- Frontend PASS.
- Backend PASS.
- Integration / Playwright E2E PASS.

أُغلقت عقود append-only rerecord، latest AudioSubmission، explicit/deferred rerecord، numeric rubric evidence، pending-audio aggregate، canonical Level Completion، Journey/Rewards truth، L1/L2 early promotion، L3 10 Core، manual override ≠ completion/badge، وإصلاح أصل WebP الفاسد دون تغيير الدلالة الأكاديمية.

---

## A10 / W2 — CLOSED GREEN

W2 = Security / Speech Boundaries.

- Exact verified SHA: `77ac72174a9e21163f6341ea8e0fcc172269eac3`
- Quality Gate: Run #822 / ID `34548388760`
- Security PASS.
- Frontend PASS.
- Backend PASS — 852 tests successful.
- Integration / Playwright E2E PASS.
- Alembic upgrade → downgrade → upgrade PASS.
- model drift PASS.
- canonical validation + seed idempotency PASS.

أُغلقت rate limiting، revocable auth epoch، protected readiness/Secure cookie، recording upload boundary، sanitized storage errors، ASR governance، machine-advisory/human-authority boundary، durable worker leases، bounded retry/dead-letter/manual recovery، request correlation وprivacy-safe auth signals.

`AUD-A03-008` يبقى **BLOCKED EXTERNAL APPROVAL**: لا يوجد Production ASR provider/model/calibration/privacy/cost/governance معتمد.

---

## A10 / W3 — ACTIVE / NOT GREEN

W3 = Admin / Student UX / Accessibility / Web Reliability.

### Latest code-bearing checkpoint before documentation commits

`3962d101b2c1ba4c5294235dfac797687209cbfb`

Commit:

`fix(admin): align audio review with shared admin component contracts`

> HEAD الحالي قد يكون أعلى بسبب commits التوثيق. عند التنفيذ اجلب HEAD وحدد أحدث code-bearing commit ولا تفترض أن documentation HEAD هو code gate.

### W3 implementation already present

- shared accessible dialog hook + unit test: focus entry/trap/Escape/return-focus/scroll lock.
- Admin mobile dialog semantics integrated.
- Settings tablist/tab/tabpanel + roving tabindex + arrows/Home/End.
- canonical researcher Journey endpoint using `journey.build_journey_summary()`.
- Student Detail canonical Journey + explicit loading/loaded/error for journey/history/rewards.
- student-filtered Audio Review API/UI preserving student context.
- route-aware BFF cache policy and tests introduced.

### Exact W3 CI stop point

Helper branch: `stage/a10-w3-ci` — verification only, do not merge.

Quality Gate:

- Run #829
- Run ID `34703574228`
- Exact SHA `3962d101b2c1ba4c5294235dfac797687209cbfb`

Final result:

- Security: PASS.
- Backend: PASS.
- Frontend TypeScript: PASS.
- Frontend ESLint: PASS.
- Frontend unit tests: **FAIL** — 1 BFF cache-policy test.
- Frontend build: skipped.
- Integration / Playwright: skipped.

### Current first blocker

`apps/web/src/app/api/[...path]/cachePolicy.ts`

Bug: successful media GET with upstream `Cache-Control: private, no-store` is incorrectly converted to `public, max-age=86400`.

Correct root fix:

- explicit upstream `private/no-store` must remain private.
- explicit safe public may be preserved.
- fallback `public, max-age=86400` only when upstream cache header is absent on approved successful media GET/HEAD with no Set-Cookie.
- do not weaken the existing failing test.

بعد الإصلاح يجب تحريك helper إلى SHA الجديد وتشغيل full exact-SHA Quality Gate.

### Remaining W3 scope

- AdminUI/presentation unification where ownership is proven.
- Student Detail partial-source error/retry regressions.
- canonical Journey UI scenario verification.
- responsive Student Detail matrix: 320/360/390/430/768/Desktop.
- accessible dialog final keyboard regression.
- Settings tokens/presentation finalization.
- Student Detail → filtered audio review context E2E.
- BFF cache root fix.
- remove runtime Google Fonts dependency; local/build-time typography strategy.
- global reduced-motion policy.
- accessible semantic color variants/contrast.
- progressbar semantics.
- scenario integrity: skipped ≠ completed; manual override ≠ completion/badge; pending audio neutrality; irreversible boundary holds; append-only history; partial failure ≠ zero/success.

W3 ليست Green حتى Security + Frontend + Backend + Integration/Playwright كلها PASS على exact SHA واحد.

---

## W4 queued — Rewards / Badges / Media semantics

الملاحظات المثبتة ولا يجب نسيانها بعد W3:

- Student Home يعرض total stars لكنه لا يعرض canonical badge assets كاملًا.
- Admin badge presentation يحتاج shared visual catalog.
- approved badge mapping: BDG-01/02/03 للنجوم، BDG-04 مستكشف الحروف، BDG-05 بطل الكلمات، BDG-06 نجم الفهم.
- L3 backend label الحالي `قارئ متميز` مقابل approved `نجم الفهم`: migration/history-compatible catalog fix مطلوب.
- Reward API failure يجب أن يظهر unavailable/error لا 0.
- Reward API يحتاج stable catalog/version/asset identity.
- audio rerecord لا يدخل حاليًا بوضوح في `_stars_for_attempt()` retry semantics؛ يجب ألا يحصل rerecord على 3 نجوم كأنه بلا إعادة.
- pending/ungraded audio لا يمنح reward مبكرًا.
- full reward award→asset→Student/Admin→refresh/idempotency E2E مطلوب في W6.
- `AUD-MEDIA-002` يحتاج Academic Review قبل تغيير lexical stimulus assets.

---

## Active academic contract

- Placement: `<50` → L1, `50..<80` → L2, `80..100` → L3.
- Activity `>=80` success, `70..<80` guided retry, `<70` reinforcement.
- L1/L2 early promotion: >=6 Core + mastery >=85 + critical coverage + critical floor >=70 + no unresolved blockers at irreversible boundary.
- no automatic demotion.
- L3 requires 10 Core.
- newest three valid active-session evidences: 50/30/20.
- `current_level` is a pointer, not historical completion proof.

---

## Canonical content/runtime contract

- Runtime total: **125**.
- Pretest: 30.
- Posttest: 30.
- Learning runtime: 65.
- Reinforcement: 35.
- Skills: 44.
- Projection: `structured_db_runtime_v1`.
- Architecture: `approved_versioned_source → deterministic_structured_projection → postgres_runtime → structured_api → deterministic_renderer`.

Do not revert to historical 105-item assumptions.

---

## Audio authority

- approved static audio IDs: 54; WAV 54; MP3 54.
- uploaded/pending = academically neutral.
- same-level learning/support may continue while learning audio is unresolved.
- irreversible promotion/L3 completion waits for unresolved learning audio.
- assessment may wait human review under current contract.
- rerecord_required deferred until explicit learner open.
- rerecord append-only; previous submissions immutable.
- latest AudioSubmission = active state.
- graded only may contribute evidence.
- Human Supervisor Review = academic authority.
- Production ASR = not approved.

---

## W5 / W6 / A11

W5: historical cleanup/performance/test ownership only after dependency proof; no destructive cleanup.  
W6: final exact-SHA Security/Frontend/Backend/Integration/Playwright/responsive/accessibility/reward lifecycle gates.  
A11: Deployment/Railway only after W6 Green.

---

## Branch governance

- No blind merge.
- Speech/Pronunciation Lab branches remain research-only / EXCLUDE FROM MERGE.
- `deployment/platform-sandbox` remains reference only.
- no Docker or Temporary Audio Skip revival.
- CI helper branches are verification pointers only.

---

## External open decisions

- Production ASR provider/calibration/privacy/cost/governance.
- intervention/session duration before study activation.
- child-recording retention policy before real-child production data.
- domain/hosting/deployment settings.
- supervising organization details/logo before final report signoff.
- credential rotation before production if historical exposure is confirmed.

---

## Exact next step

Fetch current audit HEAD → read W3 checkpoint → check whether a code commit newer than `3962...` already fixes the BFF cache bug → if not, fix `cachePolicy.ts` root cause → move `stage/a10-w3-ci` to the new exact SHA → run full Quality Gate → fix real failures → finish remaining W3 → only then W4 → W5 → W6.
