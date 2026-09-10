# منصة هِمّة — A08 Full Journey / Integration / E2E Audit

**التاريخ:** 2026-09-10  
**المرحلة:** A08  
**الحالة:** `STATIC + EXISTING-RUN EVIDENCE AUDIT COMPLETE / NO PRODUCTION FIX APPLIED`  
**المستودع:** `7eaur/himma-`  
**فرع المراجعة:** `audit/comprehensive-repository-review-2026-09-10`  
**قيد المرحلة:** لا Merge، لا Deploy، لا Docker، ولا ادعاء تشغيل جديد لم يحدث فعليًا.

---

## 1. الهدف

الغرض من A08 ليس عدّ ملفات الاختبار، بل إثبات ما إذا كانت البوابات الحالية تغطي الرحلة الحقيقية للطالب والمشرف من البداية إلى النهاية، وما إذا كانت نتائج CI الموجودة تصلح فعلًا كدليل Release. تم فحص Workflow ownership، مصفوفة E2E، الرحلة العمودية في المتصفح، الاختبار الطولي في Backend، responsive/mobile gates، media/accessibility tests، وسجل تشغيل CI المرجعي الفعلي.

---

## 2. الحقيقة التنفيذية عن CI الحالي

### 2.1 الـQuality Gate الرئيسي

`.github/workflows/ci.yml` يملك أربع طبقات رئيسية:

- Security: dependency audits + gitleaks + guards للـplaceholders/skips.
- Backend: PostgreSQL native، canonical validation، Alembic up/down/up، drift، seed idempotency، ثم pytest كامل.
- Frontend: TypeScript + ESLint + Jest + Next build.
- Integration: PostgreSQL + Redis + MinIO + FastAPI + Next + Playwright.

لكن Integration مشروط بنجاح Security + Backend + Frontend، ويشغّل فقط خمسة ملفات Playwright:

1. `vertical-slice.spec.ts`
2. `accessibility-integration.spec.ts`
3. `media-fidelity.spec.ts`
4. `question-experience.spec.ts`
5. `admin-responsive.spec.ts`

الـpush trigger لا يشمل `audit/*`، لذلك فرع المراجعة الحالي لا يملك تشغيلًا آليًا exact-HEAD.

### 2.2 تشغيل المرجع الحقيقي

التشغيل المرجعي `34419490966` على HEAD التنفيذي `7cb2192b0c31bc85dcf98a470023e9cc6f1598e0` أثبت:

- Security: PASS.
- Frontend: PASS.
- PostgreSQL startup: PASS.
- Canonical release validation: PASS — 125 عنصرًا، media verified.
- Alembic upgrade → downgrade base → upgrade: PASS.
- `alembic check`: PASS.
- canonical publication/seed idempotency: PASS.
- Backend pytest: **823 passed / 2 failed / 825 total**.
- Integration: **SKIPPED** نتيجة فشل Backend dependency gate.

الفشلان ليسا مجهولين:

- `test_uploaded_audio_stays_academically_pending_but_student_can_continue`: الـview يعيد `pending_audio_reviews=0` بدل 1 — نفس `AUD-BE-003` المثبت سابقًا.
- `test_listen_choose_image_restores_audio_and_clickable_image_mapping`: اختبار Recovery يبني catalog تاريخيًا 105 عنصرًا ويرى 3 صور في PRE-Q05 بدل canonical الحالي ذي الأربع صور — نفس `AUD-BE-004`.

في نفس التشغيل، `test_full_single_candidate_journey_keeps_history_and_reaches_exports` **نجح فعليًا**. هذا مهم لأنه يثبت أن الاختبار الطولي Backend نفسه كان أخضر على ذلك الـSHA، لكن لا يثبت مرور الـbrowser integration لأنه لم يبدأ أصلًا.

### 2.3 الـHEAD الحالي للمراجعة

عند فحص Actions للـHEAD `457dadb05d78311ab5e1a769ff96656c727cf401` لم توجد Workflow runs مرتبطة به. السبب البنيوي أن workflows الحالية لا تستهدف `audit/*` تلقائيًا. لذلك لا يوجد دليل Green جديد للـHEAD الحالي، ولا يجوز توريث Green قديم له تلقائيًا.

---

## 3. الرحلة العمودية في المتصفح — ماذا تثبت فعلًا؟

`apps/web/tests/e2e/vertical-slice.spec.ts` اختبار مهم وحقيقي، ويثبت طبقة كبيرة من المنتج:

