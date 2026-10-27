# هِمّة V2 — فحص جذور منطق التشغيل وجاهزية النسخة الأولى للعميل

**تاريخ التحقق:** 2026-10-27 (23:00–23:xx بتوقيت اليمن تقريبًا)  
**حالة التقرير:** AUDITED SOURCE / RELEASE BLOCKED / NOT A LIVE UAT CERTIFICATE  
**مرجع الكود الدقيق:** 7eaur/himma- عند ad0243022563ccd09d3518223ce37d75cff996f3  
**الفرعان المتطابقان عند الفحص:** v2/01-learning-foundation-20261007 وv2/work-owner-staging-20261027  
**حفظ التقرير:** cleanup/v2-only-20261027 — فرع مستقل لا يُنشر على Railway. يُرجى نقل القرار/الإصلاح بعناية إلى أحدث HEAD، لا دمج الكود القديم بالجملة.  
**الهدف:** V2 منتج واحد متكامل ومرئي كأنه أول إصدار؛ لا أرشيف ولا شاشات تجريبية ولا تداخل أداء أكاديمي بين V1/V2، ولا حذف بيانات إنتاجية دون إذن لاحق محدد.

## ملخص القرار التنفيذي

الواجهة ومكافآت V2 وتقاريرها تقدمت فعلاً، لكن **لا يصح توقيع تسليم نهائي** الآن. هناك عقبات مانعة على مستوى مصدر المحتوى والأهلية الأكاديمية، وحالة release، وفشل بوابات الاختبار، وتجربة المعاينة المعزولة، إضافة إلى واجهات API تاريخية ما زالت مثبتة. الصفوف التالية **فحص للمصدر المعني فقط** حيث لا يوجد إثبات E2E حي على 23 مسارًا.

### P0-01 — بدء الدرس دون قبلي أو تسكين معتمد: خلل منطق مثبت بالمصدر

- **الدليل:** services/api/v2_lesson_runtime.py؛ POST /v2/lessons/{lesson_id}/start، مسار journey is None يسجل StudentJourney وLessonSession على أساس student.current_level، دون التأكد من وجود قبلي رسمي أو PlacementDecisionV2. GET /v2/lessons/catalog يضع L1-01 current/preview_enabled لحساب بلا Journey. الاختبار services/api/test_v2_lesson_runtime.py::test_start_is_release_pinned_resumable_and_other_lesson_is_blocked يتوقع النجاح بلا قبلي، ما يرسخ السلوك الخاطئ للمنتج النهائي.
- **الأثر:** يستطيع حساب طالب مصادق، في بيئة تسمح بمشغل V2، تجاوز القبلي والتسكين مباشرة بطلب API؛ حتى إن كانت واجهة /student توجهه للقبلي.
- **الإصلاح الجذري:** جعل أهلية بدء lesson شرطًا خادميًا يتطلب pretest V2 رسميًا، placement_state=placed، PlacementDecisionV2 متسقًا مع release pin، وتطابق current_lesson_id؛ لحالات الاستئناف المؤهلة سماح مضبوط لجلسة V2 موجودة فقط. إزالة أي مسار يقوم بإنشاء رحلة درس من Student.current_level بغير قرار رسمي. الكتالوج لا يظهر current قابلًا للبدء قبل التسكين.
- **الاختبار:** طالب جديد GET catalog بلا دروس مفعلة وPOST L1-01 = 409 وبلا StudentJourney/LessonSession؛ ثم قبلي رسمي + قرار التسكين → أول درس فقط 200؛ direct URL وطلب متزامن/متكرر لا يغيران الحقيقة.

### P0-02 — Content release pinning غير مكتمل وقد يغير سؤال/تقوية الطالب بعد ترقية البنك

