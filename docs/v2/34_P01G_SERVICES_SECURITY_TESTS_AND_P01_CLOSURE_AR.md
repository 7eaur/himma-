# هِمّة V2 — فحص P01-G للخدمات والأمن والاختبارات وإغلاق P01

**التاريخ:** 2026-10-19

**الحالة:** `ready_for_review_source_only` — أُنجز فحص المصدر والتخطيط؛ لا تشغيل شامل ولا تعديل Runtime/DB/نشر

**فرع العمل:** `v2/01-learning-foundation-20261007`

**HEAD المفحوص قبل التوثيق:** `414574f13f022413598f7f69d31556194de83dc4`

**مرجع V1 الحي من GitHub:** `stage/02-content` عند `4ecb27590f7c19cbe7823804b9919d91000415ef`

## 1. الخلاصة التنفيذية

تملك V1 أساسًا تقنيًا يستحق المحافظة: FastAPI واحدة، PostgreSQL/Alembic، Redis لمحدد الدخول، تخزين S3 خاص للتسجيلات، JWT داخل Cookie، إبطال جلسات دائم، idempotency لكتابات الطالب، قيود تنافسية، محتوى canonical fail-closed، `/health` و`/ready` منفصلان، request correlation، سجل Audit، وطابور تحليل كلام دائم تكون فيه المراجعة البشرية هي السلطة الأكاديمية. لا يوجد مبرر لبناء Backend موازٍ أو حذف هذه القدرات.

لكن هذا الأساس ما يزال مربوطًا بعقد V1 ذي **125 عنصرًا و10 أنشطة لكل مستوى**، ولا يملك نموذج Lesson/Release/Review V2. والأهم أن فرع `v2/*` غير مشمول في تشغيل CI التلقائي: لا توجد GitHub Actions مرتبطة بالـHEAD المفحوص، والـstatus الوحيد الظاهر هو Vercel ناجح، وهذا لا يثبت Backend أو Security أو Integration أو E2E. لذلك لا يجوز نقل نتائج CI التاريخية لـV1 إلى V2.

أبرز النتائج الجذرية:

1. يوجد مالكان فعليان لـ`POST /assessment/start` ومالكان لـ`POST /assessment/session/{session_id}/finish`؛ السلوك يعتمد على ترتيب `include_router`، بينما تعليق التركيب يدّعي أن لكل URL مالكًا واحدًا. OpenAPI يخفي الازدواج بدل إثبات غيابه.
2. قاعدة البيانات والمحتوى والجاهزية لا تربط جلسة الطالب بإصدار محتوى immutable؛ `/ready` يثبت إصدار V1 الحالي عالميًا فقط، ولا يضمن أن جلسة قديمة تكمل على الإصدار الذي بدأت به.
3. الـBFF العام يحمّل الطلب والرد كاملين في الذاكرة بلا حد حجم أو مهلة أو معالجة صريحة لانقطاع upstream؛ والـAPI ينفذ تقارير PDF/XLSX واستعلامات وتجهيز S3 متزامنة داخل request workers.
4. التسجيل له مساران: رفع عبر FastAPI مع idempotency، ومسار presigned قديم لا ينشئ سجلًا أكاديميًا عند `/complete`. لا توجد سياسة موحدة للأيتام/الحذف/الاحتفاظ، والتحقق من النوع يعتمد metadata لا فحص الحاوية الثنائية.
5. Cookie قوية نسبيًا (`HttpOnly`, `Secure` في trial/production, `SameSite=Lax`) لكن لا توجد حماية CSRF صريحة بـOrigin/Token للطلبات المعدّلة للحالة، ولا تحقق production fail-closed من CORS origins المهيأة.
6. متطلبات Python ذات lower bounds واسعة ومن دون lock/hash، بينما Frontend يملك `package-lock.json`. بناء backend غير reproducible وقد يتغير دون تغيير Git.
7. يوجد 77 ملف اختبار Backend و305 دوال اختبار، و32 ملف Unit/Spec في Frontend منها 22 E2E و83 حالة تقريبًا، ولا توجد skips ظاهرة؛ لكن العدد لا يساوي نجاحًا، ولم تُشغّل suite لهذه الجولة.

