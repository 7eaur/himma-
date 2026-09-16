# HIMMA MASTER CONTINUITY HANDOFF — 2026-09-16

**Project:** منصة هِمّة  
**Repository:** `7eaur/himma-`  
**Execution branch:** `audit/comprehensive-repository-review-2026-09-10`  
**Default branch:** `stage/02-content` وليس `main`  
**Phase:** `A10`  
**State:** `A00–A09 CLOSED AUDIT — W1 GREEN — W2 GREEN — W3 GREEN — W4 IN PROGRESS / MEDIA-002 GATE FAILED — W5 NOT STARTED — W6 NOT STARTED`

هذه الوثيقة هي خريطة الاستلام للمحادثة التالية. لا تعتمد على SHA محفوظ قبل Fetch؛ ابدأ دائمًا من live repository وlive GitHub Actions.

## 1) المهمة ودور المسؤول

المطلوب إدارة هِمّة كمنتج تعليمي كامل، لا كمجموعة ترقيعات: Product/Domain Architecture، Backend، Frontend/UX، PostgreSQL/Alembic، Content/Media، Audio/Review، Security/Performance/Accessibility/Observability، QA/E2E، GitHub Actions، والتوثيق.

A00–A09 انتهت؛ لا تعيد التدقيق. نفّذ Master Gap Register من الجذر، موجةً بعد موجة، ولا تنتقل إلى موجة لاحقة قبل Green للموجة الحالية.

## 2) ترتيب الحقيقة

عند التعارض:

1. الكود الحي على execution branch.
2. PostgreSQL schema + Alembic migrations.
3. executable tests + exact-SHA CI.
4. canonical contracts + القرارات المؤرخة المعتمدة.
5. `docs/ops/STATUS.md` و`docs/ops/progress.json` لحالة الاستئناف.
6. Master Gap Register للفجوات وroot causes والتبعيات والاختبارات المطلوبة.
7. الوثائق التاريخية والمراجع الأصلية للسياق فقط عند وجود قرار أحدث.

اقرأ قواعد المشروع أيضًا:

- `AGENTS.md`
- `.agents/rules/00-himma-core.md`
- `.agents/rules/10-delivery-protocol.md`
- `.agents/rules/20-security-quality.md`
- `docs/specs/SOURCE_OF_TRUTH.md`

لا تحذف التاريخ ولا تعدله بصمت. القرار الأحدث يعلو في السلوك الحالي مع بقاء القديم كسجل تاريخي.

## 3) ترتيب القراءة للمحادثة الجديدة

ابدأ حرفيًا بالآتي:

1. `NEXT_CONVERSATION_PROMPT.md`
2. `docs/ops/STATUS.md`
3. `docs/ops/progress.json`
4. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-16_A10_W4_MEDIA_002_GATE_FAIL_AR.md`
5. `docs/maintenance/HIMMA_A10_W4_MEDIA_002_GATE_FAIL_2026-09-16_AR.md`
6. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_STATUS_UPDATE_2026-09-16_AR.md`
7. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
8. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_EXECUTION_ADDENDUM_2026-09-12_AR.md`
9. `docs/ops/HIMMA_W4_OWNER_CLIENT_APPROVAL_2026-09-14.md`
10. `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md`

لفهم الجذور والتاريخ قبل W5/W6، اقرأ عند الحاجة:

- `START_HERE_AR.md`
- `MASTER_PROMPT_AR.md`
- `docs/maintenance/REPOSITORY_HARDENING_PLAN_2026-09-04_AR.md`
- `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`
- `docs/maintenance/OFFICIAL_RECONCILIATION_2026-09-08.md`
- `docs/maintenance/CANONICAL_CONTENT_PORT_2026-09-08_AR.md`
- `docs/maintenance/CANONICAL_CONTENT_EXECUTION_CHECKPOINT_2026-09-09_AR.md`
- `docs/maintenance/CANONICAL_CONTENT_EXECUTION_UPDATE_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_COMPREHENSIVE_REPOSITORY_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A02_A06_STATIC_INVENTORY_2026-09-10.md`
- `docs/maintenance/HIMMA_A02_PYTHON_IMPORT_GRAPH_2026-09-10.md`
- `docs/maintenance/HIMMA_A03_AUDIO_SPEECH_REVIEW_ADAPTATION_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A04_A05_ADMIN_BADGES_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A04_ADMIN_MOBILE_DEEP_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A06_CANONICAL_IMAGE_USAGE_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A06_IMAGE_MEDIA_DEEP_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A07_SECURITY_PERFORMANCE_ACCESSIBILITY_OBSERVABILITY_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A08_FULL_JOURNEY_INTEGRATION_E2E_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A09_BRANCH_CLASSIFICATION_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A10_W1_EXECUTION_CHECKPOINT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A10_W2_EXECUTION_CHECKPOINT_2026-09-12_AR.md`
- `docs/maintenance/HIMMA_A10_W3_EXECUTION_CHECKPOINT_2026-09-12_AR.md`
- W3 automation checkpoints بتاريخ 12–13 سبتمبر عند تتبع finding بعينه.
- W4 checkpoints التاريخية، خصوصًا BADGE-003، BADGE-001، BADGE-002، وMEDIA-002 الحالي.

الـhandoffs القديمة chronology فقط؛ الحالة التنفيذية الأحدث تأتي من STATUS/progress وهذا handoff.

## 4) فكرة المنتج والمعمارية

هِمّة منصة عربية للتقييم والتعلم في القراءة والكتابة والمهارات المرتبطة. المسار العام:

`دخول → اختبار قبلي → توزيع مستوى → أنشطة المستوى → تكيف/تقوية → انتقال أو إكمال المستوى وفق evidence → اختبار بعدي`

Backend هو FastAPI/Python تحت `services/api/`، مع SQLAlchemy وPostgreSQL وAlembic. Canonical content compiler/publisher/release هو مسار نشر المحتوى إلى runtime DB. Frontend هو Next.js تحت `apps/web/` مع Student UI وAdmin/Supervisor UI وBFF.

CI يعمل بدون Docker: native PostgreSQL، Redis في Integration، pinned MinIO، migrations/seed، FastAPI، Next.js، ثم Playwright E2E.

## 5) Canonical Content

الإصدار الحالي: `HIMMA-CONTENT-APPROVAL-2026-09-08`.

آخر candidate #857 أثبت قبل pytest:

- 125 items
- 30 Pretest
- 30 Posttest
- 30 Core
- 35 Reinforcement
- 44 skills
- 358 steps
- 824 options
- 265 asset links

على code candidate `e642aa4b27974c2ec11970fa768f58195188f3f1`:

- Release SHA256: `d23153f45fd8ad5ad6d5eed234d515dc8ec53e0b51c514506619a842277bc1cc`
- Projection SHA256: `a9a2873307e9bebc24680edaaaf5250d98cca1f84c15a93f9538878a371cd3f3`

هذه البصمات evidence للcandidate فقط؛ أي تعديل لاحق يعيد حسابها.

## 6) العقود الأكاديمية الثابتة

Placement:
- `<50` → L1
- `50..<80` → L2
- `80..100` → L3

Adaptation:
- `>=80` نجاح
- `70..<80` guided retry
- `<70` reinforcement

Completion:
- L1/L2 يسمحان early promotion بعد 6 Core على الأقل إذا mastery >=85 + critical coverage + critical floor >=70 + no unresolved blockers عند irreversible boundary.
- لا automatic demotion.
- L3 يتطلب 10 Core.
- Manual level override لا يعني completion ولا badge.

Evidence:
- آخر 3 evidence صالحة من active session بوزن 50/30/20.

Audio/Review:
- uploaded/pending learning audio محايد أكاديميًا ولا يمنع same-level learning/support.
- promotion/L3 completion ينتظر unresolved learning audio عندما يلزم.
- `rerecord_required` deferred، ويُفتح صراحة.
- rerecord append-only؛ القديم immutable، وlatest submission هو active.
- فقط graded evidence تدخل الحساب.
- Human Supervisor Review هي السلطة الأكاديمية الحالية.
- machine SpeechAnalysis/ASR advisory فقط.
- `AUD-A03-008` يبقى `BLOCKED EXTERNAL APPROVAL` إلى أن يعتمد provider + calibration + privacy/cost/governance.

## 7) W1 / W2 / W3

W1 GREEN:
- SHA `ea132c9afbe152d0afa5ae581c058ce3248a0c48`
- #813 / `34467329988`
- أغلق canonical completion، numeric audio rubric، latest submission، deferred rerecord، pending-audio aggregate، early promotion، L3 10-Core، manual override semantics.

W2 GREEN:
- SHA `77ac72174a9e21163f6341ea8e0fcc172269eac3`
- #822 / `34548388760`
- أغلق human/machine linkage، ASR governance registry، worker lease/retry، auth rate limiting، JWT revocation، readiness/cookies، recording limits، sanitized storage errors، request correlation، auth failure signals.

W3 GREEN:
- SHA `62e34b151e46b406cf3936201f80010abbe9d8d1`
- #848 / `34729450663`
- أغلق Admin/Student Detail canonical journey/error states، accessible dialogs/tabs، student-filtered review، responsive matrix، reduced motion/contrast/progress semantics، route-aware media cache، font runtime dependency، وبقية W3 UX/accessibility/observability items.

لا تعيد هذه الموجات بلا regression evidence جديد.

## 8) W4 — الحالة الدقيقة

Closed Green:

- `AUD-BADGE-008` — `57495fb804d4f52f684aded176474155dace07d9`, #850 / `34731134319`.
- `AUD-BADGE-004` — `fddc8a59190d1f6522f1639d4f8156982fbaf293`, #851 / `34732091325`.
- `AUD-BADGE-005` — closed by executable canonical completion evidence on #851 baseline.
- `AUD-BADGE-007` — `970416d707639a3cab2f0dfa930b9f78990afe20`, #853 / `34733663693`.
- `AUD-BADGE-003` — `8736372f855e55646ce50712615b6274af94a9a8`, #854 / `34803602294`.
- `AUD-BADGE-001` — `1f343eb213ccc29c5802d56301319d5d9a5f2132`, #855 / `34805797495`.
- `AUD-BADGE-002` — `f7c6885518e206266bcb1d8805b636931f3ac554`, #856 / `34807098480`.

`AUD-BADGE-006` هو W6 acceptance وليس W4 implementation.

Owner/client approval الموجود في `docs/ops/HIMMA_W4_OWNER_CLIENT_APPROVAL_2026-09-14.md` لا يُطلب مرة أخرى:
- `BDG-01..BDG-06` approved.
- `lexical_stimulus` يمثل معنى الكلمة مباشرة.
- `story_context` سياقي/مساند.
- `سَمَك` → direct fish representation.
- `نُور` → direct light representation.

## 9) AUD-MEDIA-002 — نقطة التوقف الفعلية

آخر code candidate قبل commits التوثيق:

`e642aa4b27974c2ec11970fa768f58195188f3f1`

أضيف:
- `services/api/w4_media_semantics.py`
- تعديل `services/api/canonical_release.py`
- `services/api/test_w4_lexical_media_semantics.py`

العقد يغيّر فقط:
- `L2-CORE-09/R03`: `VOC-05`, `سَمَك`, `lexical_stimulus`.
- `L2-CORE-09/R05`: `VOC-15`, `نُور`, `lexical_stimulus`.

يُطبق قبل canonical hash، ويفشل fail-closed إذا تبدلت هوية الأصل.

Quality Gate #857 / Run ID `35040922310` على exact code SHA نفسه = FAILURE:
- Frontend SUCCESS.
- Security SUCCESS.
- Backend قبل pytest SUCCESS، بما فيه canonical validation + migrations + model drift + seed idempotency.
- pytest: `1 failed, 866 passed`.
- Integration skipped بسبب Backend failure.

الاختبار الوحيد الفاشل:

`test_sep8_approval_projection.py::test_every_declared_image_relationship_is_semantic_and_exact`

السبب:
- Actual الحالي الصحيح: `VOC-05 / image / lexical_stimulus / سَمَك`.
- `STEP_MEDIA` التاريخي في `content_approval_contract_2026_09_08.py` ما يزال يتوقع `VOC-05 / image / context / سمك`.

الاختبارات الجديدة الخاصة بـW4 semantics نجحت. لا ترجع القرار إلى `context` لإرضاء الاختبار القديم؛ أصلح ازدواج authority.

## 10) أول مهمة للمحادثة الجديدة

1. Fetch live execution HEAD؛ توقع أن يكون أحدث من `e642aa4...` بسبب commits التوثيق.
2. Fetch `stage/a10-w4-ci` وlatest run.
3. اقرأ MEDIA-002 checkpoint الحالي.
4. افحص معًا:
   - `content_approval_contract_2026_09_08.py`
   - `w4_media_semantics.py`
   - `canonical_release.py`
   - `test_sep8_approval_projection.py`
   - `test_w4_lexical_media_semantics.py`
   - owner/client approval doc.
5. وحّد owner of truth: التاريخ يبقى محفوظًا، لكن final-release test يجب أن يستهلك authority الحالية الأحدث.
6. لا skip/xpass/delete للاختبار.
7. لا تغيّر R01/R02/R04 بدون evidence؛ التنفيذ الحالي مقصود لـR03/R05 فقط.
8. Commit root fix على execution branch.
9. حرّك `stage/a10-w4-ci` fast-forward إلى exact audit HEAD الجديد؛ لا تدمج helper branch.
10. تأكد أن run `head_sha` يساوي candidate SHA.
11. لا تغلق MEDIA-002 أو W4 إلا بعد Backend + Frontend + Security + Integration/Playwright SUCCESS على SHA نفسه.
12. بعد ذلك فقط حدّث docs إلى W4 GREEN وابدأ W5.

## 11) W5 planned scope

قبل التنفيذ اقرأ الصف الأصلي في Master Gap Register لكل بند:

- `AUD-BE-001`: توحيد activity runtime ownership ثم retire proven-dead فقط.
- `AUD-BE-002`: تصنيف correction/projection seeds؛ حفظ migration/history وحذف dependency-free فقط.
- `AUD-BE-004`: فصل legacy recovery fixture عن canonical current-runtime fixture.
- `AUD-A04-004`: إثبات عدم وجود unique dependency في `/admin/account` قبل redirect/archive.
- `AUD-BADGE-009`: حماية RewardEvent/history من destructive cleanup/cascade.
- `AUD-MEDIA-003`: الـ23 approved unused images تبقى reserve ما لم توجد حاجة دلالية مثبتة.
- `AUD-MEDIA-004`: canonicalize duplicate character URLs فقط بعد إثبات path/dependency safety.
- `AUD-MEDIA-005`: لا حذف للـ17 public files بلا runtime/build/source proof.
- `AUD-PERF-002`: إزالة N+1 في `/researcher/students` عبر batched projection/query budget.
- `AUD-PERF-003`: notifications GET يصبح read-only، وmaterialization ينتقل إلى events/jobs.
- follow-up legacy recording route فقط إذا ثبت أنه dead؛ لا تضعف W2 upload controls.

## 12) W6 / Final Gates

- `AUD-CI-001`: final exact-SHA Quality Gate.
- `AUD-BADGE-006`: full reward lifecycle E2E: award → asset → Student/Admin → refresh/idempotency.
- final responsive/accessibility verification.
- final audio/review lifecycle.
- migrations/model drift/canonical validation/seed idempotency.
- backend/frontend/security/integration + Playwright all Green same SHA.
- security headers contract؛ deployed verification يبقى A11 عند الإذن لاحقًا.

عند W6 Green: **توقف**. لا تنتقل تلقائيًا إلى A11/Deploy/Railway/Production/final merge.

## 13) Git/CI protocol

- العمل على `audit/comprehensive-repository-review-2026-09-10`.
- `stage/a10-w4-ci` CI pointer فقط لأن workflow يستجيب لـ`stage/*`؛ لا merge له.
- لكل batch: root fix → exact SHA → helper fast-forward → match run head_sha → راقب كل jobs → أصلح أي failure من الجذر.
- Documentation-only commits بعد code candidate يجب تمييزها عن `code_sha` المختبر.
- لا تعتبر partial jobs Green نهائيًا إذا كانت Integration/Playwright مطلوبة.

## 14) قيود ثابتة

- No Docker.
- No final/base merge.
- No Deploy / Railway / Production في A10.
- No fake ASR.
- No Temporary Audio Skip.
- No history deletion.
- No Speech/Pronunciation Lab merge.
- `deployment/platform-sandbox` reference-only.
- No runtime repair/overlay hacks بدل إصلاح owner الحقيقي.
- No weakened tests.
- No PASS/CLOSED بلا exact-SHA evidence.
- Production ASR يبقى blocked حتى external governance approval.

## 15) Definition of Done

لكل Gap:
- root cause معالج عند owner الصحيح؛
- invariants الأكاديمية/التاريخية محفوظة؛
- regression tests موجودة؛
- exact-SHA gate عند الحاجة؛
- status/progress/checkpoint/gap overlay محدث؛
- لا claim أوسع من evidence.

**الخلاصة عند التسليم:** لا تعيد BADGE-001/BADGE-002 ولا موافقات W4. نقطة الاستئناف الوحيدة الآن هي حل تعارض current MEDIA-002 authority مع Sep-08 projection test، ثم إعادة Quality Gate كامل. إذا أصبح Green، أغلق W4 وابدأ W5.