- **الدليل:** services/api/v2_student_readmodel.py:_release_lessons وservices/api/v2_assessment_runtime.py:_session_release يسترجعان snapshot مثبتًا؛ services/api/v2_adaptation_runtime.py:_complete_lesson أصبح يستخدم PrivateContentBankSnapshot أيضًا (إصلاح MED-05). **لكن** services/api/v2_lesson_runtime.py:_session_payload وlesson_catalog وstart_lesson تستخدم get_lesson/get_release؛ services/api/v2_interaction_runtime.py:_question_ids و_current_question و_resolved_media وreplay تستخدم get_lesson/get_question/get_media؛ services/api/v2_adaptation_runtime.py وv2_adaptation_policy.py تستخدم get_question/get_support_for_lesson من البنك الحالي. خدمات repository.py كلها ترجع compile_release() الأحدث.
- **الأثر:** إذا تغيرت نسخة المصدر المنشورة، قد يتغير مضمون سؤال أو جواب أو دعم أثناء جلسة طالب مثبتة على إصدار أقدم؛ وبما أن start_lesson يستدعي register_candidate_release ثم يرفض اختلاف journey.content_release_id عن الجديد، فإن **استئناف طالب بين درسين من إصدار سابق قد يتوقف ب409** حتى مع snapshot محفوظة. الصيانة المستقبلية للبنك تصبح كاسرة للطلبة الحاليين.
- **الإصلاح الجذري:** إنشاء PinnedReleaseRepository(db, content_release_id) واحد يقرأ snapshot ويثبت checksum/version لكل session، ويمرره إلى question/lesson/support/media/assessment/adaptation/rewards. لا fallback للبنك الجديد. بداية درس تتابع رحلة قديمة على نسختها القديمة ما دامت معتمدة ومتاحة؛ نشر نسخة أحدث يؤثر في الطلاب الجدد فقط. audit لكل mismatch.
- **الاختبار:** طالب A على bank A، إضافة bank B بتغييرات الترتيب/السؤال/الصورة، GET/session/answer/review/support/next lesson تبقى A؛ طالب جديد يبدأ B؛ snapshot مفقود/فاسد → 409 دون تسجيل نتيجة أو مكافأة ولا تغيير المؤشر.

### P0-03 — لم تنفذ آلية نشر إصدار V2 نهائي معتمد

- **الدليل:** v2_content/compiler.py ينتج state=candidate_not_approved وversion يحوي draft؛ v2_content/importer.py:register_candidate_release ينشئ ContentRelease بحالة candidate_not_approved وبلا released_at، ولا يفعله كنشر معتمد. v2_student_readmodel.py يعيد test_only=true؛ v2_lesson_runtime.py:/catalog يعيد mode=candidate_preview وtest_only=true؛ _require_preview_student يرفض مشغل V2 في بيئة ENV=production ويجيزه كاستثناء في trial عند إعداد flag. **لا نفترض قيمة ENV الفعلية في Railway من اسم البيئة**.
- **الأثر:** واجهة V2 ما زالت معماريًا مبنية كنسخة معاينة، وليس إصدار تشغيل رسمي؛ إخفاء TEST ONLY من النص لا يصحح المصدر أو الإتاحة.
- **الإصلاح الجذري:** مرحلة release-candidate → QA pedagogical/media/security → published/activated في DB بحالة وهجرة واضحتين وتوقيع مصدر/checksum، وتغيير حارس Runtime ليقبل الإصدار المنشور في production ويرفض candidate غير معتمد. إعدادات trial/staging منفصلة. لا تغيير لمحتوى الطالب المثبت أثناء التفعيل.
- **الاختبار:** candidate مرفوض في production، published مقبول بعد إتمام QA والوسائط، GET home/catalog لا يحمل مصطلح معاينة، rollback لإصدار منشور دون ضرر لجلسات مثبتة.

### P0-04 — سياسة التسكين التربوي غير مقننة: اعتماد مستوى حر من المشرف

- **الدليل:** v2_assessment_runtime.py::PlacementRequest يقبل أي assigned_level بين 1 و3 وreason بطول صالح؛ place_student بعد اكتمال 30 سؤالًا يتلقى مستوى المشرف، لا توجد معادلة خادمية تربطه بنسبة القبلي. POLICY_VERSION يصرّح manual-placement-1-candidate.
- **أثر محتمل:** خروج طالب 20% بمستوى 3 أو طالب 95% بمستوى 1 ممكن إذا أدخل المشرف ذلك؛ هذا قد يخالف خطة التسكين الأصلية التي تعتمد حدود <50%، 50–<80%، 80–100%. **هذه الحدود تحتاج تثبيتًا تربويًا نهائيًا في قرارات النسخة**؛ لا تُفترض أنها مطبقة في الكود.
- **الحل:** PlacementPolicy V2 تحسب recommended_level من نتيجة pretest الرسمية **بعد مراجعة جميع الأصوات**؛ إظهار التوصية للمشرف مع اعتماد واضح أو استثناء مُدقق يستلزم سببًا وتفويضًا. اختبارات 0/49.99/50/79.99/80/100، وبنود pending، ونسخة البنك، وتعليل المراجعة. لا تمس بيانات V1.