قرار P01: **نحدّث نفس المنصة** عبر وحدات V2 داخل FastAPI/Next الحالية، مع إزالة ازدواج الملكية وتثبيت release/session contracts وإبقاء الوظائف الأمنية والتشغيلية النافعة. لا `RETIRE_APPROVED` لأي وظيفة V1 في هذا التقرير.

## 2. ما فُحص وحد الإثبات

### 2.1 نطاق المصدر

- تركيب FastAPI وجميع routers ومسارات Auth/Student/Supervisor/Media/Recording/Review/Reports/Speech.
- نماذج SQLAlchemy و15 migration في سلسلة Alembic واحدة من `0001_initial` إلى `0014_reward_attempt_history`، مرورًا بالمراجعة `3b33d494c447`.
- إعداد DB، المعاملات والقيود والفهارس، Redis rate limit، S3/MinIO، readiness، runtime flags، worker وتحليل الكلام.
- BFF في `apps/web/src/app/api/[...path]/route.ts`، Proxy حماية الصفحات، Cookies وCSP/security headers.
- `ci.yml`, `m04-responsive.yml`, `m09-release-readiness.yml`، manifests والاختبارات ومحددات التشغيل.
- `deploy/railway-*.Dockerfile`, `deploy/railway-predeploy.sh`, `docker-compose.yml` كمصدر إعداد؛ لم تُستخدم لإثبات نشر حي.

### 2.2 الحالة الفعلية للـHEAD

| البند | النتيجة المثبتة |
|---|---|
| HEAD قبل التقرير | `414574f13f022413598f7f69d31556194de83dc4` |
| مرجع V1 | `4ecb27590f7c19cbe7823804b9919d91000415ef` |
| GitHub Actions على HEAD | لا runs مرتبطة بالـSHA |
| Combined status | `Vercel = success` فقط؛ ليس دليل API/DB/Security/E2E |
| Trigger `ci.yml` | لا يشمل `v2/*`; PR يعمل فقط عند الاستهداف إلى `main` |
| Trigger M04/M09 | لا يشمل `v2/*` تلقائيًا |
| تشغيل محلي في الجولة | لم تُشغّل suites أو خدمات أو Browser؛ فحص ساكن فقط |

وثائق `docs/ops` التي تسجل نجاحات V1 في سبتمبر/أكتوبر أدلة تاريخية لذلك الـSHA فقط. وبما أن V1 لم تعد منشورة حسب قرار المالك، لا يُعاد وصفها كنشر حالي ولا يُطلب تشغيلها.

## 3. خط الأساس الذي نحافظ عليه

