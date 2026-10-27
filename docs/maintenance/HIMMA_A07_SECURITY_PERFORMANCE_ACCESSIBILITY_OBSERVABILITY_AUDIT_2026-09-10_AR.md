# هِمّة — A07 الأمن، الأداء، الوصولية، والمراقبة التشغيلية

**التاريخ:** 2026-09-10  
**الحالة:** `STATIC/SOURCE AUDIT COMPLETE — NO PRODUCTION FIX — NO MERGE — NO DEPLOY`  
**الفرع:** `audit/comprehensive-repository-review-2026-09-10`

---

## 1. نطاق الجولة

تمت مراجعة حدود المصادقة والجلسات، Student/Supervisor authorization، التسجيلات والتخزين، readiness، BFF proxy، CI security gates، واجهات الطالب الأساسية، Design tokens/CSS، اختبارات accessibility الحالية، مسارات الاستعلام الأعلى تكرارًا، وSpeech worker observability.

هذه الجولة لا تدعي Penetration Test خارجيًا ولا Lighthouse/axe/browser run جديدًا. النتائج أدناه مبنية على source/static evidence وعلى تشغيل CI المرجعي الموثق سابقًا فقط.

---

## 2. ضوابط موجودة ويجب الحفاظ عليها

### Security positives

- `API_SECRET_KEY` مطلوب عند startup ويجب أن يكون 32 UTF-8 bytes على الأقل.
- JWT يسمح `HS256` فقط ويشترط `sub`, `role`, `exp`، ويوجد regression للتوقيع المعدل/expired/malformed/non-allowlisted algorithm.
- Supervisor/Student dependencies تعيد تحميل الكيان من DB وتتحقق من `is_active` والـrole، فلا يكفي JWT قديم لحساب معطل.
- cookies `HttpOnly`, `SameSite=Lax`، وتصبح `Secure` عندما `ENV=production`.
- assessment session ownership يربط session بالطالب، وaudio submission يتحقق من prefix `audio/{student.id}/`.
- media serving يقبل manifest asset IDs لا arbitrary filesystem paths.
- readiness report لا يسرب raw dependency exceptions أو secrets.
- CI security job موجود ويشمل `pip-audit`, `npm audit --audit-level=high`, `gitleaks`، وحراسة TODO/mock/skipped tests في production paths.
- الجرد المرجعي السابق سجّل Security job = PASS على HEAD الأساس.

### Operational positives

- `/health` liveness رخيص.
- `/ready` يتحقق من config + PostgreSQL + canonical projection digest + approved audio package + object storage + Redis.
- canonical DB projection readiness يفشل closed عند drift/version/digest mismatch.
- Speech worker لا يخترع ASR إذا provider غير معتمد.

---

## 3. Security findings

### AUD-SEC-001 — لا Rate Limiting لمسارات الدخول

`/auth/student-login` يعتمد على **access code من 6 أرقام** كعامل الدخول الوحيد للطالب. `main.py` لا يركب rate-limit middleware، و`requirements.txt` لا يظهر طبقة rate limiter، وRedis الموجود مستخدم كاعتمادية تشغيلية لا كحماية login.

Supervisor login كذلك بلا throttling/backoff.

**الأثر:** مساحة 6 أرقام صغيرة نسبيًا ويمكن brute-force/enumerate عبر الشبكة إذا أصبح endpoint عامًا، حتى مع رسائل خطأ عامة.

**Severity:** P1 قبل Production.

**Root fix:** rate limit مركزي على auth endpoints، على الأقل per-IP + per-identifier/backoff، مع generic response وعدم تسجيل السر في logs. يجب ألا يكون الحل داخل React أو client delay.

**Required tests:** repeated failures -> 429/backoff؛ successful login بعد window؛ لا account enumeration؛ proxy/origin IP contract موثق خلف Railway.

---

### AUD-SEC-002 — تغيير access code/password لا يلغي الجلسات القائمة

JWT يحمل `sub/role/iat/exp` فقط ولا يملك `session_version/auth_epoch/jti` قابلًا للإبطال. تغيير Student access code أو Supervisor password يغير credential في DB لكنه لا يغير claim يُقارن في كل request.

