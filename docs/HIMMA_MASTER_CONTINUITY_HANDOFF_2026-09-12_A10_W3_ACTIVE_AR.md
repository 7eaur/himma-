# منصة هِمّة — Master Continuity Handoff

**الإصدار:** 2026-09-12 — A10/W3 Active  
**المستودع:** `7eaur/himma-`  
**فرع التنفيذ الرسمي لهذه المرحلة:** `audit/comprehensive-repository-review-2026-09-10`  
**الحالة:** `A00–A09 CLOSED — W1 GREEN — W2 GREEN — W3 ACTIVE/RED — NO MERGE / NO DEPLOY`  

> **هذا الملف هو مرجع الاستكمال الأساسي للمحادثات الجديدة، ويحل محل handoff القديم المؤرخ 2026-09-10 من حيث نقطة الاستكمال.** لا تحذف المرجع القديم لأنه History، لكن لا تستخدم تعليماته القديمة التي تقول إن W1 ما زالت In Progress أو تمنع بدء W2؛ هذه المراحل تجاوزت ذلك وأُغلقت بأدلة Exact-SHA.

---

# 0. أمر الاستكمال السريع

إذا بدأت محادثة جديدة، نفّذ أولًا وليس تقريرًا فقط:

1. اجلب HEAD الحالي للفرع `audit/comprehensive-repository-review-2026-09-10`.
2. اقرأ هذا الملف كاملًا.
3. اقرأ:
   - `docs/ops/STATUS.md`
   - `docs/ops/progress.json`
   - `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
   - `docs/maintenance/HIMMA_A10_W1_EXECUTION_CHECKPOINT_2026-09-10_AR.md`
   - `docs/maintenance/HIMMA_A10_W2_EXECUTION_CHECKPOINT_2026-09-12_AR.md`
   - `docs/maintenance/HIMMA_A10_W3_EXECUTION_CHECKPOINT_2026-09-12_AR.md`
4. لا تعِد A00–A09.
5. لا تعِد W1 أو W2؛ كلاهما Closed Green.
6. افحص هل أضيف code commit بعد آخر code-bearing checkpoint المذكور هنا.
7. تابع من **أول gap غير مغلق فعليًا في W3**، مع إصلاح root cause واختبار exact SHA.
8. لا Merge/Deploy/Docker/Railway حتى الحدود النهائية.

---

# 1. ما هو مشروع هِمّة؟

هِمّة منصة تعليمية عربية موجهة لتقييم وتنمية القراءة لدى طلاب لديهم صعوبات في القراءة، بمسار تفاعلي منظم يعتمد المحتوى المعتمد، قراءة/كتابة/صوت، تصنيف مستوى، تعلم أساسي، تقوية موجهة، ثم قياس بعدي وتقارير إشرافية.

المسار المفاهيمي:

`دخول الطالب بكود → اختبار قبلي → تحليل/تصنيف → مستوى 1/2/3 → أنشطة Core → تقوية عند الضعف → ترقية/استكمال → اختبار بعدي → تقارير المشرف`

المنتج ليس مجرد Quiz. أهم invariants هي الحفاظ على التاريخ، عدم تزوير التحليل الصوتي، عدم خلط current pointer مع completion، وعدم جعل واجهة المستخدم تعرض حالة أكاديمية غير صحيحة.

---

# 2. Source of Truth والمعمارية

المسار المعتمد للمحتوى:

`approved/versioned source → deterministic structured projection → PostgreSQL runtime → structured API → deterministic renderer`

Canonical compiler/publisher هو owner للمحتوى. ممنوع إنشاء repair chains أو overlays جديدة فوق runtime لتغطية مشاكل المصدر.

الأرقام المعتمدة حاليًا:

- Canonical/runtime total = **125**.
- Pretest = **30**.
- Posttest = **30**.
- Learning runtime = **65**.
- Reinforcement = **35**.
- Skills = **44**.
- Projection contract = `structured_db_runtime_v1`.

أي فرضية تاريخية عن 105 عنصرًا ليست source of truth الحالي؛ إن ظهرت في test قديم تعامل معها كـtest ownership/history compatibility لا كسبب للرجوع عن 125.

---

# 3. العقد الأكاديمي الثابت

## 3.1 Placement بعد الاختبار القبلي

- `< 50%` → المستوى الأول.
- `50% <= score < 80%` → المستوى الثاني.
- `80% <= score <= 100%` → المستوى الثالث.

## 3.2 Adaptation V4

- Activity score `>=80` → success.
- `70..<80` → guided retry.
- `<70` → guided reinforcement.

## 3.3 Promotion / Completion

L1/L2 يسمحان early promotion فقط إذا تحققت جميع الحدود:

- >=6 Core completed في الجلسة الحالية.
- weighted mastery >=85.
- critical-skill coverage موجودة.
- critical skill floor >=70.
- لا unresolved reinforcement.
- لا supervisor blocker عند boundary.
- لا unresolved learning audio عند قرار irreversible.

قواعد إضافية:

- لا automatic demotion.
- الترقية مستوى واحد فقط.
- L3 لا ينتهي إلا بعد 10 Core.
- لا يوجد L4.
- أحدث 3 evidences صالحة من active learning session تدخل mastery بأوزان 50/30/20.
- `current_level` pointer وليس دليل completion للمستويات السابقة.
- manual override لا يصنع academic completion ولا badge.

---

# 4. عقد الصوت الثابت

## 4.1 Static approved audio

- Approved static audio IDs = 54.
- WAV = 54.
- MP3 = 54.
- required static gaps = 0 في العقد المعتمد الحالي.

## 4.2 Student recordings

- uploaded/pending = neutral academic state.
- pending learning audio لا يمنع same-level learning/navigation/support.
- unresolved learning audio يمنع irreversible promotion أو L3 completion فقط.
- assessment يمكن أن ينتظر Human Review وفق العقد الحالي.
- `rerecord_required` مهمة مؤجلة لا تصبح actionable حتى يفتحها الطالب صراحة.
- rerecord append-only: كل إعادة = AudioSubmission جديد.
- التسجيل السابق immutable history.
- latest AudioSubmission هو active state.
- graded فقط يمكن أن يدخل academic evidence.
- AudioReview rubric يحافظ على القيمة الرقمية؛ لا يحول إلى Boolean.
- Human Supervisor Review هو academic authority الحالي.

## 4.3 ASR governance

لا يوجد Production ASR provider معتمد.

Machine SpeechAnalysis = advisory فقط.

ممنوع اعتبار:

- confidence
- env threshold
- model version string
- branch تجريبي

موافقة أكاديمية.

`AUD-A03-008` يبقى BLOCKED EXTERNAL APPROVAL حتى اعتماد provider + calibration + privacy + cost + governance.

---

# 5. Governance وقواعد التنفيذ

هذه القيود غير قابلة للتجاوز ضمن A10:

- لا Docker.
- لا blind merge.
- لا merge للفروع الأساسية أثناء العمل الحالي.
- لا deploy / Railway قبل W6 Green وحدود A11.
- لا fake ASR.
- لا Temporary Audio Skip.
- لا حذف Academic history.
- لا حذف AudioSubmission history.
- لا حذف Reward evidence لمجرد cleanup.
- Speech/Pronunciation Lab branches = research only / EXCLUDE FROM MERGE.
- `deployment/platform-sandbox` = reference only / لا Docker assumptions ولا temporary audio skip revival.
- كل PASS يحتاج exact SHA + actual executed gate.
- لا تعديل test ليقبل bug حقيقي؛ أصلح root cause.

CI helper branches مثل `stage/a10-w3-ci` verification pointers فقط وليست release branches ولا تُدمج.

---

# 6. A00–A09 — CLOSED AUDIT

A00–A09 انتهت كتدقيق ولا تُعاد.

المراجع الرئيسية:

- `docs/maintenance/HIMMA_COMPREHENSIVE_REPOSITORY_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A03_AUDIO_SPEECH_REVIEW_ADAPTATION_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A04_ADMIN_MOBILE_DEEP_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A04_A05_ADMIN_BADGES_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A06_IMAGE_MEDIA_DEEP_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A07_SECURITY_PERFORMANCE_ACCESSIBILITY_OBSERVABILITY_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A08_FULL_JOURNEY_INTEGRATION_E2E_AUDIT_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A09_BRANCH_CLASSIFICATION_2026-09-10_AR.md`

A10 هو التنفيذ الجذري للـMaster Gap Register.

---

# 7. A10 / W1 — CLOSED GREEN

**Scope:** Academic / History Integrity.

Exact verified SHA:

`ea132c9afbe152d0afa5ae581c058ce3248a0c48`

Quality Gate:

- Run number: `813`
- Run ID: `34467329988`
- Security PASS.
- Frontend PASS.
- Backend PASS.
- Integration / Playwright PASS.

W1 أغلق جذريًا:

- append-only assessment rerecord.
- explicit learner open before rerecord.
- latest AudioSubmission owner.
- old submissions immutable.
- numeric AudioReview rubric evidence 0.0/0.1/0.7/1.0 بدون Boolean collapse.
- pending audio aggregate مستقل عن navigation target.
- canonical Level Completion owner.
- Journey وRewards يستهلكان completion truth نفسه.
- manual override لا يصنع completion/badge.
- L1/L2 early promotion 6–9 Core وفق البوابات.
- L3 10 Core.
- corrupt house WebP لـ `HIMMA-GEN-VOC-001` أُصلح دون تغيير Stable ID أو معنى `بيت`.

المرجع:

`docs/maintenance/HIMMA_A10_W1_EXECUTION_CHECKPOINT_2026-09-10_AR.md`

---

# 8. A10 / W2 — CLOSED GREEN

**Scope:** Security / Speech Boundaries.

Exact verified SHA:

`77ac72174a9e21163f6341ea8e0fcc172269eac3`

Quality Gate:

- Run number `822`
- Run ID `34548388760`
- conclusion `success`
- Security PASS.
- Frontend PASS.
- Backend PASS — 852 tests successful.
- Integration / Playwright PASS.
- Alembic upgrade/downgrade/upgrade PASS.
- Alembic model drift PASS.
- canonical validation + seed idempotency PASS.

W2 أغلق:

- Redis/HMAC auth rate limiting.
- no raw access-code identifier storage.
- JWT/session auth epoch revocation on credential rotation.
- protected runtime Secure cookie/readiness fail-closed.
- recording upload ContentLength/MIME limits pre-presign + completion recheck.
- raw storage errors sanitized.
- ASR source-controlled governance; env cannot grant approval.
- machine advisory + human academic authority.
- durable worker lease/claim.
- bounded retry/dead-letter/manual audit recovery.
- request correlation API+BFF.
- privacy-safe auth failure signals.

استثناء:

`AUD-A03-008` remains BLOCKED EXTERNAL APPROVAL.

المرجع:

`docs/maintenance/HIMMA_A10_W2_EXECUTION_CHECKPOINT_2026-09-12_AR.md`

---

# 9. A10 / W3 — ACTIVE

**Scope:** Admin / Student UX / Accessibility / Web Reliability.

## 9.1 آخر Code-bearing checkpoint قبل هذا التوثيق

`3962d101b2c1ba4c5294235dfac797687209cbfb`

Commit:

`fix(admin): align audio review with shared admin component contracts`

من W2 SHA حتى هذا SHA توجد 19 commits W3.

التغييرات الأساسية طالت:

- Admin audio review.
- Admin layout/mobile dialog.
- Settings tabs.
- Admin Student Detail.
- BFF cache policy + unit test.
- accessible dialog hook + test.
- canonical researcher journey route + test.
- review API student filter.
- status/progress docs.

## 9.2 ما تم في W3

### Accessible dialogs

`apps/web/src/hooks/useAccessibleDialog.ts`

- initial focus.
- Tab trap.
- Shift+Tab trap.
- Escape close.
- return focus.
- body scroll lock.

Admin mobile panel يستخدمه مع `role=dialog` و`aria-modal=true`.

### Settings accessibility

`apps/web/src/app/admin/(dashboard)/settings/page.tsx`

- tablist/tab/tabpanel semantics.
- aria-selected/controls/labelledby.
- roving tabindex.
- Left/Right/Home/End keyboard navigation.

### Canonical Admin Journey

`services/api/researcher_journey.py`

يعرض `build_journey_summary()` نفسه للمشرف بدل إعادة استنتاج completion من current_level.

### Student Detail truth/error states

Student Detail أصبح يفرق بين:

- loading.
- loaded-empty.
- error.

لـJourney/history/rewards، ويستهلك canonical per-level state.

### Audio review student context

`/pending-audio?student_id=...` supervisor filter مع الحفاظ على academic eligibility نفسها.

Admin Audio Review يحتفظ بسياق الطالب ويتيح العودة/إزالة الفلتر.

### BFF cache policy

تم فصل route-aware policy في:

`apps/web/src/app/api/[...path]/cachePolicy.ts`

لكن يوجد bug حقيقي حالي موضح أدناه.

---

# 10. نقطة التوقف الحالية بالضبط

لتحقق W3 استُخدم helper:

`stage/a10-w3-ci`

وتم تحريكه إلى:

`3962d101b2c1ba4c5294235dfac797687209cbfb`

Quality Gate الحالي:

- Run #`829`
- Run ID `34703574228`
- SHA `3962d101b2c1ba4c5294235dfac797687209cbfb`

آخر حالة موثقة أثناء إنشاء ملفات الاستمرارية:

- Security = PASS.
- Frontend TypeScript = PASS.
- ESLint = PASS.
- Frontend unit tests = FAIL.
- Build skipped بعد unit failure.
- Backend full tests كانت still in progress عند آخر poll.
- Integration لا يمكن اعتباره Green في هذا run بسبب Frontend failure.

## الفشل الحالي

`apps/web/src/app/api/[...path]/route.test.ts`

الحالة الفاشلة:

approved media GET + upstream `Cache-Control: private, no-store`.

المتوقع:

`private, no-store`

الحالي:

`public, max-age=86400`

### Root cause

`responseCacheControl()` في `cachePolicy.ts` يستخدم fallback public حتى عندما upstream **صرّح صراحة** بعدم التخزين.

### أول عمل يجب تنفيذه عند الاستكمال

إذا لم يوجد commit أحدث أصلحها:

- لا تغير الاختبار لقبول public.
- إذا upstream header يحتوي private/no-store → return private/no-store.
- explicit safe public يمكن تمريره.
- fallback public يستخدم فقط عندما header غائب، ولـsuccessful approved media GET/HEAD دون Set-Cookie.
- commit root fix.
- move `stage/a10-w3-ci` إلى SHA الجديد.
- شغّل full Quality Gate exact SHA.
- حل أي failure حقيقي جديد ثم أعد full gate.

W3 لا تصبح Green قبل Security+Frontend+Backend+Integration/Playwright جميعها Green على exact SHA نفسه.

راجع:

`docs/maintenance/HIMMA_A10_W3_EXECUTION_CHECKPOINT_2026-09-12_AR.md`

---

# 11. W3 — جميع الأعمال المتبقية

لا يكفي إصلاح cache وحده. أغلق هذه المجموعة كلها:

1. **AUD-A04-001** — استكمال AdminUI/presentation unification؛ لا تترك Student Detail/Settings/Account في style islands غير مبررة.
2. **AUD-A04-002** — اختبارات partial source failure وعدم عرض zero/empty كأنه حقيقة.
3. **AUD-A04-003** — verify canonical Journey rendering للـoverride/skipped/early promotion/active/completed scenarios.
4. **AUD-A04-005** — deterministic responsive Student Detail عند 320/360/390/430/768/Desktop.
5. **AUD-A04-006** — final keyboard-only dialog regression على exact gate.
6. **AUD-A04-007** — Settings shared tokens + ARIA/keyboard final verification.
7. **AUD-A04-008** — Student Detail → filtered Audio Review → state/back-context flow.
8. **AUD-PERF-001** — BFF cache bug الحالي + safe media/private JSON contract.
9. **AUD-PERF-004** — إزالة runtime Google Fonts dependency واعتماد local/build-time strategy.
10. **AUD-A11Y-001** — global `prefers-reduced-motion` behavior.
11. **AUD-A11Y-002** — semantic accessible text/action colors مع الحفاظ على brand palette.
12. **AUD-A11Y-003** — progressbar semantics للحالات الرقمية الحقيقية.
13. Scenario integrity E2E: skipped ≠ completed؛ manual override ≠ completion؛ pending audio لا يصنع completion؛ rerecord history immutable؛ partial failure ليس success؛ mobile/keyboard نفس الحقيقة الأكاديمية.

بعد exact W3 Green: حدث W3 checkpoint + STATUS + progress + Gap Register status/evidence، ثم انتقل W4.

---

# 12. W4 — Rewards / Badges / Media Semantics

هذه الموجة مهمة جدًا بناءً على آخر مراجعة من المستخدم.

## 12.1 النظام الحالي للمكافآت

Backend لديه `RewardEvent` idempotent مع unique `(student_id, reward_key)`.

نجوم النشاط الحالية:

- 3 = completed without help/retry.
- 2 = hint without retry.
- 1 = completed after retries.

Badge eligibility تستخدم canonical `level_was_completed()`، وهذه نقطة صحيحة من W1:

- early promotion في L1/L2 يمكن أن يعطي completion badge.
- manual override وحده لا يعطي badge.
- L3 يتطلب 10 Core.

Pending/ungraded audio لا يجب أن يمنح reward أكاديميًا مبكرًا لأن `_attempt_signal()` لا يعد evidence صالحًا حتى graded.

## 12.2 Approved badge assets

المطلوب اعتماد catalog مركزي واحد يربط:

- `BDG-01` نجمة واحدة.
- `BDG-02` نجمتان.
- `BDG-03` ثلاث نجوم.
- `BDG-04` مستكشف الحروف.
- `BDG-05` بطل الكلمات.
- `BDG-06` نجم الفهم.

لا تولد assets بديلة طالما الـapproved kit موجود.

## 12.3 الفجوات المؤكدة

- Student Home يعرض total stars لكنه لا يعرض badge gallery/canonical assets بصورة مكتملة.
- Admin Student Detail badge presentation نصي أكثر من كونه shared catalog presentation.
- L3 backend label حاليًا `قارئ متميز` بينما approved catalog `نجم الفهم`؛ يجب migration-compatible display لا حذف التاريخ.
- Reward API لا يحمل stable asset/catalog identity/version بصورة كافية.
- Reward API failure لا يجوز أن يظهر `0` كأن الطالب لم يكسب شيئًا.
- full reward lifecycle E2E غير مكتمل.

## 12.4 فجوة منطق النجوم المهمة

`_stars_for_attempt()` يعتمد structured retries/hints، لكنه لا يربط audio rerecord history كـretry.

خطر حالي:

طالب يعيد تسجيل الصوت ثم يحصل نظريًا على 3 نجوم وكأنه أنجز بلا إعادة.

Root fix في W4:

- audio rerecord الفعلي يدخل effort/retry semantics.
- لا تحذف submissions القديمة.
- لا تستخدم machine confidence لذلك.
- reward event يظل idempotent.
- pending audio لا يمنح نجومًا مبكرًا.
- اختبر تراكم النجوم وتسلسلها وعدم duplicate award.

## 12.5 Media semantics

`AUD-MEDIA-002` = Academic Review Required.

لا تغيّر lexical stimulus asset آليًا دون اعتماد أكاديمي.

الواجهة يجب أن تضمن:

- الصور التعليمية بدون distortion.
- responsive sizing.
- semantic role محفوظ.
- alt meaningful للمحتوى الدلالي.
- decorative images بـalt فارغ عند المناسب.

---

# 13. Typography / images / responsive logic المطلوب تثبيته

الـCSS الحالي يستخدم Tajawal للطالب وIBM Plex Sans Arabic للإدارة، لكن يوجد runtime Google Fonts import في `globals.css`.

W3 يجب أن ينقل الخطوط إلى local/build-time strategy حتى لا يتغير التصميم عند فشل الشبكة الخارجية.

الفحص النهائي يجب أن يشمل:

- Arabic line wrapping.
- no clipping عند zoom/mobile.
- `rem`/responsive scale بدل اعتماد pixel جامد في الواجهات المهمة.
- `clamp()` حيث يخدم الهرمية بدون تعقيد.
- الصور لا تتمدد بنسبة خاطئة.
- object-fit مناسب حسب الدلالة.
- 320px حتى Desktop.
- reduced motion.
- accessible focus/contrast.

---

# 14. W5 — Historical Cleanup / Performance / Test Ownership

بعد W4، لا تبدأ cleanup أعمى.

المجالات:

- `AUD-BE-001`: تصنيف runtime service generations وتوحيد shared primitives قبل retire.
- `AUD-BE-002`: old seed/projection/correction scripts إلى runtime/migration/test/dead مع dependency proof.
- `AUD-BE-004`: legacy 105-world tests منفصلة عن canonical 125.
- `AUD-BADGE-009`: reward history cascade risk قبل destructive cleanup/reset.
- `AUD-MEDIA-003/004/005`: unused/duplicate assets لا تحذف دون proof؛ approved unused قد تكون reserve.
- `AUD-PERF-002`: N+1 في researcher students projection.
- `AUD-PERF-003`: Notifications GET لا ينبغي أن يقوم sync/upsert/commit في read polling path.
- `/admin/account` duplicate retirement فقط بعد إثبات عدم وجود unique dependency.
- legacy recording path cleanup فقط إن ثبت dead، وإلا يحافظ على الحدود الأمنية الحالية.

---

# 15. W6 — Final Exact-SHA Quality Gates

W6 هو بوابة الإطلاق، وليس مجرد documentation.

المطلوب على SHA واحد:

- Security PASS.
- Frontend TypeScript PASS.
- ESLint PASS.
- Frontend unit tests PASS.
- Next build PASS.
- Backend full tests PASS.
- Alembic upgrade/downgrade/upgrade PASS.
- model drift PASS.
- canonical validation + seed idempotency PASS.
- Integration/Playwright PASS.
- responsive viewport matrix PASS.
- accessibility regressions PASS.
- full reward award→asset→Student/Admin→refresh/idempotency E2E PASS.
- scenario integrity PASS.

لا Merge/Release/Deploy قبل W6 Green.

---

# 16. A11 — Deployment / Railway

A11 يبدأ فقط بعد W6 Green.

حتى ذلك الوقت:

- لا deploy.
- لا final Railway configuration.
- لا Docker.
- لا اعتبار sandbox reference production authority.

Deploy-specific items مثل security headers النهائية، domain/hosting وcredential rotation تُحسم عند الحدود المناسبة وبعد Green codebase.

---

# 17. القرارات الخارجية المفتوحة

هذه لا تُحل بالتخمين:

- Production ASR provider/model/calibration/privacy/cost/governance.
- intervention/session duration قبل study activation.
- child-recording retention policy قبل real-child production data.
- domain/hosting/deployment settings.
- supervising organization details/logo قبل final report signoff.
- credential rotation قبل production إذا ثبت historical exposure.

سجّلها BLOCKED/EXTERNAL ولا تخترع values.

---

# 18. Branch classification المختصر

- `audit/comprehensive-repository-review-2026-09-10` = current remediation work owner.
- `stage/a10-w3-ci` = temporary CI trigger/verification pointer only.
- old stage/recovery/integration branches = historical evidence unless Gap Register يثبت dependency محددة.
- Speech/Pronunciation Lab branches = EXCLUDE FROM MERGE / research only.
- `deployment/platform-sandbox` = reference only.

لا تدمج branch لمجرد أنها أحدث تاريخيًا.

---

# 19. ملفات يجب اعتبارها معًا عند أي استكمال

ترتيب القراءة المقترح:

1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-12_A10_W3_ACTIVE_AR.md` — هذا الملف.
2. `docs/ops/STATUS.md` — الحالة المختصرة التنفيذية.
3. `docs/ops/progress.json` — machine-readable progress.
4. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md` — جميع gaps والموجات.
5. `docs/maintenance/HIMMA_A10_W1_EXECUTION_CHECKPOINT_2026-09-10_AR.md` — W1 evidence.
6. `docs/maintenance/HIMMA_A10_W2_EXECUTION_CHECKPOINT_2026-09-12_AR.md` — W2 evidence.
7. `docs/maintenance/HIMMA_A10_W3_EXECUTION_CHECKPOINT_2026-09-12_AR.md` — مكان التوقف العملي.
8. Audit-specific docs عند الحاجة فقط؛ لا تعِد audit من الصفر.

---

# 20. تعريف Done الحقيقي

لا تعتبر المشروع مكتملًا لأن الصفحات تعمل يدويًا أو لأن بعض tests خضراء.

Done يعني:

- كل Gap في scope A10 إما CLOSED مع evidence أو BLOCKED EXTERNAL موثق.
- Academic contracts متسقة بين Backend/UI/Reports/Rewards.
- no hidden bypasses.
- no misleading UX state.
- approved media/rewards integrated semantically.
- accessibility/responsive/performance gates مثبتة.
- exact-SHA W6 Green.
- ثم فقط تبدأ release/deploy governance.

---

# 21. Prompt جاهز لمحادثة جديدة

انسخ الفكرة التالية أو استخدم `NEXT_CONVERSATION_PROMPT.md` بعد إنشائه في المستودع:

> اعمل كالمسؤول الهندسي الكامل عن منصة هِمّة في `7eaur/himma-`. ابدأ بجلب HEAD الحالي للفرع `audit/comprehensive-repository-review-2026-09-10` ثم اقرأ `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-12_A10_W3_ACTIVE_AR.md` و`docs/ops/STATUS.md` و`docs/ops/progress.json` وMaster Gap Register وW1/W2/W3 checkpoints. لا تعِد A00–A09 ولا W1/W2. تابع من أول مهمة W3 غير مكتملة، أصلح root cause واختبر exact SHA. لا Docker ولا Merge ولا Deploy ولا Production ASR افتراضي. لا تقل Green بدون Security+Frontend+Backend+Integration/Playwright على SHA نفسه. بعد W3 أكمل W4 ثم W5 ثم W6، وA11 فقط بعد W6 Green.