- Landing → حماية Admin → Login المشرف.
- إنشاء طالب حقيقي عبر UI والحصول على كود 6 أرقام.
- Login الطالب.
- تنفيذ **30 سؤالًا قبليًا عبر المتصفح**.
- تمرير أسئلة الصور والتسجيلات.
- رفع التسجيل من MediaRecorder، انتظار المراجعة، دخول المشرف إلى audio review، التقييم، ثم عودة الطالب والمتابعة.
- بدء Learning Session حقيقية والتعامل مع النشاط، الصور، pending learning audio، والـreinforcement review عند الحاجة.
- العودة إلى Student Details والتأكد من بعض حالات التقدم والتكيف وPosttest eligibility.
- التحقق من التقارير وقائمة الطلاب.

لكن الاختبار لا يكمل طالبًا واحدًا عبر المتصفح من L1 إلى L2 ثم L3 ثم تنفيذ الـPosttest كاملًا. بعد جلسة التعلم الأولى يرجع إلى المشرف ويختبر الحالة الحالية، وقد ينتهي عند reinforcement review. لذلك هو **Vertical Slice قوي** وليس **Full Longitudinal Browser Journey**.

---

## 4. الاختبار الطولي Backend — ماذا يثبت وما الذي يتجاوزه؟

`services/api/test_m09_full_single_candidate_journey.py` يغطي الطالب نفسه عبر:

`Placement → L1 early promotion → L2 targeted reinforcement + verification → L2 early promotion → L3 10/10 → supervisor posttest authorization → posttest result → reports → XLSX/PDF exports`

ويتحقق من بقاء history وعدم جعل التقارير مصدرًا جديدًا للـmastery.

لكن الاختبار نفسه يعلن أنه لا يكرر browser/MinIO mechanics:

- Pretest/Posttest يتم تمثيلهما عبر persisted assessment snapshots مباشرة في DB.
- Learning evidence يُنشأ برمجيًا لتغطية handoffs الطولية.
- Audio learning evidence لا ينفذ تسجيلًا/ASR حيًا؛ يحفظ correctness مراجَعًا بشريًا دون اختراع metrics.
- نتيجة Posttest النهائية تُpersist مباشرة بدل تنفيذ 30 سؤالًا بعديًا عبر الـbrowser/API lifecycle.

هذا تصميم مقبول لاختبار domain longitudinal، لكنه ليس بديلًا عن رحلة E2E حقيقية واحدة.

---

## 5. فجوة Evidence الأساسية: Split Journey Proof

لدينا حاليًا قطعتا evidence متكاملتان ولكن منفصلتان:

- Browser Vertical Slice يثبت UI + recording + review + جزءًا من learning.
- Backend Longitudinal Test يثبت transitions + reinforcement + L3 + posttest authorization + reporting/history.

لا توجد بوابة واحدة تثبت الطالب نفسه، على نفس runtime، عبر:

`Student creation/login → 30 Pretest → audio reviews → placement → L1/L2/L3 الحقيقي حسب المسار → reinforcement/rerecord عند الحاجة → L3 completion → supervisor enable → 30 Posttest → reports/rewards`

ولذلك Release proof النهائي غير مغلق حتى بعد إصلاح bugs الحالية.

---

## 6. Responsive / Mobile evidence

### 6.1 Admin responsive

`admin-responsive.spec.ts` يغطي 390×844 و768×1024 فقط. Student Details conditional: الاختبار يفتحها فقط إذا صادف وجود student link صالح، ولا ينشئ fixture مضمونًا داخل الاختبار. هذا يعني أن صفحة Student Details يمكن أن تمر البوابة دون أن تُختبر أصلًا.

لا توجد المصفوفة المطلوبة صراحة:

`320 / 360 / 390 / 430 / 768 / Desktop`

ولا يوجد داخل هذا الاختبار عقد keyboard/focus كامل للـStudent Details.

### 6.2 Responsive smoke

`m04-responsive.yml` يشغّل `responsive-smoke.spec.ts` فقط، ويبدأ Next.js دون Backend. وهو يغطي `/`, `/student/login`, `/admin/login` على 360/390/768/1024/1440. هو useful visual smoke للـentry surfaces، لكنه ليس authenticated product journey ولا student/admin runtime mobile gate.

### 6.3 Student viewport safety

`student-viewport-safety.spec.ts` موجود لكنه **ليس ضمن main CI Integration**، ويغطي حالة واحدة 1280×720 لزر الاختبار القبلي. لا يغطي الهواتف ولا النشاط/التقوية/الـposttest.