| ID | قدرة V1 المثبتة | قرار V2 |
|---|---|---|
| SG-K01 | FastAPI واحدة وNext واحدة وحدود BFF مع Cookie forwarding | `KEEP/CONSOLIDATE`؛ لا Backend موازٍ |
| SG-K02 | JWT HS256 بحد أدنى 32 byte وclaims مطلوبة ودور/حساب نشط | `KEEP/HARDEN` |
| SG-K03 | `AuthSessionState` يبطل الجلسات السابقة بعد تغيير الكلمة/الكود/التفعيل | `KEEP` |
| SG-K04 | Redis atomic rate limiting حسب IP ومعرّف مهشّم وfail-closed في trial/production | `KEEP` |
| SG-K05 | Cookies `HttpOnly`, `SameSite=Lax`, و`Secure` في البيئات المحمية | `KEEP` مع CSRF/host validation |
| SG-K06 | request correlation و`x-request-id` من BFF إلى FastAPI | `KEEP/EXTEND TO AUDIT` |
| SG-K07 | `/health` liveness منفصل عن `/ready` dependency/content/security gate | `KEEP/GENERALIZE FOR V2` |
| SG-K08 | Alembic upgrade/downgrade/model-drift gate وسلسلة migration واحدة | `KEEP` على قاعدة V2 النظيفة |
| SG-K09 | قيود DB للجلسة النشطة، محاولة/خطوة وحيدة، retake pending، وidempotency | `KEEP/EVOLVE` إلى lesson/support/review |
| SG-K10 | نشر canonical ذري وdigest/readiness fail-closed | `KEEP PRINCIPLE`؛ compiler V2 لبنك 300 |
| SG-K11 | S3 خاص، حد 10MB، مفاتيح ضمن الطالب، streaming range وno-store | `KEEP/HARDEN` |
| SG-K12 | التسجيلات/reviews append-only وأحدث تسجيل هو الحي | `KEEP` |
| SG-K13 | العامل الصوتي durable lease و`SKIP LOCKED`، وقرار الآلة advisory | `KEEP AS OPTIONAL CAPABILITY`؛ الإنسان سلطة |
| SG-K14 | CI يجمع dependency/secret/placeholder/skip guards وBackend/Frontend/Integration | `KEEP/ENABLE FOR V2` |
| SG-K15 | M09 يشمل migrations/seed/MinIO/Redis/E2E/backup-restore | `KEEP/PORT TO V2 CONTRACT` |
| SG-K16 | Security headers: CSP/frame/nosniff/referrer/permissions | `KEEP/HARDEN WITHOUT BREAKING NEXT` |
| SG-K17 | سجل Audit للأفعال الحساسة والتصدير | `KEEP/MAKE COMPLETE` |
| SG-K18 | لا توجد اختبارات disabled/skipped ظاهرة في المسارات المفحوصة | `KEEP AS GATE` |

## 4. سجل الفجوات والأسباب الجذرية

