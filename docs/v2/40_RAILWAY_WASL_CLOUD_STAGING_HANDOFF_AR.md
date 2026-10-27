# هِمّة V2 — تسليم إعداد Railway على حساب «وصل تك كلاود همّه»

> **تنبيه توحيد 2026-10-24:** يبدأ هذا المستند بسرد تدقيق ما قبل النشر، وتتضمن أقسامه اللاحقة النشر الناجح. للحصول على الحالة الحية الأخيرة وإصلاح الدخول وإعادة ضبط كلمة مرور المشرف وسجل المخاطر، اقرأ أولًا [`42_SUPERVISORY_CONTINUITY_WORK_RAILWAY_FULL_HANDOFF_AR.md`](42_SUPERVISORY_CONTINUITY_WORK_RAILWAY_FULL_HANDOFF_AR.md). لا تعتبر فقرة «لم تُنشر V2» القديمة وصفًا للحالة الحالية؛ نسخة trial للمراجعة منشورة بالفعل.

**تاريخ التحقق:** 2026-10-23  
**الهدف:** استخدام Railway المتصل لمعاينة تحديث **نفس منصة هِمّة**، والفحص والتطوير المرحلي، وليس إعلان محتوى V2 مرشحًا جاهزًا للأطفال أو نشرًا إنتاجيًا قبل الاعتماد.  
**التنفيذ هنا:** تدقيق قراءة فقط في Railway + هذا الملف؛ **لم تُنشر V2 ولم تُغيّر أي خدمة أو بيانات أو أسرار في Railway**.

## 1. حساب Railway والمشروع الحقيقي الموجود

- اتصال Railway المسمى **«وصل تك كلاود همّه»**، اسم الحساب: «وصل تك كلاود».
- Workspace: `وصل تك كلاود's Projects`، معرف `a8e8d913-7684-4d6c-a0b6-fa957f5a6580`.
- **المشروع الموجود (لا تُنشئ مشروعًا بدلًا منه):** `intelligent-courtesy`، ID `968ce1df-b94f-4de8-a365-88e5073d3d11`.
- **البيئة الوحيدة الحالية:** `production`، ID `be33aeb5-262e-47bb-b21b-8658522d0e3f`.
- **الخدمة الحالية:** `himma-`، ID `9f34b0d0-f3c2-4747-8be1-257855b2e326`.
- **المصدر الحالي لهذه الخدمة:** GitHub `7eaur/himma-`، فرع `stage/02-content` **القديم V1**، وليس `v2/01-learning-foundation-20261007`.
- آخر نشر `8a317ebb-446a-499e-9fbb-b8e67aebb657`: **FAILED** منذ 2026-10-23. عملية Railpack وقفت عند `BUILD_IMAGE` / `Railpack failed to prepare the build`. التشخيص لم يستخرج سببًا أكثر تحديدًا؛ سجلات الـbuild توضح أنها فحصت **جذر monorepo المختلط** دون `rootDirectory` أو `buildCommand` أو `startCommand`.
- لا مجال عام أو مخصص مرتبط بالخدمة حاليًا، ولا متغيرات مشروع مخصصة للخدمة، ولا Postgres/Redis/وسائط S3 Bucket/volumes مدارة ضمن هذا المشروع حسب فحص Railway.
- لا توجد تغييرات Railway staged أو عمليات نشر جارية، حسب وصف البيئة وقت الفحص.

**مهم:** مجرد ربط GitHub إلى Railway لا يعني أن V2 منشورة أو تعمل. فشل الخدمة الحالية يتعلق بمحاولة قديمة لبناء جذر V1 بدون إعداد monorepo، **ولا يثبت فشل كود V2 عند إعداده إعدادًا صحيحًا**.

## 2. حالة V2 قبل اتخاذ أي إجراء في الاستضافة

