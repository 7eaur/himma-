# منصة هِمّة — A10 / W2 Execution Checkpoint

**التاريخ:** 2026-09-12  
**المستودع:** `7eaur/himma-`  
**فرع التنفيذ:** `audit/comprehensive-repository-review-2026-09-10`  
**الموجة:** `A10/W2 — Security / Speech Boundaries`  
**الحالة:** `CLOSED GREEN`  

> هذا الملف يوثق الإغلاق التنفيذي النهائي لـ W2. لا يعيد فتح W2 ولا يجيز Merge/Deploy. أي محادثة جديدة يجب أن تعتبره دليلًا تاريخيًا ثابتًا، ثم تجلب HEAD الحالي وتتابع من الموجة النشطة.

---

## 1. دليل الإغلاق Exact-SHA

- **Verified SHA:** `77ac72174a9e21163f6341ea8e0fcc172269eac3`
- **Workflow:** `Himma CI — Quality Gate`
- **Run number:** `822`
- **Run ID:** `34548388760`
- **Conclusion:** `success`

النتيجة على SHA نفسه:

- Security: PASS.
- Frontend: PASS.
- Backend: PASS — 852 tests successful.
- Integration / Playwright E2E: PASS.
- Alembic upgrade → downgrade → upgrade: PASS.
- Alembic model drift: PASS.
- Canonical content validation: PASS.
- Canonical seed idempotency: PASS.

لا يوجد ادعاء PASS مبني على SHA مختلف.

---

## 2. ما أُغلق في W2

### AUD-SEC-001 — Auth abuse/rate limiting

تم اعتماد limiter مركزي لمسارات الدخول في البيئات المحمية:

- Redis atomic counter.
- حدود لكل IP ولكل identifier.
- identifier لا يُخزن خامًا؛ يستخدم HMAC-SHA256 بمفتاح التطبيق.
- لا ثقة في Forwarded IP بدون trusted proxy contract.
- protected runtime يفشل مغلقًا عند عدم توفر Redis بدل فتح باب brute-force.
- `429` مع Retry-After عند تجاوز الحدود.
- نجاح الدخول يمسح عداد identifier فقط.

### AUD-SEC-002 — Revocable authentication epochs

تمت إضافة `AuthSessionState` و`auth_epoch`:

- JWT يحمل epoch.
- تغيير كلمة مرور المشرف أو كود الطالب أو تعطيل الحساب يرفع epoch.
- JWT القديم يصبح غير صالح بعد تدوير credential.
- history لا يُحذف.

### AUD-SEC-003 — Protected runtime readiness + Secure cookies

تم ربط readiness بالأمان الفعلي:

- protected trial/production يتطلب Security mode صحيحًا.
- API secret بطول فعلي آمن.
- Secure cookie إلزامي في protected runtime.
- `/ready` لا يعلن الجاهزية عند فشل حدود الأمان.

### AUD-SEC-004 — Recording upload boundary

تم تشديد legacy recording boundary بدل ترك presigned upload بلا حد:

- `file_size` و`mime_type` مطلوبان قبل presign.
- الرفع المعتمد `audio/webm` فقط في هذا المسار.
- Content-Type وContent-Length مربوطان بالـpresigned request.
- completion يعيد التحقق من الحجم والنوع.
- object oversized يُزال best-effort.

### AUD-SEC-005 — Storage error sanitization

- لا يعود raw storage exception إلى العميل.
- أخطاء العميل عامة وآمنة.
- التشخيص الداخلي يعتمد request correlation بدل تسريب تفاصيل التخزين.

### AUD-A03-004 — Machine/Human adjudication boundary

- `SpeechAnalysis` machine output = **advisory**.
- Human Supervisor Review = **academic authority**.
- payload يوضح السلطة الأكاديمية ولا يخلط machine confidence بالحكم النهائي.

### AUD-A03-005 — ASR governance

تم إنشاء source-controlled governance boundary:

- `APPROVED_PRODUCTION_ASR_REGISTRY` بقي فارغًا عمدًا.
- environment variables لا تستطيع اختراع provider/model/calibration approval.
- threshold/version عشوائي لا يستطيع تحويل machine result إلى academic acceptance.

### AUD-A03-006 — Durable worker claim leases

- transactional claim.
- `FOR UPDATE SKIP LOCKED` semantics.
- worker owner + lease expiry.
- claim commit قبل provider call.
- stale processing لا يُستعاد إلا بعد lease expiry.
- idempotent enqueue محفوظ.

### AUD-A03-007 — Retry / dead-letter recovery

- bounded retry cycle.
- dead-letter state واضح.
- manual recovery audited.
- recovery يقفل الصف قبل التعديل.
- لا يعاد تشغيل job مكتمل له SpeechAnalysis نهائي في المكان نفسه.
- recovery يبدأ bounded cycle جديد مع حفظ previous status/attempt count في AuditLog.

### OBS-001 / OBS-003 — Correlation and security signals

أضيفت حدود observability الداعمة لـ W2:

- Request ID عبر API وBFF.
- قبول incoming request-id فقط بصيغة آمنة، وإلا يولد UUID.
- structured request logs.
- failed-auth security signals بدون raw access code/password/IP.
- identifier/IP يتم HMAC-hash قبل logging.

---

## 3. الاستثناء المقصود — AUD-A03-008

**Status: BLOCKED EXTERNAL APPROVAL**

لا يوجد Production ASR Provider معتمد حتى الآن.

ممنوع:

- دمج Speech/Pronunciation Lab branch واعتباره Production.
- اعتبار confidence وحده حكمًا أكاديميًا.
- اختراع approval من env/config.
- تشغيل auto-accept أكاديمي قبل provider + calibration + privacy + cost + governance approval.

إذا تمت الموافقة مستقبلًا، تفتح هذه الفجوة كمهمة مستقلة ولا يُعاد بناء W2 من الصفر.

---

## 4. القيود التي بقيت سارية بعد W2

- لا Docker.
- لا Merge.
- لا Deploy/Railway.
- لا Temporary Audio Skip.
- لا حذف Academic/Audio/Reward history.
- Speech/Pronunciation Lab branches = research only / EXCLUDE FROM MERGE.
- `deployment/platform-sandbox` = reference only.
- أي PASS لاحق يحتاج Exact-SHA evidence.

---

## 5. نقطة الانتقال

بعد هذا الإغلاق انتقل التنفيذ إلى:

`A10/W3 — Admin / Student UX / Accessibility / Web Reliability`

المصدر الأحدث لاستكمال العمل ليس هذا الملف وحده؛ اقرأ:

- `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-12_A10_W3_ACTIVE_AR.md`
- `docs/maintenance/HIMMA_A10_W3_EXECUTION_CHECKPOINT_2026-09-12_AR.md`
- `docs/ops/STATUS.md`
- `docs/ops/progress.json`
- `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
