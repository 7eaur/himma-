> **تنبيه تسليم حديث 2026-10-26:** هذه الوثيقة لقطة P08 تاريخية، وليست نقطة الاستئناف الأخيرة. بعد موافقة المالك أُنجز P08 واعتمدت سياسة الصوت الأخير، ثم P09.0، وبدأ P09.1-A/B/C. **مرجع المتابعة الجديد الملزم:** [63_LIVE_P09_HANDOFF_FIRST_STUDENT_ASSESSMENT_BLOCKER_AR.md](63_LIVE_P09_HANDOFF_FIRST_STUDENT_ASSESSMENT_BLOCKER_AR.md)، وخاصة عطل أول دخول «تعذر فتح الاختبار» وفشل E2E الحالي. لا تعتمد عبارة `P09=not_started` أدناه كواقع حاضر.

# هِمّة V2 — التسليم التنفيذي الشامل إلى محادثة جديدة (استكمال P08)

> **تاريخ التحقق من GitHub وRailway:** 2026-10-25، المنطقة الزمنية اليمن (+03:00).
> **الغرض:** استلام واستكمال نفس مشروع هِمّة من آخر حالة فعلية **دون البدء من الصفر**، وبمراجعة المستودع الحي لا الاكتفاء بهذا النص.
> **مراجعة الحقيقة في أول دقيقة:** آخر GitHub HEAD ثم CI/M04/M09 على نفس SHA ثم خدمات Railway؛ إذا تغيّرت الحالة بعد هذا التوثيق، يعمَّم الأحدث وتُحدّث الأرقام.

## 1. التكليف وحدود السلطة

- مالك القرار الوحيد هو المستخدم. في المشروع توجد قاعدة عمل **«لا ننتقل حتى أقول تم»**: تنفيذ ما بقي في المرحلة P08 مسموح الآن، لكن **P08 لم تعتمد بكلمة «تم» ولا يجوز الانتقال إلى P09** دون اعتماد جديد منفصل من المالك بعد عرض نتائج P08.
- المستخدم طلب **حلولًا جذرية لا ترقيعات، وأعمالًا حقيقية في GitHub، وفحصًا صريحًا ثم توثيقًا، وعدم تكرار الأسئلة المعلوم جوابها**. لا تغيّر أسماء الدوال بلا داعٍ ولا تنشئ منصة موازية.
- هِمّة V2 تطوير جذري **لنفس منصة هِمّة V1** بالمستودع نفسه: المحافظة على الشعار/الهوية وتصميمات الصفحات والإصلاحات والوظائف النافعة كافة. ملف تكافؤ V1/V2: `docs/v2/25_V1_TO_V2_FEATURE_PARITY_REGISTER_AR.md`، وصفحات/Regression: `26_V1_IDENTITY_PAGES_AND_FIXED_REGRESSIONS_AUDIT_AR.md`. إلغاء أي ميزة يتطلب `RETIRE_APPROVED` مستقلًا.
- ليس مطلوبًا استيراد **بيانات حسابات الطلاب القديمة** إلى V2، لكن ليس مسموحًا حذف بيانات حقيقة أو تسجيلات أطفال دون موافقة ونسخ احتياطية. استخدام حسابات اختبار اصطناعية فقط للمعاينة.
- لا Docker، ولا ترقية لبيئة الطلاب النهائية أو إطلاق إعلامي. لا أسرار/كلمات مرور/مفاتيح S3 أو صوت أطفال حقيقيين في GitHub أو هذا التقرير.
- يمكن للمحادثة الجديدة **القيام بالتنفيذ بنفسها** باستخدام GitHub/Railway المتصلين؛ ليست ملزمة بالانتظار على جلسة Work أخرى. قد تتحرك الفروع بسبب جلسات أخرى: قبل أي كتابة اقرأ HEAD الحالي واستخدم `expected_sha` ثم تحقق من Push وQA.

## 2. الروابط والمراجع الحاكمة