- فرع العمل الحاكم `v2/01-learning-foundation-20261007`، آخر HEAD تحقق منه وقت هذه الجولة `0265c5810a79ffc71bb261791723b9d4f5d6faa8`.
- P00–P05 معتمدة؛ **P06=ready_for_review** وليس approved؛ P07–P09 لم تبدأ، P10 متوقفة على الوسائط والاعتماد.
- على هذا HEAD: `Himma CI — Quality Gate` = **failure** بسبب Playwright القديم عند وجود زري «ابدأ الاختبار» في لوحة الطالب (وعدم تمييز الاختيار)؛ M04 وM09 = success. **لا تُعطِ تصريح نشر حقيقي بسبب نجاح M09 وحده**، ولا تعطل اختبارات V1 لتحقيق الأخضر.
- بنك V2 مربوط بكود Python Compiler وCandidate Release، 19 درسًا/12 دعمًا/300 بند، ووسائط `TEST_ONLY`، مع 19 فيديو و14 صوتًا جديدًا ناقصة. `candidate_not_approved` ليس محتوى إنتاجيًا.
- كود `runtime_flags.py` يرفض معاينة V2 للطلاب عند `ENV=trial` أو `ENV=production`، ويمنع ملفات الاختبار الوهمية في الإنتاج. **لا تغيّر `ENV` إلى `staging` في خدمة عامة لتجاوز الحظر دون طبقة أمن دخول واضحة وحماية بيانات وحصر حسابات اصطناعية**. الحظر مقصود لحماية الطفل/الإصدار.

## 3. بنية خدمات Railway المستهدفة — ضمن **نفس** مشروع Railway

**لا تنشر جذر المستودع كخدمة واحدة دون إعداد.** مطلوب فصل خدمات التشغيل داخل المشروع:

1. **himma-web**: Next.js من `/apps/web` مع `package.json` و`package-lock.json`. يتم التشغيل `next start` على `0.0.0.0:$PORT`، وربط BFF الداخلي بخادم API عبر DNS الخاص بـRailway. لا expose لمفاتيح قاعدة أو تخزين.
2. **himma-api**: FastAPI من `services/api/main.py`، Python 3.12/requirements pinned، `uvicorn main:app --host 0.0.0.0 --port $PORT` مع build يثبت المتطلبات. **تنبيه حرج:** `services/api/v2_content/compiler.py` يقرأ ملفات `docs/v2/content-bank` من جذر المستودع، لذا **لا تعزل `services/api` كجذر build دون توفير تلك الملفات**؛ يفضّل إبقاء full monorepo context للـAPI مع خطة بناء Python موثقة أو تعديل deterministic packaging بحيث يشمل البنك، دون Docker.
3. **PostgreSQL** (مدار) لحفظ الطلاب الجدد وجلسات V2؛ توصيل `DATABASE_URL` داخليًا، واختبار Alembic `upgrade`, `drift`, readiness. عدم إعادة استخدام بيانات أو DB نسخة V1 بلا قرار مستقل.
4. **Redis** (مدار) إن كانت متطلبات المصادقة/الـrate-limiting/الـreadiness تستلزمه في وضع محمي؛ `REDIS_URL` من مرجع خدمة Railway الداخلي، لا تعطيل متطلبات الأمن.
5. **S3-compatible Bucket** لتسجيلات القراءة الخاصة مع سياسات الوصول والاحتفاظ؛ `storage.py` يحتاج `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET_NAME`. لا استخدام تخزين ملفات الحاوية المؤقت أو متغيرات مفاتيح داخل Git.
6. **متغيرات/أسرار التشغيل:** `API_SECRET_KEY` آمن مولّد خارج Git، `CORS_ORIGINS` مقيّد، `DATABASE_URL`, `REDIS_URL`, `S3_*`، `NEXT_PUBLIC_API_URL` (تستخدمها Next server handlers للـBFF)، `ENV` والكوكيهات/الأصل المصرح به؛ تحقق من كل متغير مطلوب فعليًا في الكود ولا تخمّن قيمًا أو تكشف أسرارًا في توثيق.
7. **الأمن:** واجهة معاينة V2 للأطفال محظورة في بيئة `trial/production` بالمصدر. إذا أُنشئت بيئة `staging` (من خلال واجهة Railway أو أداة تدعم البيئات) يجب تأمينها أولًا ضد الجمهور بحماية دخول مستقلة أو نطاق خاص، واستخدام **حسابات تجريبية اصطناعية فقط**. لا تغيير سلوك `protected_runtime` بقصد إظهار محتوى مرشح للعامة.