| ID/أولوية | المكان ووظيفة V1 | القصور والسبب الجذري | هدف V2 وما يُحفظ | اختبار الإغلاق |
|---|---|---|---|---|
| SG01 `P0 Quality` | `.github/workflows/ci.yml`, `m04-responsive.yml`, `m09-release-readiness.yml` | `v2/*` خارج push triggers؛ لا Quality Gate على HEAD | أضف `v2/**` أو عقد PR إلزامي، واحفظ كل jobs الحالية | push/PR تجريبي يثبت Security+Backend+Frontend+Integration+M04/M09 حسب النطاق |
| SG02 `P0 Evidence` | GitHub status للـHEAD | Vercel نجاح وحيد؛ لا workflow runs؛ النجاحات التاريخية ليست transitive | سجل Evidence مرتبط بالـSHA والبيئة والأثر | required checks تمنع الدمج وملف evidence يطابق commit |
| SG03 `P0 Route correctness` | `main.py`, `assessment.py`, `assessment_retake.py`, `assessment_completion.py` | ازدواج `POST /assessment/start` و`.../finish`؛ أول route يفوز runtime وOpenAPI يطوي اللاحق | مالك Router واحد؛ الخدمات المشتركة بلا decorators؛ حافظ على retake/completion | route ownership AST/OpenAPI + طلب runtime يثبت handler واحد ولا يعتمد الترتيب |
| SG04 `P0 V2 model` | `AssessmentSession`, `Attempt`, readiness والثوابت | الجلسة لا تحمل `content_release_id`، والنموذج `pretest/posttest/core` لا Lesson stages؛ الجاهزية تقفل 125 عنصرًا عالميًا | Release immutable مربوط بكل assessment/lesson/support session | جلسة تبدأ على N ثم تفعيل N+1؛ الاستئناف يبقى N والتقرير يصرح الإصدار |
| SG05 `P0 Content/runtime` | `_EXPECTED_TOTAL_ITEMS=125`, أنواع 30/30/30/35 | `/ready` وseed/compiler مصممة لإصدار V1؛ لا 300 سؤال/19 درسًا/89 asset roles | حارس V2 مشتق من compiled manifest لا أرقام متناثرة | tamper/missing/extra/duplicate/role leak وfixture-vs-approved gates |
| SG06 `P0 Security` | كل endpoints تعتمد `researcher` العام | حدود الخدمة لا تطبق capability/cohort scope؛ فجوة AF01 تمتد لكل API/recording/report | Dependency authorization مركزي default-deny مع actor scope | matrix 401/403/cross-cohort/forged URL لكل command/read/export |
| SG07 `P1 CSRF` | Cookie auth + BFF mutating routes | `SameSite=Lax` تخفيف وليس عقد CSRF كاملًا؛ لا Origin/Referer allowlist أو token | تحقق same-origin على BFF/API وCSRF token إن لزم، دون كسر رفع الصوت | POST/PATCH من origin مسموح/مرفوض، missing/null origin policy، login/logout |
| SG08 `P1 CORS/config` | `main.py` يقبل `CORS_ORIGINS` ويستخدم `allow_methods/headers=["*"]` | لا validation fail-closed للقيم في production؛ خطأ env قد يوسع السطح أو يعطل credentials | Config object typed، origins HTTPS صريحة، منع wildcard/فارغ غير المقصود | startup config matrix trial/production + preflight tests |
| SG09 `P1 BFF resilience` | `api/[...path]/route.ts` | `req.blob()` و`upstream.arrayBuffer()` بلا حد/streaming/timeout؛ exception غير محولة إلى عقد 503 | حد body، timeout/abort، streaming للملفات والصوت، error envelope وrequest id | oversized/slow/disconnect/large export/range، وعدم تضاعف الذاكرة |
| SG10 `P1 Upload integrity` | `storage.py`, `recordings.py` | الثقة في `Content-Type/Length` وmetadata؛ لا magic/container inspection أو malware policy | تحقق WebM/audio فعلي، مدة وحدود، quarantine عند الحاجة | ملف متنكر، truncated/corrupt/polyglot، الحجم/المدة، unavailable storage |
| SG11 `P1 Storage lifecycle` | رفع FastAPI + presigned compatibility | مساران متوازيان؛ `/complete` لا ينشئ Evidence DB، وفشل DB بعد put يترك object يتيمًا؛ لا retention/delete reconciliation | Recording service واحد: reserve→upload→verify→attach، job تنظيف وretention مدقق | orphan cleanup، retry/idempotency، DB failure، rerecord history، delete authorization |
| SG12 `P1 Recording auth` | `/recordings/play-by-key`, `/stream-by-key` | يقبل أي key يبدأ `audio/` للمشرف العام دون إثبات ارتباطه بسجل/طالب/scope | resolve عبر Recording row + capability/scope؛ لا raw arbitrary key | key لطالب خارج النطاق/يتيم/path tricks/non-audio يرفض |
| SG13 `P1 DB operations` | `create_engine(DATABASE_URL)` | لا `pool_pre_ping` أو pool/connect/statement timeouts أو application name؛ لا عقد استرداد اتصال ميت | إعداد typed حسب البيئة ومقاييس pool/slow query | killed connection، saturation، statement timeout، readiness recovery |
| SG14 `P1 Transactions` | commits موزعة داخل handlers/services | بعض domain flows تملك commits متعددة/side effects خارج DB؛ لا Unit of Work موحد أو outbox للإشعارات | transaction boundary لكل command، after-commit events/outbox، idempotency | failure injection بكل خطوة، no partial academic state/duplicate event |
| SG15 `P1 API errors` | FastAPI defaults وصفحات React | 422 array وHTTP errors ونقاط 500 لا envelope موحد؛ BFF لا يصون `Retry-After` وبعض headers | `code/message/field_errors/request_id/retry_after` موحد، عربي مناسب | 400/401/403/404/409/413/422/429/503 وUI بلا crash |
| SG16 `P1 Performance` | `review.py`, `reports.py`, `skill_reports.py`, student projections | N+1 و`.all()` بلا pagination؛ exports synchronous؛ queue يقرأ كل uploaded ثم يستعلم لكل صف | batched read models، pagination، limits، export job/stream مع authorization | query budgets وcohort كبير وطابور كبير وtimeout/cancel |
| SG17 `P1 Async capacity` | sync FastAPI handlers + boto3/PDF/XLSX | S3/توليد الملفات/استعلامات طويلة تحجز workers؛ لا load/SLO evidence | افصل الأعمال الثقيلة أو thread/job آمن، ضع timeouts/backpressure | concurrent uploads/reports/login، latency/error/memory budgets |
| SG18 `P1 Dependencies` | `services/api/requirements.txt` | 17/18 تقريبًا lower-bound غير مقفلة ولا hashes؛ بناء اليوم قد يختلف غدًا | lock reproducible وفحص تحديثات منضبط وSBOM عند الإصدار | clean build مرتين، hash verification، audit لنفس lock |
| SG19 `P1 Deployment parity` | API Python 3.13؛ CI Python 3.12؛ local docs متباينة | اختلاف runtime قد يخفي أخطاء؛ لا matrix أو policy نسخة واحدة | وحّد النسخة أو اختبر 3.12/3.13 حسب production الفعلي | image build + smoke + migration على نفس runtime |
| SG20 `P1 Worker operations` | `speech_worker.py` موجود بلا خدمة worker في ملفات النشر المفحوصة | queue/retry/lease source جيد لكن لا lifecycle/health/deployment مثبت؛ لا يجوز ادعاء ASR تشغيلية | إما feature-off واضح أو worker مستقل monitored بعد اعتماد المزود | crash/reclaim/dead-letter/health/scaling/provider-off؛ الإنسان يبقى authority |
| SG21 `P1 Readiness cost` | `/ready` يقرأ 125 item وخطوات/أصول ويحسب digest ويفحص 108 ملفًا كل نداء | فحص قوي لكنه مكلف وقد يضغط DB/filesystem عند probe متكرر | cache bounded/invalidation أو startup attestation + cheap live readiness | probe frequency/load، stale invalidation، tamper closes readiness |
| SG22 `P1 Schema invariants` | ContentRelease/ContentStep/Option/AssetLink | بعض الحقائق في التطبيق لا DB: إصدار نشط واحد، ترتيب step/option فريد، asset مرتبط item XOR step، status/kind values | constraints/indexes وpublisher transaction بلا فقد المرونة | concurrent publish، duplicate order، both/neither owner، invalid enum/status |
| SG23 `P1 Audit/privacy` | `AuditLog.details` نص حر وactor IDs بلا FK، logs متنوعة | لا schema/redaction/retention أو correlation شامل؛ خطر كتابة secrets/PII ونقص المصالحة | structured minimal event، request ID، actor/scope، redaction/retention | access code/password/audio URL لا تظهر في logs؛ كل command حدث واحد |
| SG24 `P1 Backup/restore` | M09 يختبر DB/object backup تاريخيًا | لا run حديث لـV2 ولا عقد restore release/session/review الجديد؛ لا دليل RPO/RTO | backup/restore gate بعد schema V2 وencrypted retention | restore منعزل ومصالحة DB↔objects↔release/digests |
| SG25 `P1 Test gaps` | اختبارات كثيرة لكن V1-oriented | لا contracts لبنك 300 وLesson stages/write_text/video/RBAC/release pin ولا exact-head run | Port القديم + اختبارات V2 الجديدة، لا حذف suites النافعة | مصفوفة القسم 6 وكل C/D/E/F tests مرتبطة بالـSHA |
| SG26 `P2 Maintainability` | ملفات خدمات وصفحات كبيرة وlegacy compatibility | ownership موزع وimports خدمية من router modules؛ يزيد التداخل والازدواج | domain services صغيرة وواضحة داخل نفس التطبيق، وcomposition root واحد | dependency boundary/static ownership، لا cyclic imports أو duplicated renderer/service |