| الوظيفة | المرجع الحقيقي |
|---|---|
| Repo | `https://github.com/7eaur/himma-` |
| فرع V2 الحاكم | `v2/01-learning-foundation-20261007` |
| V1 للمقارنة فقط | `stage/02-content` |
| **HEAD لحظة التسليم** | `d560940b3bb47558e7d7b1aa0801d2117decc4fc` |
| آخر تنفيذ وظيفي اجتاز البوابات الثلاث | `fc0750f48a4e76f97856b22848b984132933b24f` |
| قرارات المنصة | `docs/v2/DECISIONS_AR.md` |
| الخطة الرسمية المرحلية | `docs/v2/09_IMPLEMENTATION_ROADMAP_AR.md` |
| حالة التنفيذ الزمنية | `docs/v2/21_EXECUTION_PROGRESS_AR.md` |
| مصفوفة قبول النظام | `docs/v2/22_FULL_SYSTEM_COVERAGE_AND_ACCEPTANCE_MATRIX_AR.md` |
| تنفيذ P02–P08 | `docs/v2/35_...` حتى `48_...`؛ انظر القسم 10 أدناه |
| **هذا التسليم الأحدث** | `docs/v2/49_P08_FULL_WORK_CONTINUATION_HANDOFF_AR.md` |

**تفسير التعارض:** الوثائق `40` و`42` و`README` قد تتضمن حكايات تاريخية مثل «P06 ما زالت جارية» أو «لم تُنشر V2»، ولا يجوز اعتمادها كحالة راهنة. الحالة الحية = GitHub/Railway، وهذا التقرير يؤرشف تحقق 2026-10-25؛ تفاصيل قرارات المنتج تظل في `DECISIONS_AR.md`.

## 3. حالة المراحل المعتمدة

- `P00`: معتمدة — بنك المحتوى وخطط العمل.
- `P01`: اعتمد المالك فحص V1 الجذري وأجزاء A–G؛ الاعتماد السابق لفحص المصدر لا يعني أن كل اختبارات V1 قد نُفذت آنذاك.
- `P02`: معتمدة — compiler/release/media/security أساس V2.
- `P03`: معتمدة — مشغل درس/فيديو واختبار الاستئناف مع `TEST_ONLY`.
- `P04`: معتمدة — سبعة أنواع تفاعل وتسجيل/كتابة وفصل التدريب/الاختبار.
- `P05`: معتمدة — التكيف، الأدلة، التقوية، وحماية التقدم.
- `P06`: `approved_by_owner` بتاريخ 2026-10-24 — القبلي/البعدي 30+30 والتسكين اليدوي والمشرف/التقارير.
- `P07`: `approved_by_owner` بتاريخ 2026-10-24 بعد نجاح `CI 40049653887`، `M04 40049653871`، `M09 40049653873` على `15509b6f...`. تجهيز ربط الميديا **ليس** اعتماد ملفات الإنتاج نفسها.
- **`P08=in_progress/acceptance_pending`**: المرحلة الوحيدة المسموح بإكمالها الآن. التنفيذ والاختبارات الآلية متقدمان؛ التجربة على أجهزة حقيقية والخصوصية النهائية غير معتمدتين.
- **`P09=not_started`**، `P10=not_started`؛ لا تنتقل لهما لأن المستخدم قال «اكمل» أو «سلم العمل»؛ يلزم **«تم» مستقلة** للموافقة على كل مرحلة.

## 4. المنصة ومحتواها: مصدر الحقيقة