## 4. خطة تنفيذ بمراحل آمنة

- **مرحلة A — تصحيح البوابة:** في GitHub، أغلق CI للفرع على آخر HEAD دون تعطيل V1 regression. صحح أيضًا مرجع Implementation SHA غير القابل للاكتشاف في تقرير P06. هذه شروط بداية نشر Candidate قابل للقياس.
- **مرحلة B — إعداد Staging حقيقي:** أنشئ/استخدم بيئة **Staging داخل المشروع الحالي**، منفصلة عن `production`، أو نظام preview معزول ومغلق للمصرح لهم فقط. **لا تغيّر الخدمة الوحيدة الحالية إلى رابط عام لنظام غير جاهز.**
- **مرحلة C — موارد البنية:** أنشئ خدمات API/Web وقاعدة PostgreSQL وRedis والتخزين S3 عند الحاجة المثبتة، داخل المشروع/بيئة المعاينة، مع الأسرار عبر Railway Variables/References وhealth checks؛ افصل web عن api وتعامل مع قيود monorepo.
- **مرحلة D — النشر:** اربط فرع V2 نفسه في خدمات المعاينة؛ حدد Root/Build/Start/Port/Healthcheck، شغّل migrations بأمان، اطلب deploy وانتظر نتيجة `SUCCESS` على الأقل لويب وAPI وDB، مع فحص `/health` و`/ready` المناسبين. حالة `QUEUED` أو `BUILDING` ليست نجاحًا.
- **مرحلة E — المعاينة/المتابعة:** رابط خاص لفريق المشروع، سجلات build/deploy، health وresponse times و5xx، وأدلة Screenshot وPlaywright لـV2 بمعلومات اصطناعية. لا تستخدمها لنشر بيانات طلاب حقيقية.
- **مرحلة F — الإنتاج النهائي (لاحقًا):** بعد P09/P10 ووسائط مصادق عليها وregression parity + موافقة المالك، اعتمد `production` وخدمة/نطاق الطلاب بصورة آمنة. **لا نشر تلقائي من فرع التطوير إلى production**.

## 5. تعليمات Work والفرق بين البيئتين

- الاستضافة الصحيحة المؤكدة: مشروع `intelligent-courtesy` داخل حساب «وصل تك كلاود همّه»، **وليس** حساب Railway الآخر «Primary» وليس مشروعًا جديدًا.
- قبل أي Mutation: أعد قراءة `describe_environment`, `describe_service`, `get_staged_changes` و`list_variables` **بالأسماء فقط**؛ خطط للميزانية وحجم الموارد واحذر تكرار Postgres أو Bucket.
- **لا حذف** الخدمة القديمة أو موارد أخرى؛ لا تبديل الإنتاج ولا نشر للعامة دون جاهزية وإذن. يسمح إعداد Staging المعزول عندما تكون بوابات CI سليمة والحماية قائمة.
- لا تكتب «تم النشر» إلا عند ظهور `SUCCESS` + اختبارات HTTP وتشغيل حقيقي على Commit محدد. وحتى عند ذلك قل **«معاينة تجريبية»** وليس «تم إطلاق هِمّة V2».
- نموذج Work يبقى على قواعد موافقات P00–P10 كما في `docs/v2/21_EXECUTION_PROGRESS_AR.md`؛ تشغيل بيئة معاينة لا يعني اعتماد P06 أو P07.