## 5. مراجعة CI والاختبارات الفعلية

### 5.1 ما هو موجود في المصدر

| المجموعة | ما تفعله | الحكم الحالي |
|---|---|---|
| Security | `pip-audit`, production `npm audit`, gitleaks pinned checksum، guards للـTODO/mock/delay/skips | تصميم جيد، **غير منفذ على HEAD V2** |
| Backend | PostgreSQL، canonical validation، Alembic up/down/up + check، seed idempotency، pytest كامل | جيد لـV1، يحتاج عقد V2 وtrigger |
| Frontend | npm ci، TypeScript، ESLint، Jest، build | جيد، غير منفذ على HEAD |
| Integration | PG/Redis/MinIO/API/Web و13 ملفات Playwright مختارة | مفيد، لكن ليس كل 22 E2E ولا V2 stages |
| M04 | responsive smoke وscreenshots | لا يبدأ API في workflow نفسه ويشغّل test مخصصًا؛ لا يُعامل كرحلة full-stack |
| M09 | release readiness وE2E وbackup/restore | قوي تاريخيًا؛ trigger لا يشمل V2 ولا run حالي |

### 5.2 جرد ساكن لا نتيجة نجاح

- Backend: **77** ملف `test_*.py`، وفيها نحو **305** دوال `test_*`.
- Frontend: **32** ملف test/spec، منها **22** E2E، ونحو **83** حالة `test/it` بالعد الساكن.
- لم يظهر `pytest.mark.skip/skipif/xfail` أو `test.skip/describe.skip/.only` في البحث الحالي.
- لا توجد أي suite منفذة في P01-G؛ كل الاختبارات التالية `NOT_RUN` حتى تظهر نتيجة مرتبطة بالـSHA.