- تقنية: `FastAPI/Python 3.12` في `services/api`، `Next.js/React/TypeScript` في `apps/web`، `SQLAlchemy/Alembic/PostgreSQL`، `Redis`، تخزين صوت خاص S3-compatible، GitHub Actions (CI/M04/M09)، Railway.
- البنك الحالي: **13 مجموعة مهارات، 19 درسًا** (L1=6, L2=6, L3=7)، **12 دعمًا**، **300 بندًا**: 76 تدريب درس، 75 تحقق درس، 43 تدريب دعم، 46 تحقق دعم، 30 قبلي و30 بعدي. رحلة الدرس: تمهيد ← فيديو ← تدريب موجه بتلميحات ← تحقق مستقل ← دعم/تقدم بحسب الأدلة. لا تجاوز فجوة مهارية بالحدس، ولا ترقية إتقان بسبب التدريب الموجه وحده.
- مصدر الأسئلة التنفيذي **فقط** ملفات JSON الأربعة تحت `docs/v2/content-bank/`: `L1_AUTHORING_BANK_DRAFT.json`, `L2_AUTHORING_BANK_DRAFT.json`, `L3_AUTHORING_BANK_DRAFT.json`, `ASSESSMENT_PRE_POST_DRAFT.json`. نسخ PDF/ملف العميل وتقارير QA ليست مصدر بنك تشغيل.
- **62 سؤال قراءة بشرية** موزعة L1=17 وL2=14 وL3=17 والقبلي/البعدي=14. لا تصحيح صوتي آلي افتراضي أو كشف `private_answer` وrubric للطالب؛ `pending_review` محايدة حتى المشرف.
- الجرد `docs/v2/45_P07_MEDIA_READINESS_AND_BINDING_CONTRACT_AR.md`: **89 media IDs** (19 video،47 audio،23 image)، **73 مستخدمة فعلًا** (19 video،34 audio،20 image)، 16 خاملة. وفق آخر جرد هناك 56 أصول تعليمية مرشحة/مرتبطة بـV1 و33 ناقصة (19 فيديو نهائي و14 صوتًا مطلوبًا). لا تساوِ candidate مع approved؛ بعض الأصوات الواردة تحتاج QA تربويًا. تحقق مجددًا من manifest إذا تغيّر.
- ملفات تسليم الوسائط: `docs/v2/15_ALL_LESSON_VIDEO_BRIEFS_AR.md`، `16_REQUIRED_IMAGES_AR.md`، `17_REQUIRED_LISTENING_AUDIO_AR.md`، `18_STUDENT_READING_AI_REFERENCE_AR.md`، `41_RECEIVED_AUDIO_AND_SHARED_DEMO_VIDEO_AR.md`. الهدف توفير الأصول النهائية في **P10** بعد قبول المنصة وظيفيًا P09.

## 5. ماذا نفذ P08 بالفعل؟ (ليس مجرد خطة)

### القراءة/الكتابة ومراجعة المشرف
- مراجعة إجابات دروس V2 تحت `/v2/review/...`، واختبارات قبلي/بعدي تحت `/v2/assessments/admin/...`، مع قائمة معلقة وأدلة خاصة ومرجع قراءة وحكم بشري مُسبب وسجل تدقيق.
- تحديث `LessonQuestionResponse` و`SkillEvidence` دون جعل `guided_practice` إتقانًا، واستئناف سياسة التكيف عند انتهاء `waiting_review` وبشرط checksum للإصدار الأصلي.
- مسار خصوصي لبث الملفات الصوتية مع Range، وعزل المشرف/الطالب ومنع إرجاع مفاتيح S3 الخاصة ضمن DTO الطالب.
- `v2_lesson_review_actions` append-only لمراجعات الدروس، ومعرفات وملاحظات الحكم الخاصة.