## 6. التنفيذ الفعلي بعد كتابة الخطة — Railway LIVE Trial بتاريخ 2026-10-23

> هذا القسم **أحدث زمنيًا** من أقسام الحالة السابقة. أصبح Railway يشغّل هِمّة V2 بصفة **trial development** للمراجعة، وليس إطلاق المحتوى المرشح إنتاجيًا. **اسم Environment في Railway هو `production` لأسباب تنظيمية في المشروع الأصلي، لكن متغير API `ENV=trial`**. لذلك تجنب وصف هذا بأنه اعتماد إنتاجي، ولا تغيّر `ENV` إلى `production` قبل P10.

**المشروع نفسه:** `intelligent-courtesy`، المعرف `968ce1df-b94f-4de8-a365-88e5073d3d11`، حساب «وصل تك كلاود همّه». **لا أُنشئت بيئة أخرى**.

**الموارد الفعلية الخمسة فقط** (أربع خدمات وBucket واحدة):

| مورد | المعرف | الحالة المرصودة |
|---|---|---|
| خدمة الخادم API `himma-` | `9f34b0d0-f3c2-4747-8be1-257855b2e326` | `SUCCESS` نشر `f35d4fdc-45da-40fa-a902-11febc6b8c24` |
| خدمة الواجهة `himma-web` | `f1b83b7b-3164-44f1-932a-6a7067f76339` | `SUCCESS` نشر `4385d9b4-3550-405e-b20a-fb3a32f27700` |
| PostgreSQL `Postgres` | `aec061a2-cfa5-49c7-ac87-8b58bc53b749` | `SUCCESS` ومعها persistent volume |
| Redis `Redis` | `607b2c20-0801-4d4c-86c1-f601be516776` | `SUCCESS` |
| S3 `himma-private-audio` | `36bafa78-4d3b-4c33-93a6-f31a3e8cc5a0` | Bucket منشأة بنفس المشروع، لا خدمة حوسبة إضافية |

