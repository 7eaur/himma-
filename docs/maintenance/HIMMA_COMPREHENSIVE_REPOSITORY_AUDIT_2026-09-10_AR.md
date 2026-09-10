# منصة هِمّة — المراجعة الشاملة للمستودع

**التاريخ:** 2026-09-10  
**الحالة:** `A00–A09 AUDIT COMPLETE — A10 ROOT REMEDIATION STARTS — NO MERGE — NO DEPLOY`  
**المستودع:** `7eaur/himma-`  
**فرع المراجعة/الصيانة الحالي:** `audit/comprehensive-repository-review-2026-09-10`

> هذا الملف سجل مركزي. التفاصيل الكاملة لكل مرحلة في تقارير `docs/maintenance/`. Git الحالي هو الحقيقة التنفيذية إذا تقدم عن SHA مذكور في تقرير أقدم، مع عدم الرجوع عن قرارات المحتوى/الصوت/التكيف الأحدث.

---

## 1. الهدف والقواعد

المراجعة لم تكن بحثًا عن أخطاء سطحية، بل فحص ownership والمعمارية والتاريخ والـUX والبيانات والاختبارات والفروع قبل الصيانة والنشر.

القواعد الثابتة:

- لا Docker.
- لا Merge أو Deploy أثناء A00–A10.
- لا Repair/Overlay runtime جديد.
- لا حذف history أو AudioSubmissions أو evidence أكاديمي بغرض التنظيف.
- canonical content الحالي = **125 عنصرًا** بعد اعتماد 2026-09-08.
- pending/uploaded audio محايد أكاديميًا ولا يمنع same-level navigation/support.
- promotion/L3 completion فقط هي boundaries التي تنتظر unresolved audio.
- `rerecord_required` مهمة مؤجلة يفتحها الطالب صراحة.
- إعادة التسجيل يجب أن تكون append-only.
- `graded` فقط يدخل evidence الأكاديمي.
- latest AudioSubmission هو الحالة الفعالة.
- لا Production ASR Provider معتمد؛ لا دمج لفروع Speech Lab قبل اعتماد مستقل.
- early promotion في L1/L2 قرار معتمد ولا يُلغى لتسهيل الشارات أو الاختبارات.

---

## 2. حالة المراحل

| المرحلة | الحالة | المخرج |
|---|---|---|
| A00 Baseline / CI | CLOSED AUDIT | تشغيل مرجعي وتحليل gates |
| A01 Backend ownership | CLOSED AUDIT | ownership gaps + runtime layering |
| A02 Seeds / Migrations / Legacy | CLOSED AUDIT | static inventory + Python import graph |
| A03 Audio / Speech / Review / Adaptation | CLOSED AUDIT | `HIMMA_A03_AUDIO_SPEECH_REVIEW_ADAPTATION_AUDIT_2026-09-10_AR.md` |
| A04 Admin / Student Details / Mobile | CLOSED AUDIT | `HIMMA_A04_ADMIN_MOBILE_DEEP_AUDIT_2026-09-10_AR.md` |
| A05 Rewards / Badges | CLOSED AUDIT | `HIMMA_A04_A05_ADMIN_BADGES_AUDIT_2026-09-10_AR.md` |
| A06 Images / Media | CLOSED AUDIT | `HIMMA_A06_IMAGE_MEDIA_DEEP_AUDIT_2026-09-10_AR.md` |
| A07 Security / Performance / Accessibility / Observability | CLOSED AUDIT | `HIMMA_A07_SECURITY_PERFORMANCE_ACCESSIBILITY_OBSERVABILITY_AUDIT_2026-09-10_AR.md` |
| A08 Full Journey / Integration / E2E | CLOSED AUDIT | `HIMMA_A08_FULL_JOURNEY_INTEGRATION_E2E_AUDIT_2026-09-10_AR.md` |
| A09 All Branches | CLOSED AUDIT | `HIMMA_A09_BRANCH_CLASSIFICATION_2026-09-10_AR.md` |
| Master Gap Register | COMPLETE | `HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md` |
| A10 Root Remediation | **NEXT / START W1** | تنفيذ جذري بالموجات |
| A11 Railway Finalization | BLOCKED UNTIL GREEN | بعد Final Gates فقط |