### إعادة التسجيل/الكتابة وقفل التزامن
- `v2_review_retry_tasks`: دورة `requested → submitted → resolved`، والسابق `superseded`؛ حفظ الإجابة/الصوت الأصلي وكل نسخة بديلة دون محوه أو إرجاع درجات آلية، وإرسال `submit_key` يحمي من التكرار ويمنع استخدام نفس المفتاح مع دليل مختلف.
- مسارات `/v2/retries/admin/{kind}/{response_id}/request` (المشرف) و`/v2/retries/student/tasks` / `/recording` / `/submit` (الطالب)، وبالإضافة إليها `/draft` لمسودة كتابة لا تُحتسب.
- `v2_review_claims`: حجز المشرف لمدة **10 دقائق**، يمنع مشرفًا آخر من القرار المتعارض أثناء الحجز، ويسمح بتحريره أو انتهاء مدته؛ لا يخفي تجاوز صلاحيات.
- تاريخ أصل الإجابة والنسخ والملفات الصوتية تحت `/v2/review-history/admin/...` مخصص للمشرف، ويعرض التسجيلات الأصلية والبديلة دون روابط عامة.
- قائمة مهام الطالب تدعم `limit/offset/next_offset` وجلب صفحات متعددة، وتعافي عند `online` و`visibilitychange`، وعدم إظهار بطاقة فارغة في Dashboard العادي. طلبات تدريب `guided_practice` تظهر حتى إذا انتهى الدرس دون إعادة فتحه.

### تعافي الدليل في شبكة ضعيفة
- `staged_audio` metadata خاص بعد رفع S3 وقبل إرسال الإجابة؛ ينجو من Reload/انقطاع استجابة الرفع ويمكن إكمال `submit` دون رفع ثاني. التحقق من الحجم/MIME/المدة والمهمة وملكية الطالب قبل الاعتماد، مع حفظ مرجع التسجيلات السابقة.
- دعم `MediaRecorder` وWebM، ومحاكاة Safari `audio/mp4` في Playwright؛ تحذير حجم 10MiB وإيقاف الميكروفون عند فشل التسجيل أو الملف الفارغ؛ لا تدّعِ أن محاكاة Safari تكافئ iPhone حقيقيًا.
- مسودة `draft_text` على خادم مهمة الإعادة للطالب المالك دون درجة، مع حفظها واستعادتها بعد Reload للدرس والقبلي. إخفاء المسودات والنصوص عن الطلاب الآخرين.
- تم حل regression مرئي: بطاقة مهام الإعادة لا تظهر إن لم توجد مهمات، فلا تطيل لوحة الطالب وتكسر حد Playwright 390px.
- قُلص نسخ سبب المراجعة ونصوص الأطفال في `AuditLog`؛ السجل يشير إلى مرجع الملاحظة الخاصة فقط.

### أهم المسارات في الكود
```
services/api/v2_lesson_review.py
services/api/v2_assessment_runtime.py
services/api/v2_retry_runtime.py
services/api/v2_retry_state.py
services/api/v2_review_claims.py
services/api/v2_review_history.py
services/api/v2_interaction_runtime.py
services/api/v2_adaptation_runtime.py
services/api/storage.py
services/api/db/learning_models.py
services/api/alembic/versions/0021_private_bank_snapshot.py
services/api/alembic/versions/0022_v2_lesson_review.py
services/api/alembic/versions/0023_v2_review_retry.py
services/api/alembic/versions/0024_v2_review_claims.py
apps/web/src/components/learning/StudentRetryTasks.tsx
apps/web/src/components/admin/SupervisorClaimActions.tsx
apps/web/src/app/student/page.tsx
apps/web/src/app/student/learning-v2/[sessionId]/page.tsx
apps/web/src/app/student/assessment-v2/[sessionId]/page.tsx
apps/web/src/app/admin/(dashboard)/v2-lesson-review/page.tsx
apps/web/src/app/admin/(dashboard)/v2-assessments/page.tsx
```

أهم الاختبارات: `services/api/test_v2_lesson_review.py`, `test_v2_retry_runtime.py`, `test_v2_review_claims.py`, `test_v2_review_history.py`, `test_v2_reading_review_coverage.py`، و`apps/web/tests/e2e/v2-rewrite-draft.spec.ts` وسائر E2E الخاصة بـP08. لا يُستبدل التحقق بكود جديد دون regression.

## 6. GitHub QA — الأدلة الدقيقة عند التسليم