**الرابط العام للواجهة:** [https://himma-web-production-eafd.up.railway.app/](https://himma-web-production-eafd.up.railway.app/). Railway يؤكد Domain managed والخدمتان `SUCCESS` و`online`؛ **فحص GET خارجي مستقل لم يثبت نجاحه من بيئة المراجعة**، ولا تدعِ أنه مرئي على كل شبكة قبل Browser QA.

**المصدر وتحديثات المستقبل:** API/Web متصلتان بفرع `v2/01-learning-foundation-20261007` دون pin. يطلق Railway النشر عند Push في الملفات ذات الصلة:
- API: `services/api/**`, `docs/v2/content-bank/**`, `requirements.txt`, `.python-version`, `assets/audio/**`, `packages/content/**`.
- Web: `apps/web/**`.
- الهدف خفض عدد عمليات Build وعدم إعادة نشر المنصة لتغيير وثائق Markdown فقط؛ لا تفسر `push` أو `QUEUED` بأنها نجاح حتى تظهر `SUCCESS`.

**إعدادات التشغيل التي ثُبتت:**
- API: root monorepo `/` للحفاظ على `docs/v2/content-bank`; Python `3.12` عبر `.python-version`, `requirements.txt` مكتمل في الجذر لRailpack؛ build `python -m compileall -q services/api`; start `cd services/api && python -m uvicorn main:app --host 0.0.0.0 --port 8000`; `PORT=8000`, healthcheck `/health`; قبل النشر `cd services/api && alembic upgrade head && python -m db.seed`. سجل أحدث نشر يثبت نجاح migrations وseed وFastAPI.
- Web: root `/apps/web`; build `npm run build`; start `npm run start -- -H 0.0.0.0 -p $PORT`; healthcheck `/`. `NEXT_PUBLIC_API_URL` يشير إلى API DNS الداخلي `http://himma.railway.internal:8000` وليس endpoint API عامًا.
- API: `ENV=trial` و`HIMMA_TRIAL_V2_PREVIEW=true` و`V2_FIXTURE_MEDIA_ENABLED=true`. معاينة V2 مشروطة **بتسجيل دخول صالح** ولا تُفعّل في `ENV=production`، مع استمرار حماية الجلسة/Redis. **حسابات اصطناعية فقط، بلا بيانات أطفال حقيقية.**
- PostgreSQL عبر `DATABASE_URL` مرجع Railway `Postgres`، وRedis عبر `REDIS_URL` مرجع `Redis`، وS3 عبر مراجع `himma-private-audio`. `API_SECRET_KEY` و`ADMIN_PASSWORD` تم توليدهما وإضافتهما في Railway Variables، **ولا تُنسخ قيمهما إلى GitHub**. Username المشرف الابتدائي `admin`. لا تعرض السر في سجلات/Documentation.
- أول فشل نشر API كان بسبب Root Railpack الذي لا ينسخ `services/api/requirements.txt` أثناء مرحلة requirements المبكرة؛ أصلح بإضافة Root requirements **مستقل بذاته**، وبـPython 3.12. فشل healthcheck التالي كان بسبب عدم تثبيت `PORT`؛ حُل بإضافة `PORT=8000`، وشهدنا `SUCCESS` للخادم بعد ذلك. لا حاجة لـDocker.

**مصدر بنك المحتوى ومسار البيانات:**
- **تأليف بنك V2:** ملفات JSON الأربعة تحت `docs/v2/content-bank` في GitHub، يقرؤها `v2_content/compiler.py` ويجمع `candidate_not_approved` ذا checksum وversion. **ليس صحيحًا أن كل البنود التعليمية انتقلت بالفعل إلى PostgreSQL بصورة Release معتمد**.
- **PostgreSQL:** تحفظ حسابات الاختبار الجديدة، الجلسات، التقدم، نتائج الأسئلة، evidence والمراجعات، وإشارات/نسخ `ContentRelease` المرتبطة بالرحلة عند تسجيلها. لا ترحيل لبيانات أطفال V1.
- **الوسائط:** أصول صور وصوت V1 الموجودة ملفات في المستودع، ومعاينة الفيديو/الصوت التجريبية `TEST_ONLY` تستخدم Provider/fixtures. **19 فيديو و14 صوتًا جديدًا حقيقيًا ما تزال ناقصة**. S3 الحاضر يُستخدم للتسجيلات الخاصة؛ يُمكن مستقبلًا استخدامه أيضًا لتخزين ملفات فيديو/صوت إنتاجية بمسارات مفصولة وسياسة وصول آمنة عبر مرحلة P07/P10، دون Bucket ثانية **لكن الربط الإنتاجي غير مطبق بعد**. تخزين Bytes وسائط في PostgreSQL غير مقصود؛ قاعدة البيانات تحمل identifiers/metadata.
- `/ready` القديم يشترط Catalog V1 المعتمد وإكمال الوسائط، لذا يستخدم Healthcheck Railway `/health` للتحقق من تشغيل API في هذه النسخة التجريبية. نجاح `/health` **لا يعني** قبول P06 أو P07–P10 أو سلامة كل الوظائف تربويًا.

**مراجعة الجودة:** عند نشر أول نسخة Trial، كان آخر CI على `be3848582c99b22552b483410ed30129047d8f9e` في GitHub `in_progress`، لا تسجله Passed؛ وP06 لم تحصل على اعتماد المالك النهائي. تم تحديث اختبارات V1 لتمييز `student-primary-action` عن CTA V2 بدل تعطيلها.

**المتابعة:** في كل جلسة Work، افحص Railway `environment_status` و`list_deployments` و`get_logs`، وSHA الفعلي للـWeb/API، وربطهما بأحدث Commit مستهدف. لا تغيّر موارد الاستضافة أو الأسرار أو Public Trial Access دون سبب/اعتماد؛ كل مراحل النشر التالية تلقائية من Push ومراقبة نتائجها ضرورية.