---

## 7. E2E inventory وتصنيف الثقة

### Release-gate relevant حاليًا

- `vertical-slice.spec.ts`: قوي، لكنه slice وليس journey كاملة.
- `accessibility-integration.spec.ts`: مهم للوصولية، وتوجد source/test mismatches موثقة في A07.
- `media-fidelity.spec.ts`: يثبت real bytes وgenerated assets serving، مع gallery تركيبية لبعض الأصول.
- `question-experience.spec.ts`: يثبت أول 10 أسئلة readiness فقط، لا 30 ولا posttest.
- `admin-responsive.spec.ts`: مفيد لكن coverage للمقاسات/Student Details غير كامل.

### منفصل عن main Integration

- `responsive-smoke.spec.ts`: يشغله M04 منفصلًا فقط.
- `student-viewport-safety.spec.ts`: لا يشغله CI الرئيسي.
- بقية ملفات E2E تحتاج تصنيف ownership قبل تحويلها إلى gate.

### Legacy/loose candidate

`browser-flow.spec.ts` يحمل دلائل superseded/weak contract:

- hard-coded `http://localhost:3000`.
- fallbacks لكود طالب قديم بصيغة حرفية/شرطات مع أن العقد الحالي 6 أرقام.
- optional selectors و`catch` كثيرة.
- يستطيع الاستمرار حتى لو لم يجد question area ويكتفي بصورة/log.
- خطوة “logout” للطالب ليست assertion حقيقيًا على session revocation.

الحكم في A08: `OBSOLETE/SUPERSEDED TEST CANDIDATE` حتى dependency/history classification، لا حذف خلال التدقيق.

---

## 8. Release Readiness workflow ليس Full Release Test

`.github/workflows/m09-release-readiness.yml` يقوم بأعمال تشغيلية مهمة:

- canonical validation + migrations/seed.
- PostgreSQL/Redis/MinIO.
- readiness probe.
- التأكد من غياب temporary audio bypass.
- backup/restore لـPostgreSQL وobject storage.

لكن الملف **لا يشغّل `pytest` ولا Playwright**. لذلك تسميته `Release Readiness Gate` لا تعني أنه يغلق رحلة المنتج أو regression suite. حتى trigger paths يذكر `vertical-slice.spec.ts` لكن workflow لا ينفذ هذا الملف.

الحل الجذري في A10/A11 ليس نسخ كل الاختبارات عشوائيًا؛ بل تحديد Final Release Gate مركب ومعلن يجمع domain + UI + infrastructure evidence على exact SHA.

---

## 9. Accessibility/Visual tests في سياق A08

`accessibility-integration.spec.ts` موجود فعلًا ضمن main Integration، ويختبر:

- RTL + focus ring.
- Admin mobile touch target.
- reduced motion.
- 200%-zoom equivalent.
- contrast tokens.

A07 أثبت source/test mismatch في reduced-motion والcontrast. لكن بما أن Integration في التشغيل المرجعي لم يبدأ، لا نصنف ذلك كـ"E2E failed"؛ نصنفه **verified pre-run defect/test mismatch** يحتاج إصلاحًا ثم تشغيلًا فعليًا.

---

## 10. Rewards/Badges في الرحلة النهائية

A05 أثبت أن backend rewards موجود لكن visual/catalog contract غير مكتمل، ولا يوجد E2E يغلق:

`award evidence → canonical reward catalog/asset → Student UI → Admin UI → refresh → idempotency/history`

لذلك `AUD-BADGE-006` يبقى Release blocker وظيفيًا حتى A10 ثم Final E2E في A11.

---

## 11. سجل فجوات A08