## 6. بوابة الاختبارات المطلوبة بعد اعتماد P01

| ID | السيناريو | المرحلة الأدنى |
|---|---|---|
| SG-T01 | كل workflow المطلوب يعمل على `v2/*` ويظهر required check على SHA | P02 |
| SG-T02 | route ownership يثبت handler واحد لكل method/path وOpenAPI بلا تضارب | P02 |
| SG-T03 | Alembic V2 على DB نظيفة: upgrade/downgrade/upgrade/check وseed idempotent | P02 |
| SG-T04 | release N/N+1، pin للجلسة، resume/report reproducibility | P02–P03 |
| SG-T05 | Student projection لا يسرّب answer/rubric/reference/origin الداخلي | P02 |
| SG-T06 | 300 بند/19 درس/13 مهارة/12 دعم وmedia manifest كاملة | P02 |
| SG-T07 | RBAC/scope matrix لكل Student/Review/Report/Export/Recording API | P02–P08 |
| SG-T08 | CSRF/Origin/CORS/cookie/session revoke/rate-limit fail-closed | P02 |
| SG-T09 | oversized/slow/disconnected BFF/API مع timeout و413/503 وrequest ID | P02–P03 |
| SG-T10 | رفع صوت صالح/متنكر/تالف/مكرر وانقطاع S3/DB وتنظيف orphan | P04/P08 |
| SG-T11 | التسجيل لا يُقرأ بمفتاح خام خارج scope ويعمل Range seek | P08 |
| SG-T12 | failure injection لكل command يمنع partial state/duplicate reward/notification | P02–P08 |
| SG-T13 | DB pool saturation/dead connection/statement timeout/recovery | P02/P09 |
| SG-T14 | query-count وlatency/memory مع cohort/queue/export كبير | P07/P09 |
| SG-T15 | worker lease/reclaim/retry/dead-letter/provider disabled/human authority | P08 |
| SG-T16 | readiness رخيصة نسبيًا، وتغلق عند dependency/content/media/security drift | P02/P09 |
| SG-T17 | dependency lock يبني image مطابقة على runtime المعتمد ويمر audit | P02 |
| SG-T18 | backup/restore لقاعدة V2 وobjects مع reconciliation وRPO/RTO | P09 |
| SG-T19 | إعادة كل B/C/D/E/F tests و`RG01–RG25` على الهاتف/التابلت/الديسكتوب | P03–P09 |
| SG-T20 | لا نشر Production مع fixture/missing media أو suite/status غير مرتبطين بالـSHA | P09/P10 |

## 7. مصالحة تقارير P01-A إلى P01-F