### P0-05 — بوابات GitHub فاشلة على آخر SHA

- **الدليل:** SHA ad024302؛ CI 40573689238 = FAIL: Backend 1113 PASS/1 FAIL (test_v2_content_api.py::test_candidate_media_is_explicitly_test_only؛ بعد قبول الفيديو المؤقت)؛ Frontend 163 PASS/1 FAIL (اختبار Home page يتوقع النص القديم «أنشطة قصيرة بالصوت والصورة والقراءة» بعد تغيير صفحة /). Security PASS وintegration SKIPPED. M04 40573689367 = SUCCESS. M09 40573689281 لم يُحسم عند الاستعلام الأول، والمسار الموازي staging M09 40573676557 فشل باختبار Backend نفسه.
- **الإصلاح:** تحديث assertions إلى سياسة الوسائط المؤقتة الجديدة مع بقاء اختبارات رفض media غير المعتمدة، وتحديث نص Home expected، ثم CI/M04/M09 + Playwright على **نفس SHA** (وبدون حذف اختبارات أو تجاوزها). التحقق من حالات video temp الحقيقي لا يساوي media-final.
- **القبول:** ثلاث بوابات SUCCESS، backend 0 fail وfrontend 0 fail وintegration/E2E 0 fail، مع artifact/trace في حالة فشل سابق.

### P0-06 — لا توجد معاينة معزولة قابلة للتشغيل الكامل

- **الدليل:** Railway project himma-v2-work-preview-20261027، environment staging يحوي Postgres مستقلة وباكت synthetic audio، **ولا توجد Web/API/Redis**. إنشاء API رفض بسبب resource provision limit بحسب W0_ISOLATED_STAGING_BLOCKER_AR.md. Railway production فيه الخدمات الأربع Online ولكنه auto-deploy من v2/01-learning-foundation-20261007 قبل اكتمال CI؛ آخر Web/API SHA ad024302 مطابق وناجح نشرًا فقط.
- **الحل:** تفعيل قدرة موارد معزولة ومفاتيح اختبار وAPI/Web/Redis وصوت وهمي، وعدم ربطها بقاعدة إنتاج/تسجيلات الأطفال؛ منع auto-deploy إلى Production من فروع التطوير حتى QA/موافقة واعتماد exact SHA.
- **القبول:** staging فعلي، /ready وlogin وعشرة سيناريوهات أولية ثم مصفوفة 23 مسارًا، وخطة rollback + نسختي Web/API بنفس SHA.

### P1-01 — بقايا مسارات API V1 تشغل منتجًا موازيًا

- **الدليل:** services/api/main.py ما زال يشمل routers تاريخية assessment، activities، journey، adaptation، reinforcement_review، review، reports، skill_reports، notifications، content_preview وغيرها. أضيفت guards تمنع الطالب الذي يملك StudentJourney من كتابة درجات V1، لكن الحساب التاريخي بلا Journey قد يستمر في مسار V1. صفحات /student/session و/activity و/admin/audio-review حُولت إلى المنتج الحالي، وليست هذه كافية لوقف API القديمة لجميع الحالات.
- **الحل:** dependency graph لكل route وmodel وworker، نقل المزايا المشتركة إلى service V2، غلق إنشاء V1 evidence الجديد لأي حساب يعمل في المنتج النهائي، مع إبقاء البيانات التاريخية للقراءة المصرح بها خارج تجربة المنتج. عدم حذف وحدات auth وStudent وAssessmentSession المشتركة قبل الفصل. اختبار جميع GET/POST القديمة للحساب الحديث والتاريخي، وعدم إنشاء أي Attempt/RewardEvent V1.

### P1-02 — عدم تطابق اعتماد وسائط البنك مع اعتماد منتج تعليمي