---

## 3. خط الأساس وCI الحقيقي

تشغيل GitHub Actions المرجعي `34419490966` على `7cb2192b0c31bc85dcf98a470023e9cc6f1598e0` أثبت:

- Security PASS.
- Frontend PASS.
- canonical validation PASS.
- Alembic up/down/up PASS.
- drift PASS.
- canonical seed idempotency PASS.
- Backend: **823 passed / 2 failed / 825**.
- Integration: **SKIPPED** لأن Backend dependency gate فشل.

الفشلان:

1. `AUD-BE-003`: pending learning audio summary يرجع 0 في حالة يوجد معها step آخر actionable.
2. `AUD-BE-004`: recovery test يبني baseline 105 قديمًا ويرى PRE-Q05 بثلاث صور بدل canonical الحالي بأربع.

وفي نفس التشغيل نجح `test_m09_full_single_candidate_journey.py`، لكنه domain longitudinal test وليس Full Browser Journey.

فرع المراجعة `audit/*` غير داخل push triggers الحالية، لذلك لا يوجد Green exact-HEAD للـaudit branch ويجب تشغيل Final Gate صريح لاحقًا.

---

## 4. Backend / Seeds / Runtime ownership

### AUD-BE-001

Router الأنشطة العام واحد، لكن `activity_runtime.py` ما زال يعتمد خدمات تاريخية من `activities_v4.py` و`activities.py`. لا حذف قبل parity/dependency extraction.

### AUD-BE-002

`seed_all.py` canonical وينشر 125 عنصرًا دون repair chain runtime، لكن ملفات seed/projection/correction التاريخية ما زالت في الشجرة. تصنيفها migration/test/tool/dead مطلوب قبل cleanup.

### AUD-BE-003

navigation resolver يخلط اختيار next action مع pending-audio summary. W1 يفصل الاثنين.

### AUD-BE-004

Recovery test تاريخي يبني عالم 105 بدل current canonical 125. W5 يفصل migration compatibility tests عن runtime-current tests.

---

## 5. A03 — الصوت والتحليل والتكيف

أهم P0/P1:

- `AUD-A03-001 P0`: assessment rerecord يستبدل نفس AudioSubmission بدل append-only.
- `AUD-A03-002 P1`: latest-submission semantics غير موحدة في assessment/profile/completion.
- `AUD-A03-003 P1`: invalid human review يعيد Attempt إلى in_progress فورًا بدل deferred explicit rerecord.
- `AUD-A03-009 P0`: `rubric_score > 0` يتحول إلى boolean correctness؛ يمكن أن تصبح 0.10 و1.00 متكافئتين في evidence.
- `AUD-A03-004/005`: machine analysis وhuman adjudication/calibration governance غير موحدين.
- `AUD-A03-006`: worker claim غير ذري.
- `AUD-A03-007`: retry/operator recovery غير مكتمل.
- `AUD-A03-008`: Production ASR **BLOCKED** حتى اعتماد provider/model/calibration/privacy/cost.

ما هو صحيح ويحفظ:

- core learning audio لا يوقف same-level navigation.
- unresolved audio يوقف فقط irreversible promotion/L3 completion.
- speech queue/pipeline موجود فعلًا ولا يخترع score عند غياب provider.
- machine confidence ليس academic truth.

---

## 6. A04 — Admin / Student Details / Mobile

الفجوات الأساسية:

- `AUD-A04-001 P1`: AdminUI موجود، لكن Student Details + Settings + legacy Account يعيدون بناء presentation systems موازية.
- `AUD-A04-002 P1`: فشل history/rewards يتحول إلى empty/zero في Student Details بدل error state.
- `AUD-A04-003 P1`: Journey UI يستنتج completion من `current_level` بدل longitudinal evidence، ويتأثر manual override.
- `AUD-A04-004 P2`: `/admin/account` legacy duplicate؛ لا حذف قبل dependency scan/redirect plan.
- `AUD-A04-005 P1`: لا Student Details mobile gate deterministic عند 320/360/390/430/768/Desktop.
- `AUD-A04-006/007`: keyboard dialog lifecycle وSettings tabs/accessibility تحتاج توحيدًا.
- `AUD-A04-008`: Student Detail يفقد سياق الطالب عند الانتقال إلى audio-review العامة.

اتجاه A10: `global tokens → AdminUI primitives → page-specific composition`، دون Design System ثانٍ.

---

## 7. A05 — Rewards / Badges

Backend RewardEvent موجود ودائم مع idempotency، لكن المنتج غير مكتمل end-to-end:

- Student لا يعرض badges بصريًا.
- Admin يعرض label فقط.
- الحزمة الرسمية BDG-01..06 غير مدمجة كReward Catalog في الويب.
- L3 backend `قارئ متميز` مقابل asset الرسمي `نجم الفهم`.
- أخطر semantic gap: early promotion يثبت L1/L2 completion عند 6–9 Core بينما badge logic يمنح عند 10 فقط.
- Reward API لا يحمل stable asset/catalog version.
- failure في Student rewards يظهر 0 بدل unavailable.
- لا full badge lifecycle E2E.
- Reward history FK يحتاج حماية من cleanup destructive paths.

الحل: **Level Completion owner واحد + Canonical Reward Catalog واحد**.

---

## 8. A06 — Images / Media

المثبت:

- 125 canonical items.
- 71 image IDs معروفة.
- 48 referenced من canonical release.
- 23 approved unused reserve.
- 0 referenced image IDs مفقودة.
- 18 multi-semantic IDs، أغلبها accepted aliases/context reuse.
- لا exact duplicate SHA داخل `assets/education`.
- 5 duplicate character SHA groups في `apps/web/public`، ولا حذف قبل dependency proof.

الفجوة الأكاديمية P1:

`L2-CORE-09` يستخدم image context كـlexical stimulus، بينما semantic guard صارم أساسًا للـchoice images. جولتا `سَمَك` مع صورة `سمكة` و`نُور` مع صورة مصباح/ضوء تحتاجان **قرارًا أكاديميًا** ثم role-aware semantic contract (`lexical_stimulus` مقابل `story_context` وغيرها). لا تغيير عشوائي أثناء التدقيق.

---

## 9. A07 — Security / Performance / Accessibility / Observability

### Security P1

- لا rate limiting لمسارات login.
- تغيير access code/password لا يبطل JWT قائمًا فورًا.
- Secure cookie يعتمد `ENV=production` لكن readiness لا يفرض هذا الوضع.
- legacy `/recordings/init` presigned PUT بلا max upload policy مثبت.

P2: raw storage errors، وsecurity headers تحتاج owner/verification نهائيًا.

### Performance

- P1: Next BFF يحول immutable media cache إلى `private,no-store` حتى لـ`/api/media/*`.
- P2: Admin students N+1، notification GET يكتب/reconciles، Google Fonts runtime dependency.

### Accessibility

- P1: reduced-motion contract في E2E دون implementation عالمي ظاهر.
- P1: primary/green tokens لا تحقق 4.5:1 في الاختبار المكتوب لبعض normal-text usages.
- P2: progressbar semantics، mobile-dialog keyboard، broad axe/SR gate.

### Observability

- لا request correlation/structured app logs contract.
- speech worker metrics/alerts غير كافية إذا فُعّل Production ASR.
- failed auth ليس security signal تشغيليًا واضحًا.

---

## 10. A08 — Full Journey / Integration / E2E

الـBrowser Vertical Slice قوي: Admin login، create student، student login، 30-question assessment، image/audio flows، human audio review، resume، learning/reinforcement slice، Student Details/reports.