| الجزء | نتيجة المصدر المعتمدة | ما يؤكده P01-G | ما بقي غير منفذ |
|---|---|---|---|
| P01-A | الهوية والأصول محفوظة؛ CSS debt | readiness الحالية تفحص حزمة صوت V1 فقط؛ بوابة V2 تحتاج manifest وقياس تحميل | Visual/audio/performance QA |
| P01-B | Auth جيد جزئيًا مع فجوات redirect/error/logout | Redis rate-limit وepoch حقيقيان؛ تُضاف CSRF/CORS/BFF resilience | Security/runtime/browser tests |
| P01-C | رحلة V1 durable لكنها 10 أنشطة/مستوى | DB والجلسات والجاهزية تؤكد التثبيت على V1 وعدم release pin | CurrentAction/LessonSession/resume tests |
| P01-D | لا stages/video/write_text وبنك 300 غير موصول | لا schema/runtime/readiness لهذه العقود، وBFF/upload يحتاجان hardening | Compiler/DTO/player/interactions |
| P01-E | تكيف/دعم V1 لا يطابق policy V2 | المعاملات والطابور قابلان للحفظ، لكن لا evidence/support/review model موحد | Policy calibration/concurrency/review |
| P01-F | لوحة كاملة يجب حفظها مع RBAC/report fixes | القيود الأمنية والأداء/التصدير تؤكد AF01/03/04/18/21 | Admin runtime/E2E/exports |

لم يظهر تناقض يبرر إلغاء قرار سابق. التصحيح الجديد الوحيد واسع الأثر هو أن عبارة `main.py` عن مالك واحد للمسارات ليست صحيحة لمساري البدء والإنهاء، لذلك أضيف SG03 ولا نعد اختبار Activity ownership دليلًا على Assessment ownership.

## 8. قرار معمارية الإغلاق

1. **نفس المستودع ونفس التطبيقين:** Next + FastAPI؛ لا منصة موازية.
2. **قاعدة V2 نظيفة مسموحة** لعدم الحاجة لترحيل الطلاب، لكن الوظائف والهوية والإصلاحات تنتقل كلها.
3. **نستبقي الجداول/المبادئ النافعة** أو نعيد هيكلتها بمهاجرات، ولا نربط V2 بأرقام V1 أو seed تاريخي.
4. **مصدر محتوى خاص immutable** لبنك 300، وكل جلسة تحمل release pin؛ DTO الطالب allowlist فقط.
5. **Router واحد لكل contract** وطبقة خدمات بلا decorators؛ لا ترتيب تركيب يقرر المنطق.
6. **Command transactions + idempotency + outbox/domain events** للأفعال المركبة، وRead Models للطالب والمشرف والتقارير.
7. **Recording/Review service موحد** للصوت والكتابة وحالات pending، والآلة لا تستبدل قرار المشرف دون اعتماد لاحق.
8. **CI exact-SHA شرط بدء التنفيذ:** أول عمل P02 تفعيل البوابات وتصحيحها دون تخفيف guards.

## 9. حكم إغلاق P01

`P01-A` إلى `P01-F` معتمدة من المالك **كتدقيق مصدر**، و`P01-G` الآن `ready_for_review_source_only`. وبذلك اكتمل نطاق الفحص المخطط لـP01، لكن **P01 الكلية لا تصبح approved ولا تبدأ P02 إلا بعد موافقة المالك «تم» على هذا الإغلاق**.

القبول يعني اعتماد خريطة المحافظة والفجوات والعقد المستهدف، وليس أن `SG01–SG26` صُلحت أو أن `SG-T01–SG-T20` نجحت. لم يتغير الكود أو DB أو النشر، ولم تُحذف ميزة أو أصل أو بيانات.

## 10. نقطة البدء الوحيدة بعد الموافقة

إذا اعتمد المالك P01 كاملة، يبدأ **P02 فقط** بالترتيب:

1. تفعيل CI على فرع V2 وإنتاج evidence للـSHA دون تعطيل Security.
2. توحيد route ownership/config/dependency lock كأساس قابل للاختبار.
3. عقود content release/student projection/media manifest الآمنة.
4. schema V2 النظيفة والمهاجرات والـrelease pin/idempotency.
5. ثم التوقف لاعتماد P02؛ لا يبدأ بناء واجهات P03 تلقائيًا.