- **الدليل:** 19 فيديو درس ترتبط بملف مؤقت مشترك نحو 20 ثانية بـapproved_temporary، بإذن المالك للنسخة المرحلية؛ الجرد يحوي 89 أصلًا و73 مستخدمًا، وصوتين اختياريين بلا ملف. media_readiness_contract يضع publishable إذا كانت ملفات الأصول المطلوبة ready وغير test_only، لكنه لا يختبر بنفس الشرط rights_pending أو توقيع المراجعة التربوية والجهازية؛ ويصف academic_qa_pending بناء على state، وليس إثبات تحكيم لغوي.
- **الحل:** فصل technical_asset_ready عن academic_qa_approved وrights_approved وdevice_qa_passed وrelease_published. إبقاء وصف الفيديو المؤقت متاحًا للعميل/المشرف ولا تقديم نفس الفيديو وكأنه شرح فعلي لكل مهارة. ملف فيديو مستقل لكل درس عند التسليم النهائي أو استثناء صريح بعقد العميل، مع تدقيق النطق والتشكيل وVTT/Safari/Android/ميكروفون/وسائط خيارات الصوت.
- **القبول:** جدول asset_id لكل سؤال/درس مع hash والحقوق والنص المنطوق والمالك والمقاس والـcodec والتجارب؛ 300 سؤال و19 درسًا و12 دعمًا و30+30 ومراجعات صوت من جهازين.

### P1-03 — معنى حدث «مشاهدة الفيديو» والنجوم لا يثبت مشاهدة فعلية

- **الدليل:** v2_lesson_runtime.py::record_lesson_event يقبل client-supplied position_seconds/duration_seconds، ويعتبر video_ended صالحًا عند ratio >=0.9 دون تحقق خادمي من مدة الملف الفعلية أو زمن مرور واقعي؛ v2_rewards.py يمنح intro_video star بناء على intro_seen/video_seen/video_completed_at. معرف الحدث idempotent، لكن صحة المشاهدة نفسها ليست مثبتة.
- **الحل:** اجعل نجمة الفيديو «مشاركة مسجلة» فقط إن كان ذلك مقصودًا، أو اربط إكمال المشاهدة بمدة أصل موثوقة وcheckpoints/timestamps منضبطة وresume/retry دون معاقبة الطفل على buffering؛ افصل المكافأة عن قياس الإتقان تمامًا. اختبارات event فوري 10/10، اختلاف المدة، انتهاء متأخر، تكرار الأحداث/فقد ACK، تحديث الصفحة.

### P1-04 — المحتوى التعليمي والتسكين والاختباران لم يثبت تحكيمهما النهائي

- **الدليل:** D15 في docs/v2/DECISIONS_AR.md يفرق بين اكتمال بنك 300 بنيويًا واعتماد تربوي خارجي نهائي؛ D09 لا يدعي تكافؤ صعوبة قبلي/بعدي مثبتًا. D22/D23 أحدث من D05/D12، واستبدلا 21 سؤال كتابة حرة إلى 9 build_word +12 sequence مع 0 write_text، لكن Backend ما زال يحتفظ بـwrite_text كفرع تاريخي/توافقي.
- **الحل:** توقيع العميل على جميع بنود 300 والتشكيل والأصوات والخيارات والتقوية و13 مهارة و5 محاور ومنطق مستويات 1–3، وحسم توزيع الصعوبة والبدائل، وتأكيد عدم تسريب الإجابة/المعينات في القبلي والبعدي. لا إعادة تأليف عشوائية.
- **القبول:** تقرير content QA موقّع + ملاحظات/تصحيحات إصدار جديد مع الحفاظ على المسار المثبت.

### P1-05 — حالات الانتظار/مراجعة القراءة والاستئناف end-to-end تحتاج إثباتًا حقيقيًا

- **الدليل:** توجد وحدات assessment/lesson review/claim/retry/audio retention والصلاحيات مع اختبارات، لكن لم يُنفذ فحص Work Cloud Browser على نسخة staging موحدة بـ23 route وجميع الحالات وبنك كامل. منطق الصوت الرسمي مراجعة بشرية ولا يجوز ظهور ASR كقرار نهائي. D24: آخر تسجيل معتمد فقط داخل الصوت المحفوظ، تاريخ محاولات وصفية وحذف المؤقت وفق مهلة.
- **الحل:** مصفوفة N جديد، L قديم، P بعد أول جواب، R ينتظر المراجعة، S تقوية، U حساب آخر، مع ملكية صوت وملف آخر تسجيل وحالات repeat/error/503/409/race وrole guard وتقرير المشرف. حافظ على نتيجة المشرف/تسجيله الأخير وعدم حذف الدليل قبل قبول البديل.

### P1-06 — اختبارات حجم وأداء DB غير منفذة وقابلية الزيادة ضعيفة