لذلك:

- تدوير access code لا يلغي token الطالب المسروق/القديم فورًا.
- تغيير كلمة مرور المشرف لا يلغي token مشرف قائم حتى انتهاء `exp` (الافتراضي 24 ساعة)، إلا إذا تم تعطيل الحساب بالكامل.

**Severity:** P1 للطالب لأن access code هو عامل الدخول الوحيد؛ P2 للمشرف ضمن نفس root gap.

**Root fix:** auth/session version على Student/User أو durable session table. تضمينه في JWT ومقارنته في dependency، وزيادته عند password/access-code rotation/explicit revoke.

**Migration risk:** إضافة field default واضح دون إبطال تاريخ أكاديمي؛ الجلسات الحالية يمكن إبطالها مرة واحدة عند rollout بقرار موثق.

---

### AUD-SEC-003 — `Secure` cookie يعتمد على ENV لكن readiness لا يفرض production mode

`auth._set_token_cookie()` يجعل `secure = (ENV == "production")`، بينما `_REQUIRED_CONFIG` في readiness لا يتضمن `ENV`.

بالتالي يمكن نظريًا أن يمر `/ready` مع config/storage/DB سليمة و`ENV` غير مضبوط، بينما auth cookie بلا Secure flag.

**Severity:** P1 release configuration gap.

**Root fix:** runtime environment contract واحد: في production يجب أن يفشل startup/readiness إذا `ENV != production` أو إذا cookie/security-mode غير متوافق مع public HTTPS deployment. لا تعتمد على ذاكرة المشغل.

---

### AUD-SEC-004 — Presigned recording upload لا يفرض حدًا أعلى للحجم

`recordings.py` ما زال Router mounted.

`POST /recordings/init` ينشئ presigned `put_object` لمدة 15 دقيقة مع ContentType، لكن لا يفرض max content length. `POST /recordings/complete` يتحقق فقط من:

- prefix يخص الطالب.
- وجود object.
- الحجم أكبر من 1KB.

ولا يرفض object أكبر من `MAX_AUDIO_BYTES`.

المسار الحديث للـassessment/activity يرفع عبر API ويملك 10MB limit، لكن endpoint القديم ما زال reachable لطالب authenticated حتى لو لم تستخدمه الواجهة الحالية.

**الأثر:** storage/cost denial by oversized uploads إلى object store.

**Severity:** P1.

**Root fix:** إما إغلاق legacy presigned route بعد dependency proof، أو استخدام presigned POST policy/content-length-range أو server-side enforcement موثوق قبل قبول object مع cleanup للأحجام المرفوضة. لا يكفي فحص الحجم بعد أن دُفع التخزين بالفعل.

---

### AUD-SEC-005 — Storage errors قد تسرب تفاصيل بنية تحتية

`recordings.py` يعيد في بعض 503 responses نص الاستثناء (`Storage unavailable: {e}`, `Storage error: {e}`, و`detail=str(e)` في stream-by-key).

**Severity:** P2 information exposure.

**Root fix:** رسائل عامة للعميل + structured server log داخلي مع correlation id. readiness الحالي نموذج جيد لأنه يعيد `unavailable` فقط.

---

### AUD-SEC-006 — Security response headers غير معرفة في التطبيق

`next.config.ts` لا يعرّف CSP/frame-ancestors/nosniff/referrer policy وغيرها، ولا يوجد في `main.py` security-header middleware.

قد تضيف Railway أو reverse proxy بعض headers، لذلك لا نصنفها incident مثبتًا في runtime الحالي.

**Severity:** P2 / A11 verification required.

**Root fix:** owner واضح للـheaders (Next أو edge/proxy) + automated header smoke test على public deployment. لا تضاعف policies متعارضة بين طبقتين.

---

## 4. Performance findings

### AUD-PERF-001 — BFF يلغي cache الخاص بالوسائط المعتمدة

Backend `/media/{asset_id}` يعيد:

`Cache-Control: public, max-age=86400, immutable`

لكن Next BFF `src/app/api/[...path]/route.ts` يعيد لكل upstream response بلا استثناء:

`cache-control: private, no-store`

والـlearner payloads تشير إلى `/api/media/{asset_id}`، أي أن المتصفح يمر فعليًا عبر هذا BFF.

**الأثر:** الصور/الأصوات التعليمية الثابتة يعاد تنزيلها بدل الاستفادة من cache، ما يرفع latency/bandwidth خصوصًا في شبكة بطيئة أو عبر جولات عديدة.

**Severity:** P1 performance/reliability.

**Root fix:** cache policy route-aware: authenticated JSON يبقى `private/no-store`، لكن GET/HEAD للـapproved immutable media يمكن أن يمرر safe public cache headers. يجب عدم تمرير cache عامة لأي payload طالب خاص.

**Required tests:** media response عبر Next = expected public cache; auth/profile/reports = no-store; repeated media request browser/network regression.

---

### AUD-PERF-002 — `/researcher/students` N+1 query pattern

`list_students()` يجلب الطلاب ثم يستدعي `_student_payload()` لكل طالب. كل payload ينفذ عدة queries مستقلة:

- pretest completion.
- posttest completion.
- core session + count.
- `build_journey_summary()` الذي يستعلم pretest، promotion decisions، core sessions، counts لكل session/level، posttest.

مع الحد الحالي المتوقع <=50 طالبًا قد يبقى مقبولًا وظيفيًا، لكنه scaling/query-count debt واضح ويزداد مع sessions التاريخية.

**Severity:** P2.

**Root fix:** batched dashboard projection/query أو aggregate view/service، لا cache عشوائي يخفي stale academic state.

**Required tests:** query-count budget لـ1/10/50 طالبًا + response-time budget على PostgreSQL.

---

### AUD-PERF-003 — Notification GET يقوم بمزامنة وكتابة كاملة

`GET /researcher/notifications` يستدعي `_sync_actionable_notifications()` الذي:

- يستعلم كل uploaded audio.
- upserts notifications.
- يقرأ stale rows ويعدلها.
- يستعلم كل escalated cycles.
- `commit()`.

أي أن GET ليس read-only، وقد يعيد نفس reconciliation مع كل polling للواجهة.

**Severity:** P2 performance/HTTP ownership.

**Root fix:** materialize عند domain transition أو job/event واضح، واجعل GET يقرأ inbox فقط. إذا بقي reconciliation safety-net فيكون scheduled/explicit وليس كل poll.

---

### AUD-PERF-004 — Google Fonts `@import` runtime dependency

`globals.css` يبدأ بـGoogle Fonts `@import` لـIBM Plex Sans Arabic/Tajawal. هذا request خارجي blocking نسبيًا ويضيف dependency على شبكة/طرف ثالث قبل اكتمال الخط.

**Severity:** P2 performance/privacy/reliability.

**Root fix:** self-host/Next font strategy مع preload/subset/fallback مناسب بعد مراجعة الترخيص والحزمة؛ لا تضف font payload ضخم بلا قياس.

---

## 5. Accessibility findings

### AUD-A11Y-001 — Reduced Motion contract موجود في الاختبار لكن implementation غير موجود

`accessibility-integration.spec.ts` يطلب عند `prefers-reduced-motion: reduce` أن تصبح animation/transition <=0.02ms على student login.

لكن `globals.css` يحتوي حركات كثيرة (`pop`, `fadeUp`, `float`, `pulse-ring`, orbit, smooth scroll...) ولا يوجد `@media (prefers-reduced-motion: reduce)` في الملف.

الـE2E المذكور لم يصل إلى التشغيل في CI المرجعي لأن Backend gate فشل قبله، لذلك لا يجوز القول إنه passed.

**Severity:** P1 accessibility gate defect.

**Root fix:** global reduced-motion policy يعطل decorative animation/smooth scrolling ويحتفظ فقط بالحركة الضرورية وظيفيًا مع بديل ثابت.

---

### AUD-A11Y-002 — Palette tokens تفشل gate التباين المكتوب أصلًا

اختبار accessibility نفسه يشترط >=4.5:1 لـprimary وgreen على white.