| ID | Severity | Status | Evidence | Symptom | Root Cause | Correct Owner of Truth | Root Fix | Required Tests | Release Risk | Wave |
|---|---:|---|---|---|---|---|---|---|---|---|
| AUD-A08-001 | P1 | VERIFIED | CI triggers + current Actions query | لا CI exact-HEAD للـaudit branch | branch filters تستبعد `audit/*` | Final release CI orchestration | تشغيل exact-SHA gate بعد A10/قبل A11 وعدم توريث Green قديم | backend/frontend/security/integration exact SHA | HIGH | A11 Gate |
| AUD-A08-002 | P1 | VERIFIED | `vertical-slice.spec.ts` + `test_m09_full_single_candidate_journey.py` | لا طالب واحد يمر Full Live Journey من Pretest إلى Posttest عبر UI/runtime | evidence مقسوم بين browser slice وDB-domain longitudinal | Journey acceptance contract | بناء deterministic full journey E2E بعد إصلاح A10 | full student journey + audio/reinforcement + posttest + reports | HIGH | A10 tests/A11 |
| AUD-A08-003 | P1 | VERIFIED | `m09-release-readiness.yml` | workflow اسمه Release Readiness لكنه لا يشغل pytest/Playwright | readiness التشغيلي منفصل عن product regression | Release gate orchestration | جعل Final Gate مركبًا وواضح المسؤوليات بدل الاعتماد على الاسم | exact-SHA regression + readiness + backup/restore | HIGH | A11 |
| AUD-A08-004 | P2 | VERIFIED | E2E inventory + `ci.yml` | 5 فقط من ملفات E2E داخل main integration، وأخرى خارجها/قديمة | تراكم test generations بدون classification موحد | Test ownership manifest | تصنيف tests إلى release/targeted/visual/legacy ثم تشغيل المناسب | manifest + gate membership regression | MEDIUM | A10 |
| AUD-A08-005 | P1 | VERIFIED | `admin-responsive.spec.ts`, `responsive-smoke.spec.ts`, `student-viewport-safety.spec.ts` | mobile matrix غير مكتملة وStudent Details conditional | responsive gates موزعة حسب مراحل تاريخية | Product responsive acceptance | fixture deterministic + 320/360/390/430/768/Desktop لكل critical authenticated surface | overflow/touch/keyboard/screenshots | HIGH | A10 |
| AUD-A08-006 | P2 | VERIFIED | `browser-flow.spec.ts` | test legacy/loose قد يعطي ثقة زائفة | selectors/contracts تاريخية وفallbacks permissive | Test suite ownership | archive/supersede بعد إثبات عدم dependency، وعدم ترقيته لrelease gate | replacement coverage proof | MEDIUM | A10 cleanup |
| AUD-A08-007 | P1 | VERIFIED-PRE-RUN | A07 + accessibility E2E source | reduced-motion/contrast contract متوقع أن يكشف defects، لكن لم يُنفذ في baseline | Integration skipped بسبب Backend | Accessibility owner + CI | إصلاح A07 ثم تشغيل accessibility gate فعليًا | reduced motion + contrast + keyboard + zoom | HIGH | A10/A11 |
| AUD-A08-008 | P1 | OPEN | A05 + E2E inventory | لا Badge lifecycle visual E2E | reward visual/catalog layer غير مكتملة | Reward Catalog + Reward domain | إكمال A10 reward catalog/UI ثم E2E كامل | award→asset→student/admin→refresh/idempotency | HIGH | A10/A11 |
| AUD-A08-009 | P1 | VERIFIED | run `34419490966` | integration بأكمله blocked بفشلين Backend، أحدهما current bug والآخر legacy-test-world mismatch | gate لا يفرق product regression عن obsolete recovery contract | Backend test ownership | إصلاح AUD-BE-003 وتصنيف/تحديث AUD-BE-004 جذريًا قبل إعادة gate | pytest full then integration | HIGH | A10 |

---

## 12. ما لا يجب تغييره بسبب A08

- لا تُحذف الرحلة الطولية Backend؛ هي evidence domain قيّمة.
- لا يُلغى Vertical Slice؛ بل يُحتفظ به كاختبار browser حقيقي.
- لا تُشغّل كل ملفات E2E القديمة عشوائيًا كحل؛ أولًا classification وownership.
- لا يُعاد جعل pending learning audio blocking لمجرد تبسيط E2E.
- لا يُختصر early promotion إلى 10/10 لتسهيل journey test.
- لا تُختلق درجات ASR لإكمال رحلة الاختبار؛ human review أو approved provider فقط.

---

## 13. قرار A08

A08 مغلق **كتدقيق Evidence/Integration فقط**. لم يحدث Production code change، Merge، Deploy، أو تشغيل جديد لTest Suite على audit HEAD.

الحقيقة الحالية:

- لدينا domain longitudinal proof قوي وقد نجح في التشغيل المرجعي.
- لدينا browser vertical slice قوي، لكن لم يُنفذ في التشغيل المرجعي لأن Integration سُكبت.
- لا توجد Full Live Browser Journey واحدة حتى Posttest.
- Mobile/Student Details/Badges release evidence غير مكتمل.
- M09 readiness الحالي operational، وليس regression release gate كاملًا.

**نقطة الاستكمال التالية: A09 — مراجعة جميع الفروع بالـcompare وتصنيفها دون دمج.**