- **آخر Commit وظيفي:** `fc0750f48a4e76f97856b22848b984132933b24f` (اختبار الرفع الخاص بنمط Safari MP4). فحوص **نفس SHA** مكتملة SUCCESS:
  - CI Quality Gate **40141820366**: Backend + Frontend + Security + PostgreSQL/MinIO + Browser Integration.
  - M04 Responsive Visual Gate **40141820358**.
  - M09 Release Readiness Gate **40141820354**.
- **HEAD الأخير عند التسليم:** `d560940b3bb47558e7d7b1aa0801d2117decc4fc`، غيّر **وثائق فقط**: `21`,`46`,`47`,`48`، لا تغييرات Runtime. CI **40141971301 SUCCESS** (backend/security/frontend/integration).
- لا توجد M04 أو M09 جديدة مطلوبة من GitHub تلقائيًا على HEAD توثيقي فقط؛ استند بصدق إلى بوابات SHA الوظيفي `fc0750f` وبوابة CI على `d560940`. عند تعديل runtime/واجهة مجددًا، اطلب SUCCESS جديد على **نفس SHA** ولا تكتفِ بإشارات تشغيل سابقة.
- إخفاقات قديمة حُلّت (اختبار تسجيل `audio/1`، بطاقة Dashboard الفارغة، حالات فقد الاستجابة/metadata، عدم ظهور retry عند تعطل current-action، pagination وdraft). **لا تقدم نتائج الإصدارات الفاشلة تاريخيًا كأنها آخر وضع.**

## 7. Railway المتصل — الحي وليس التخمين

- اختر اتصال **«وصل تك كلاود همّه»** (link id: `link_6adbbcda290481919b1a131d34477e25`). لا تستخدم اتصال Railway مختلفًا اسمه Primary.
- مشروع Railway الموجود **`intelligent-courtesy`**: `968ce1df-b94f-4de8-a365-88e5073d3d11`. لا تنشئ مشروعًا ثانيًا.
- البيئة تسمى `production` (ID: `be33aeb5-262e-47bb-b21b-8658522d0e3f`) لكن تشغيل المنصة التجريبية مضبوط `ENV=trial` ومعاينة ميديا موسومة `TEST_ONLY` ومحجوبة عن نشر تعليم فعلي؛ **اسم البيئة لا يعني اعتماد Production**.
- خدمات أربعة موجودة: `himma-web` Web `f1b83b7b-3164-44f1-932a-6a7067f76339`؛ `himma-` API `9f34b0d0-f3c2-4747-8be1-257855b2e326`؛ `Postgres` و`Redis`. هناك bucket صوت خاص متصل بحسب `42` وملفات الإعداد.
- عند تحقق 2026-10-25: **الخدمات الأربع online**، 0 تنبيهات حرجة/تحذيرات، ولا `pendingWork`. آخر Web SUCCESS مرتبط بـ`fc0750f`، وآخر API SUCCESS مرتبط بـ`d6d04525`؛ أحداث نشر `d560940` كانت `SKIPPED` لخدمات Railway لأنها توثيق فقط. افحص actual SHA والوصول الحقيقي دائمًا قبل أي حكم runtime.
- نشر الفرع على Railway يتم تلقائيًا حسب watchPatterns؛ **Push ليس إذن إنتاج تعليمي**. تجنب إنشاء خدمة جديدة أو تغيير ENV أو فتح حسابات أطفال حقيقية أو مشاركة أسرار، وتأكد من حماية معاينة الطلبة وصحة BFF و/health وlog تحذيرات التخزين.
- وسائل فحص أدوات الاتصال: `list_deployments`, `environment_status(includeSuccessful=true)`, `get_logs`, `describe_service`؛ راقب API/Web بشكل منفصل.

## 8. المتبقي الحقيقي — لا يُدفن في عبارة «كل شيء تمام»