القيم الحالية في `globals.css`:

- `--color-primary: #347FD9` -> تقريبًا **4.05:1** على الأبيض.
- `--color-green: #51B985` -> تقريبًا **2.43:1** على الأبيض.
- navy على background يتجاوز 4.5 بوضوح.

إذًا primary/green يفشلان شرط normal-text الذي كتبه المشروع نفسه. وهذا يؤثر على utilities/text/button combinations حين تستخدم كنص عادي على white.

**Severity:** P1 WCAG/design-token gate.

**Root fix:** لا تغير ألوان الهوية عشوائيًا. أنشئ accessible semantic text/action variants (dark shades) مع بقاء brand/display color حيث يسمح contrast/large-text/non-text use، ثم audit usages.

---

### AUD-A11Y-003 — Progress bars بلا progressbar semantics كاملة

Assessment session progress track لديه `aria-label="التقدم X%"` لكنه عنصر `div` بلا `role="progressbar"` ولا `aria-valuenow/min/max`.

**Severity:** P2.

**Root fix:** shared accessible Progress primitive على assessment + learning/admin حيث ينطبق، مع role/value semantics ونص مرئي لا يعتمد على اللون وحده.

---

### AUD-A11Y-004 — Mobile admin dialog keyboard contract ما زال مفتوحًا

من A04: mobile Admin dialog يملك role/name وتوجد focus outlines، لكن لا يوجد contract مثبت لـfocus trap, Escape close, return focus. الاختبار الحالي يفتح dialog ويتحقق من touch target فقط.

**Severity:** P2، carry from A04.

---

### AUD-A11Y-005 — لا Automated semantic a11y engine شامل

الحزمة لا تتضمن axe-core/playwright-axe؛ اختبار accessibility الحالي custom ومفيد لكنه يغطي subset محدد. لا نستنتج من ذلك أن الموقع غير متاح، لكن release gate لا يملك automated scan للـARIA/name/role/contrast tree على المسارات الرئيسية.

**Severity:** P2 gate gap.

**Root fix:** أضف automated a11y scan للمسارات الأساسية بعد إصلاح known blockers، مع manual keyboard/screen-reader smoke للStudent flow وAdmin dialog؛ لا تعتمد على scanner وحده.

---

## 6. Observability findings

### AUD-OBS-001 — لا request correlation/structured application logging contract

`main.py` لا يركب request-id/correlation middleware، ولا توجد طبقة structured logging موحدة ظاهرة. توجد `AuditLog` للأحداث الأكاديمية/الإدارية، لكنها ليست بديلًا لـoperational logs.

**الأثر:** عند خطأ 500 أو storage/provider failure يصعب ربط browser request بAPI log/DB operation/worker job دون معرف موحد.

**Severity:** P2.

**Root fix:** request ID يولد/يمر عبر BFF→API، structured logs sanitized مع route/status/latency/correlation، وعدم تسجيل access tokens/passwords/presigned URLs/raw child data.

---

### AUD-OBS-002 — Speech worker observability غير كافية للإنتاج

`run_cycle()` يرجع counts (`discovered/processed/blocked_provider`) وCLI يطبع dict فقط. لا توجد مقاييس/alerts واضحة لـ:

- queue depth.
- oldest pending age.
- retries/dead-letter age.
- provider latency/error rate.
- jobs stuck processing.
- duplicate claims/concurrency.

وهذا يرتبط بفجوات A03 claim/retry.

**Severity:** P1 قبل تفعيل Production ASR. حاليًا provider غير معتمد، لذلك لا نعاملها outage قائمًا.

**Root fix:** queue metrics + structured job events + alert thresholds بعد حسم atomic claiming/retry contract، ولا تفعّل worker production provider قبل ذلك.

---

### AUD-OBS-003 — Failed authentication غير ممثل كإشارة تشغيلية/أمنية

Successful login يُسجل AuditLog، لكن failed logins تخرج 401 فقط ولا يوجد rate-limit/security event counter مثبت.

**Severity:** P2، مرتبط بـAUD-SEC-001.