- **الدليل:** v2_student_readmodel.py:supervisor_v2_cohort_overview يستدعي build_student_v2_home لكل طالب (limit حتى 50)، والدالة تحتوي عدة queries متسلسلة؛ v2_reports.py يجمع أدلة الطلاب للتقرير. هذا خطر N+1 مثبت بالكود، لكن لا قياس حي يثبت بطئًا فعليًا.
- **الحل:** SQL query count/p50/p95/ذاكرة على 50 و500 حساب اصطناعي، prefetch/aggregated queries وpagination للتقارير والصادرات، مع قفل دقة المقارنات الأكاديمية وRBAC. لا تُعلن نتيجة أداء من الانطباع البصري.

### P1-07 — الاختبارات والوثائق التاريخية قد تخلق تعريفًا مزدوجًا للمنتج

- **الدليل:** docs/v2/DECISIONS_AR.md D05/D12 وdocs/v2/13_* تحتوي مصطلح write_text القديم وتوضح D22/D23 لاحقًا الاستبدال؛ compiler.py ما زال يسمّي الملف draft والنسخة candidate؛ العديد من docs/ops خاصة V1 موجودة. الواجهات القديمة أزيلت بقدر كبير لكن الـAPI ما زالت.
- **الحل:** توحيد مواصفات المنتج الحالية في وثيقة canonical واحدة: أسئلة 300، 6 أنواع، مراجعة read_aloud، فيديو 19 مؤقت بإذن منفصل، release state، source of truth، رصد parity للقدرات. وثائق V1 الأقدم توسم historical_reference خارج واجهة المنتج/حزمة التسليم، لا حذف أصول مفيدة.

### P1-08 — التسليم الأول يتطلب خط تشغيل وهجرات ونسخ احتياطية فعليًا

- **الدليل:** production قاعدة مشتركة تضم نموذج V1/V2، لا SQL row counts حي ولا pg_dump + restore مثبت على قاعدة منفصلة، ولا جرد FK أو ملفات تسجيلات الطفل؛ التنظيف UI لا يعادل migration وdata cleanup. Dockerfile ومهاجرات Alembic كثيرة موجودة لكن هذا ليس بديلًا عن تشغيل dry-run مع rollback.
- **الحل:** تجهيز clean fresh-client database ببيانات جديدة وحساب مشرف آمن وبنك published فقط؛ أو ترحيل آمن للخدمة الحالية مع الحفاظ على الأدلة عبر backup/restore؛ اختبار Migrations آخر رأس وتهيئة وتعطّل Redis/S3 وفشل redeploy، DNS/SSL وسياسة Privacy وتدريب العميل على الإدارة.
- **تحذير:** لا DELETE/DROP/TRUNCATE أو استبدال original production أو ملف صوتي للطفل دون inventory+restorable backup+rowcounts+owner final explicit approval.

## القائمة الأخيرة للقدرات الواجب إثباتها قبل توقيع تسليم العميل

1. مسار الطالب: تسجيل جديد → قبلي 30 سؤالًا بكل الأنواع → انتظار/مراجعة قراءات → نتيجة رسمية → قرار التسكين المبرر → أول درس صحيح → 19 درسًا حسب المستوى → 12 دعمًا عند الحاجة دون حلقة → إعادة محاولة ونجوم/شارات → بعدي 30 سؤالًا → تقرير رسمي.
2. مشرف: الدخول والصلاحيات والمستخدمون وإنشاء/تعديل رمز الطالب والمراجعة الصوتية وإعادة التسجيل وإتاحة البعدي والتقارير ومهارات 13 وتصدير Excel/PDF والإشعارات والصوت المقيّم وواجهة محتوى للقراءة؛ كل زر يجب أن ينتج أثرًا خادميًا متحققًا وليس استجابة HTTP200 فقط.
3. جرد الصفحات: 15 مشرفًا +7 طالب + الصفحة العامة = 23 مسارًا أساسيًا، مع routes الديناميكية والخفية، 320/390/768/1440، keyboard، RTL، 200% zoom، شبكة بطيئة/offline، 401/403/409/422/500/503.
4. تعليم: 300 سؤال/33 قسمًا/6 تفاعلات بدون write_text، 19 فيديو (مؤقت معتمد للنسخة المرحلية فحسب) و12 support/13 skill، وحسم تعلم الطلاب المدعومين دون فرض فيديو Support مستقل.
5. التشغيل: secure cookies وrate limit وASR غير حاكم وملفات الأطفال الخاصة وعدم كشف أجوبتهم؛ Web/API نفس SHA؛ CI/M04/M09 ناجحة؛ staging بلا بيانات حقيقية؛ restore + rollback + دليلا تدريب وتسليم.