1. **اختبارات أجهزة حقيقية غير منفذة:** `docs/v2/48_P08_DEVICE_AUDIO_QA_EXECUTION_PROTOCOL_AR.md` يحتوي **DEV-01–DEV-16** لـiPhone Safari وAndroid Chrome، السماح/الرفض للميكروفون، بدء/إيقاف، خطأ ملف/حد 10MiB، فقد الرفع/الـACK/Reload، replay وre-record، مسودات، عزل حساب، claim متزامن، صوت قديم وجديد وRange، Zoom وRTL. يجب جمع نتائج صريحة `Pass/Fail/Not Run` مع متصفح/OS ولقطات دون بيانات أطفال حقيقيين. Playwright بمحاكاة `audio/mp4` ليس دليل جهاز.
2. **سياسة حفظ/احتفاظ وحذف/تصدير الصوت لم تُعتمد**: لا تحذف ملف طفل أو تخمّن عدد أيام قانونيًا؛ حضّر قرار خصوصية وموافقة المالك والجهة التعليمية/القانونية، واختبر الوصول الخاص والتصدير الآمن والنسخ/الاستعادة قبل اعتماد الإنتاج.
3. **المراجعة التربوية البشرية** لنصوص ومراجع 62 قراءة وبنك 300 سؤال، والتحقق من إعدادات الضجيج واللهجات/التشكيل ووظائف المشرف على حسابات اختبار؛ تبقى غير موقعة. AI/ASR اختياري وخارج Gate التشغيل الإلزامي؛ الافتراضي Human-First ولا يُرسل الصوت لمزود خارجي دون تفويض.
4. **فحص تكامل P08 النهائي يدويًا** على Railway trial + E2E للمسارات التي لا تختبرها بيئة Playwright، خاصة S3 playback/Range على هاتف حقيقي، الأجهزة المختلفة، حالات الشبكة والاحتفاظ والوصول.
5. قبل إعلان `P08=ready_for_owner_review`: تحديث `21` و`46` و`47` و`48` بأدلة QA وآخر SHA، وتجميع النواقص المفتوحة وتحديد ما يمكن قبوله كتأجيل رسمي؛ **لا تعلن P08 approved** دون قول المالك «تم». لا P09 إطلاقًا قبل هذه الموافقة.

## 9. طريقة التنفيذ المقترحة للمحادثة التالية — خطوات عملية

1. ابدأ بفتح هذا الملف، ثم `docs/v2/21_EXECUTION_PROGRESS_AR.md`, `46`,`47`,`48`,`09`,`22`,`25`,`26` و`DECISIONS_AR.md`؛ تحقق من آخر HEAD بدل نسخه من هنا دون فحص.
2. تحقق من QA على آخر SHA وظيفي وHEAD الحالي. إن ظهر إخفاق جديد، اقرأ سجل الـjob وتتبعه للمصدر، وأصلح **السبب الحقيقي** في نفس الفرع (لا رفع عتبة الاختبارات أو skip أو تغيير Assertions لإخفاء regression).
3. افحص 16 حالة DEV مقابل ما يمكن اختبارُه عبر TestClient/Playwright على بيئة sandbox مستقلة؛ أغلق النقص القابل للأتمتة في GitHub مباشرة باختبارات مثبتة، وانشرها من الفرع الحالي بعد تحقق CI/M04/M09. الحالات التي تتطلب **جهازًا حقيقيًا** تُسجل بوضوح Not Run وتُنفذ على الجهاز فعليًا بمساعدة اختبار من المالك/فريقه إن لزم، لا ادعاء.
4. افحص انقطاع الشبكة أثناء upload وعرض الصوت المحمي وRange وعزل المهمة ودورة الحجز على Railway المتصل بحسابات اصطناعية فقط، دون نشر الوسائط التعليمية غير المعتمدة للعامة.
5. جهّز إطار سياسة retention/export/rights مكتوبًا لعرضه على صاحب القرار. لا تعيّن أرقامًا أو تحذف بيانات دون موافقة.
6. اعرض للمالك **ملخص P08 قابل للمراجعة** من ثلاثة أقسام: ما ثبت، ما بقي أو مُنع، القرار الذي يحتاجه. **توقف قبل P09** حتى اعتماد صريح من المالك بعبارة «تم».
7. بعد اعتماد P08 فقط، يبدأ P09 حسب `09` و`22`: E2E لجميع 300 سؤال وكافة وظائف V1/الـFxx/PGxx/RGxx والهاتف والدعم والمشرف والصور، مع `functional_ready_with_test_media`. P10 لاحقة للأصول النهائية والأذونات والاعتماد.