لكن لا يكمل طالبًا واحدًا عبر browser/runtime من Pretest → L1/L2/L3 → Posttest كامل.

Backend longitudinal test يغطي transitions/history/reinforcement/L3/posttest authorization/reports، لكنه يستخدم persisted assessment snapshots ويعتمد على vertical slice لميكانيكا المتصفح/التسجيل.

لذلك evidence مقسوم ولا توجد Full Live Journey واحدة.

إضافيًا:

- `m09-release-readiness.yml` infrastructure/readiness/backup gate ولا يشغّل pytest أو Playwright.
- main CI integration يشغّل 5 E2E فقط.
- authenticated responsive matrix ناقصة.
- `browser-flow.spec.ts` legacy/loose archive candidate.
- badge visual E2E غير موجود.

---

## 11. A09 — مراجعة كل الفروع

تم جلب ومقارنة **20 فرعًا** بما فيها audit الحالي.

### Already contained — لا Merge

B01/B02/B03، Stage 02/03/04، recovery baselines، `recovery/ui-media-admin-overhaul`، `integration/official-content-reconciliation-2026-09-08`، و`integration/canonical-content-2026-09-08` كلها `ahead_by=0` بالنسبة لفرع المراجعة.

### `b04/asr-pipeline`

Diverged لكنه يملك 3 commits فريدة توثيقية فقط (`RESUME_HERE`, `STATUS`, `progress.json`)؛ لا ASR code فريد يحتاج نقلًا. `obsolete/archive-candidate`.

### Speech/Pronunciation Labs — **EXCLUDE FROM MERGE**

- `m08/speech-lab-google-stt`
- `b08/speech-lab-google-stt`
- `b08/arabic-pronunciation-lab`
- `b08/acoustic-pronunciation-evidence`

تحمل providers/lab/pronunciation code فريدًا وتجريبيًا، وبعضها diverged عن بعض. تبقى research reference فقط حتى اعتماد Production ASR مستقل.

### Deployment sandbox — لا Merge

`deployment/platform-sandbox` يحمل مواد نشر فريدة لكنه يعتمد Dockerfile ويذكر `HIMMA_TEMP_AUDIO_SKIP=true` وتجربة Vercel/Railway/Supabase قديمة. يستفاد منه مرجعيًا فقط في A11 لما لا يتعارض مع الحقيقة الحالية، ولا يعاد إحياء Docker أو bypass.

**نتيجة A09: لا يوجد فرع يجب دمجه الآن.**

---

## 12. Master Gap Register وA10

السجل الجامع:

`docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`

موجات A10 المعتمدة:

1. **W1 Academic / History Integrity** — P0 audio history + latest semantics + numeric evidence + completion truth.
2. **W2 Security / Speech boundaries** — auth/session/storage/queue/observability؛ Production ASR يبقى HOLD.
3. **W3 Admin / Student UX / Accessibility / Web reliability**.
4. **W4 Rewards / Badges / Media semantics**.
5. **W5 Historical cleanup / performance / test ownership**.
6. **W6 Final Quality Gates** على exact SHA.

بعد W6 فقط يبدأ A11 Railway finalization.

---

## 13. نقطة الاستكمال الدقيقة

**A00–A09 لا تعاد. A09 مغلق. Master Gap Register موجود.**

ابدأ الآن بـ **A10 / W1** بالترتيب:

1. توحيد canonical latest AudioSubmission lifecycle للـassessment.
2. جعل rerecord append-only بعد explicit open وعدم reopen التلقائي عند review.
3. فصل pending review summary عن navigation resolver.
4. إصلاح numeric rubric evidence بدل booleanization.
5. توحيد Level Completion truth للاستهلاك من Journey/Rewards مع الحفاظ على early promotion.
6. Regression tests لكل boundary قبل الانتقال إلى W2.

لا Merge، لا Deploy، لا Railway الآن.