## ترتيب التنفيذ القابل للقياس — لا تتجاوز البوابات

- **Gate G0/الحجر:** امنع التحديث الآلي إلى production قبل CI، حل موارد staging أو بيئة معزولة مصرح بها؛ لا مساس بـA/B/C المتوقفة.
- **Gate G1/P0 أكاديمي:** منع تجاوز قبلي/تسكين، تثبيت المحتوى end-to-end (questions/support/media/next/rewards)، وتثبيت سياسة التسكين؛ اختبارات API + PostgreSQL + E2E وحالات رفض الطلب المباشر وتغير نسخة البنك.
- **Gate G2/الإصدار:** آلية compile→validate→approve→publish + release pin + real runtime production، ومسح الرسائل التطويرية *بعد* نجاح حالة الإصدار.
- **Gate G3/V2-only:** إزالة ما بقي من API V1 وقراءات/كتابات V1 بمراجعة dependencies والحفاظ على auth/shared DB والقدرات الحقيقية؛ لا إبقاء تشغيل تاريخي ظاهر أو background writes.
- **Gate G4/المحتوى والصوت:** اعتماد الوسائط المؤقتة المشروط، QA نطق/صور/قراءة+حقوق، خصوصية S3 ومراجعة الأطفال والنجوم والتلميحات.
- **Gate G5/التشغيل والأداء:** قياس cohort 50/500، CI/M04/M09، Work browser 23 مسارًا/سجل مشرف/طالب وفحوص الأجهزة، تجربة النسخ الاحتياطي والاستعادة، حزمة تدريب.
- **Gate G6/العميل:** release candidate مقفل وchangelog/QA matrix وcredentials handoff آمن وrollback ثم توقيع قبول العميل والمالك؛ لا تخالف موافقة البيانات المستقلة.

## حالة الدليل وموانع الاستنتاج

- **فحص الآن:** قراءة كود/Docs وGitHub jobs وRailway deployment/env inventories، وليس اختبار متصفح مصادق لكامل 23 مسارًا. محاولة فتح الموقع بأداة الويب في هذه الجولة لم توفر وصولًا يمكن الاعتماد عليه للفحص التفاعلي. يمكن فحص المتصفح في Work Cloud Browser عندما تتوفر بيئة معاينة مصادق عليها.
- إنتاج Railway حاليًا أربع خدمات Online وWeb/API على SHA ad024302، لكن CI على نفس SHA FAILED (backend 1/1114 وfrontend 1/164)، وM04 SUCCESS وM09 لم يكتمل عند التحقق.
- staging المعزول: Postgres + bucket فقط؛ لا Web/API/Redis قابلة للاختبار، resource limit blocker.
- A/B/C PAUSED ولا تعاد؛ لم أنفذ حذف بيانات أو migration أو نشرًا خلال هذا التدقيق.
- **هذا التقرير يقوّم أحدث فرع رسمي رغم حفظه في فرع التنظيف الآمن**. إن تغير HEAD تُعاد المقارنة وتُحدث حالات الأدلة؛ لا تطبق إصلاحات فرع التنظيف الأقدم فوق الكود الجديد بالجملة.

## مصادر الملفات المهمة

- docs/v2/DECISIONS_AR.md ؛ docs/v2/09_IMPLEMENTATION_ROADMAP_AR.md
- docs/v2/agent-ops/WORK_BROWSER_ACCEPTANCE_MATRIX_20261027_AR.md ؛ docs/v2/agent-ops/V2_ONLY_CLEANUP_INVENTORY_20261027_AR.md
- docs/v2/work-owner/W2_ADMIN_PRODUCT_STRUCTURE_AND_GAP_REGISTER_20261027_AR.md
- docs/v2/work-owner/W7_OWNER_MEDIA_AND_SUPPORT_PATH_20261027_AR.md
- docs/v2/work-owner/W8_REMAINING_GAPS_AND_PERFORMANCE_20261027_AR.md
- services/api/v2_lesson_runtime.py ؛ v2_interaction_runtime.py ؛ v2_adaptation_runtime.py ؛ v2_adaptation_policy.py
- services/api/v2_content/repository.py ؛ v2_content/compiler.py ؛ v2_content/importer.py ؛ v2_content/media.py ؛ v2_content/readiness.py
- services/api/v2_assessment_runtime.py ؛ v2_student_readmodel.py ؛ v2_student_accounts.py ؛ v2_rewards.py
- .github/workflows/ci.yml و m09-release-readiness.yml