## 10. خريطة الوثائق التي لا يجوز تجاهلها

- `docs/v2/20_VERIFIED_CONTENT_BASELINE_AND_GAPS_AR.md`: حقيقة البنك.
- `docs/v2/21_EXECUTION_PROGRESS_AR.md`: جدول التقدم والاعتمادات.
- `docs/v2/22_FULL_SYSTEM_COVERAGE_AND_ACCEPTANCE_MATRIX_AR.md`: قبول كل وظيفة/صفحة.
- `docs/v2/25_V1_TO_V2_FEATURE_PARITY_REGISTER_AR.md`: وظائف V1.
- `docs/v2/26_V1_IDENTITY_PAGES_AND_FIXED_REGRESSIONS_AUDIT_AR.md`: التصميم/التراجعات.
- `docs/v2/29_WORK_CONTINUITY_AND_P01C_HANDOFF_AR.md`: التسليم التاريخي المؤسس.
- `docs/v2/35_P02_CONTENT_RELEASE_MEDIA_FOUNDATION_DELIVERY_AR.md`.
- `docs/v2/36_P03_LESSON_PLAYER_VIDEO_RESUME_DELIVERY_AR.md`.
- `docs/v2/37_P04_UNIFIED_INTERACTION_RUNTIME_DELIVERY_AR.md`.
- `docs/v2/38_P05_ADAPTATION_SUPPORT_MASTERY_DELIVERY_AR.md`.
- `docs/v2/39_P06_ASSESSMENT_PLACEMENT_SUPERVISOR_REPORTING_DELIVERY_AR.md`.
- `docs/v2/42_SUPERVISORY_CONTINUITY_WORK_RAILWAY_FULL_HANDOFF_AR.md`: تاريخ الحسابات/الاستضافة، وليس آخر حالة.
- `docs/v2/44_P06_ROOT_REPAIR_IMPLEMENTATION_AND_VERIFICATION_AR.md`: إصلاحات أصلية P06.
- `docs/v2/45_P07_MEDIA_READINESS_AND_BINDING_CONTRACT_AR.md`: وسائط P07.
- `docs/v2/46_P08_HUMAN_EVIDENCE_REVIEW_DELIVERY_AR.md`: تفاصيل التنفيذ الفعلي P08.
- `docs/v2/47_P08_AUDIO_PRIVACY_ASR_AND_ACCEPTANCE_GATE_AR.md`: خصوصية الصوت/الـASR وحدود القبول.
- `docs/v2/48_P08_DEVICE_AUDIO_QA_EXECUTION_PROTOCOL_AR.md`: بروتوكول 16 حالة أجهزة حقيقية.
- **`docs/v2/49_P08_FULL_WORK_CONTINUATION_HANDOFF_AR.md`**: نقطة تسليم المحادثة الجديدة.

## 11. صيغة قرار الاستلام والإبلاغ

على المنفذ القادم أن يقول الحقيقة دائمًا: هل النجاح من GitHub Actions بالفعل؟ هل التغيير منشور على Railway أم مجرد commit؟ هل اختبار `DEV-xx` عُمل على جهاز حقيقي أم بمضاهاة؟ ما المفقود؟ وأين الدليل؟ **لا ينقل المرحلة أو يدمج إلى الفرع النهائي أو يفعّل نشر تعليم إنتاجي بمجرد عبارة «اكمل».**