**Root fix:** aggregate failed-login telemetry بدون تخزين password/access code الخام، مع alert على bursts وحدود الخصوصية.

---

## 7. Master Gap Register — A07

| ID | Severity | Status | Owner | Root fix | Required gate |
|---|---:|---|---|---|---|
| AUD-SEC-001 | P1 | VERIFIED | Auth/API edge | auth rate limiting/backoff | brute-force/rate-limit integration |
| AUD-SEC-002 | P1 | VERIFIED | Auth session model | auth_epoch/session_version revocation | credential-rotation revokes old JWT |
| AUD-SEC-003 | P1 | VERIFIED | Runtime config/readiness | require production security mode | production config/readiness smoke |
| AUD-SEC-004 | P1 | VERIFIED | Recording upload/storage | bounded presigned policy or retire route | oversized upload rejected/cost-safe |
| AUD-SEC-005 | P2 | VERIFIED | Storage error boundary | sanitized client errors + internal logs | no raw provider detail |
| AUD-SEC-006 | P2 | NEEDS DEPLOY VERIFY | Web/edge | explicit security headers owner | deployed header smoke |
| AUD-PERF-001 | P1 | VERIFIED | Next BFF/media | preserve safe immutable media cache | proxy cache contract |
| AUD-PERF-002 | P2 | VERIFIED | Admin student projection | batched aggregate query | query-count/perf budget |
| AUD-PERF-003 | P2 | VERIFIED | Notification domain | write on transition; GET read-only | polling/reconciliation tests |
| AUD-PERF-004 | P2 | VERIFIED | Web typography | local/build-time font strategy | network/perf smoke |
| AUD-A11Y-001 | P1 | VERIFIED | Global design system | reduced-motion policy | existing E2E must pass |
| AUD-A11Y-002 | P1 | VERIFIED | Design tokens | accessible semantic dark variants | contrast gate >=4.5 where normal text |
| AUD-A11Y-003 | P2 | VERIFIED | Shared UI primitives | semantic progress component | role/value screen-reader test |
| AUD-A11Y-004 | P2 | CARRY | Admin shell | focus trap/Escape/return focus | keyboard E2E |
| AUD-A11Y-005 | P2 | OPEN GATE | QA | axe + manual keyboard/SR smoke | major-route a11y suite |
| AUD-OBS-001 | P2 | VERIFIED | API/BFF ops | correlation + structured logs | request/error tracing smoke |
| AUD-OBS-002 | P1 | BLOCKED WITH ASR | Speech ops | queue metrics/alerts after queue fix | worker reliability/metrics |
| AUD-OBS-003 | P2 | VERIFIED | Auth observability | failed-auth telemetry | burst detection test |

---

## 8. قرارات لا يجب كسرها أثناء A10

- لا تجعل rate limit يمنع الطالب من إعادة المحاولة الطبيعية بسبب خطأ إدخال عابر.
- لا تسجل رمز دخول الطالب أو password أو JWT أو presigned URL في logs.
- لا تجعل session revocation يمس التاريخ الأكاديمي أو AudioSubmission history.
- لا تجعل media cache عامة لأي profile/report/private JSON.
- لا تستبدل brand colors عالميًا؛ عالج semantic text/action roles فقط.
- لا تفعّل Production ASR لمجرد إضافة metrics؛ provider/calibration approval ما زال مستقلًا.
- لا تحذف `/recordings` قبل dependency proof، رغم وجود vulnerability؛ الإصلاح قد يكون bounded policy أولًا ثم retirement إذا ثبت legacy.

---

## 9. إغلاق A07

A07 مغلق كـ **static/source audit**.

أهم blockers قبل Production من هذه الجولة:

- auth brute-force protection.
- credential/session revocation.
- production Secure-cookie readiness contract.
- unbounded presigned recording upload.
- BFF media caching regression.
- reduced-motion + contrast blockers.
- speech/operational observability قبل أي Production ASR.

**لا Production code عُدل، ولا PenTest/Lighthouse/axe run ادُّعي، ولا Merge/Deploy تم.**

**نقطة الاستكمال التالية: A08 — Full Journey / Integration / E2E / release-gate evidence.**
