# منصة هِمّة — MASTER CONTINUITY HANDOFF

التاريخ: 2026-09-09

الحالة: **IN PROGRESS — تنفيذ فعلي على فرع تكامل مستقل، بلا Merge أو Deploy**

المستودع الرسمي: `7eaur/himma-`

فرع العمل الحالي: `integration/canonical-content-2026-09-08`

نقطة الكود قبل إنشاء هذا الملف: `2df6ce570c3254cf8f482b80a439d3bc3d83f99b`

> هذا الملف هو مرجع استمرارية شامل لمحادثة جديدة. المطلوب من أي وكيل لاحق أن يقرأه أولًا، ثم يراجع الملفات المشار إليها، ثم يواصل من الحالة الحالية بدل إعادة التحليل من الصفر. لا تعتبر أي نتيجة «مغلقة» إلا إذا كان لها دليل تشغيل فعلي، وليس مجرد كود مكتوب أو GitHub Action لم يبدأ خطواته.

---

## 1) ما هي منصة هِمّة؟

هِمّة منصة تعليمية عربية موجهة لطلاب الصف الثالث ممن لديهم صعوبات في القراءة. المنصة ليست مجرد بنك أسئلة؛ هي مسار تعلم تكيفي كامل يربط الاختبار القبلي، تحليل الاستجابة والقراءة، التصنيف، الأنشطة الأساسية، التقوية الموجهة، المراجعة الصوتية، ثم الاختبار البعدي والتقارير.

مسار الطالب المعتمد:

`دخول بكود طالب → اختبار قبلي → تحليل/تصحيح → تصنيف مستوى → أنشطة أساسية → تقوية حسب الضعف → متابعة تكيفية → اختبار بعدي → تقارير المشرف`

التحليل الصوتي المستهدف معماريًا هو **Reference-Guided Arabic Reading Analysis**: النص المطلوب معروف مسبقًا، لذلك لا يعتمد النظام على ASR حر فقط؛ الفكرة هي التعرف الصوتي ثم المحاذاة مع النص المرجعي وتحليل Correct / Deletion / Insertion / Substitution مع تحليل فونيمي مساعد عند الحاجة.

---

## 2) العقود الأكاديمية الثابتة

الحجم النهائي للمحتوى المعتمد:

- الاختبار القبلي: **30 سؤالًا**.
- الأنشطة الأساسية: **30 نشاطًا**، 10 لكل مستوى.
- التقوية: **35 نشاطًا** موزعة: L1=12، L2=11، L3=12.
- الاختبار البعدي: **30 سؤالًا**.
- الإجمالي: **125 عنصرًا**.
- عدد المهارات الرسمية المستهدفة في الكتالوج: **44 مهارة**.

التصنيف بعد الاختبار القبلي:

- أقل من 50% → المستوى الأول.
- من 50% إلى أقل من 80% → المستوى الثاني.
- من 80% إلى 100% → المستوى الثالث.

السياسة التكيفية الرسمية الموجودة في المستودع المتقدم يجب الحفاظ عليها ما لم يوجد قرار أحدث صريح:

- نجاح النشاط عند >= 80.
- من 70 إلى أقل من 80: Guided Retry.
- أقل من 70: Reinforcement.
- الترقية المبكرة مبنية على أدلة فعلية، مع شرط 6 أنشطة أساسية وإتقان 85 وحد أدنى 70 للمهارات الحرجة.
- لا يوجد Auto-Demotion عشوائي.
- المستوى الثالث يمر بجميع 10 أنشطة أساسية.
- أوزان الأدلة المعتمدة في V4: 50/30/20 حسب العقد الموجود في طبقة التكيف.

لا تغير هذه السياسة أثناء إصلاح المحتوى إلا بقرار مستقل واضح.

---

## 3) قواعد العمل غير القابلة للتجاوز

1. لا تنقل كود Sandbox نسخًا ولصقًا إذا كانت معمارية الرسمي أفضل. انقل **النية والقرار الأكاديمي** فقط.
2. لا تعالج مشكلة محتوى بإضافة Seed/Repair جديد فوق إصلاحات قديمة. الحل يجب أن يكون في المصدر الكانوني/Compiler/Publisher/Serializer المسؤول.
3. Runtime الطالب يقرأ **Structured DB Runtime فقط**. لا Parsing لـ`source_text` ولا JSON مرجعي في وقت الطلب.
4. لا تخمّن ربط الصور بالخيارات حسب ترتيبها. الربط Semantic وصريح، وإذا لم يوجد Mapping موثوق يفشل العقد بدل التخمين.
5. لا تحذف History لإجابات الطلاب. IDs القديمة التي تشير لها AttemptResponse يجب أن تبقى صالحة.
6. لا تستخدم Docker في مسار العمل الحالي.
7. لا Merge إلى الفروع الأساسية ولا Deploy ولا تعديل Production قبل اكتمال بوابات التحقق وطلب المستخدم ذلك صراحة.
8. لا تقول إن CI Green إذا لم تبدأ خطواته فعلًا.
9. إذا وجدت ملفًا قديمًا يخالف اعتماد أحدث، الأحدث هو الأعلى أولوية وفق ترتيب مصادر الحقيقة أدناه.
10. كل إصلاح جذري يجب أن يصاحبه Regression Test يثبت القرار.

---

## 4) ترتيب مصادر الحقيقة

عند وجود تعارض، استخدم هذا الترتيب:

### أ) أعلى سلطة أكاديمية حالية

وثائق اعتماد 2026-09-08 الموجودة في مستودع Sandbox `7eaur/himma-deployment-sandbox`:

1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-08_AR.md`
2. `docs/HIMMA_CONTENT_APPROVAL_MASTER_INDEX_2026-09-08_AR.md`
3. Approved Changesets: PRE / L1 / L2 / L3 / POST
4. Media Requirements
5. Root-cause / invariants docs
6. Execution transfer/correction logs
7. PR #3 transfer log
8. كود PR #2 وPR #3 كمرجع نية، لا كمرجع معماري واجب النسخ.

### ب) المستودع الرسمي

المعمارية الحالية في `7eaur/himma-` هي المرجع الهندسي إذا كانت أقوى وأكثر اتساقًا. الفرع المتقدم الذي استُخدم كأساس عملي هو خط `recovery/ui-media-admin-overhaul` ثم فروع reconciliation/canonical الحالية، وليس `stage/02-content` القديم.

### ج) الملفات المرجعية الأقدم

الملفات المرفقة بالمشروع مفيدة لفهم الفكرة والهوية والتاريخ، مثل:

- `05_توثيق_فكرة_المشروع_ومتطلبات_العميل_للمبرمج.docx`
- `06_دليل_الهوية_البصرية_لمنصة_همة.pdf`
- `00_حالة_المشروع_ومؤشر_الاعتماد_v1.2.pdf`
- `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md`
- `himma_comprehensive_audit_2026-08-16.docx`
- حزم الصور/الشخصيات/الصوت والمستودع الموحد.

هذه لا تتقدم على اعتماد 8 سبتمبر إذا تعارضت معه.

---

## 5) أهم قرارات المحتوى المعتمد بتاريخ 8 سبتمبر

### قواعد عامة

- السؤال المباشر منفصل عن التعليمة.
- المحتوى المنظم في DB هو ما يصل للطالب.
- `source_text` تاريخي/هجرة فقط.
- خيار الصورة يظهر **الصورة فقط**، بلا Label نصي يكشف الإجابة.
- كل خيار منطقي له صورة واحدة مطابقة دلاليًا عندما يكون نوع السؤال Image Choice.
- لا قاعدة تقول «أضف خيارًا رابعًا دائمًا». عدد الخيارات حسب العقد الأكاديمي الفعلي.
- الصحة Explicit وليست مستنتجة من الترتيب.
- القصة لها شاشة استماع مستقلة قبل الأسئلة.
- Timed Reading يقيس الزمن داخليًا ولا يعرض عدادًا يضغط الطالب.
- Sequence يعتمد الصور/الأحداث الفعلية، لا نصوصًا مختصرة تكشف الترتيب.

### PRE

- Q10 يستخدم صورًا.
- Q11 short vowels له 3 خيارات فقط.
- Q13 sequence له 3 عناصر.
- Q17 يحتاج الخيار الرابع «بيت» مع صورة بيت حقيقية منفصلة.
- Q25–Q30 لا تعرض صورة القصة داخل جولة السؤال.

### L1

- 10 Core + 12 Reinforcement.
- `L1-REIN-02` اختيار من صورتين.
- قصتا ليان ونادر لهما Intro مستقل.
- `L1-REIN-12` Sequence مع أزواج صور فعلية.

### L2

- 10 Core + 11 Reinforcement.
- `L2-REIN-07` قراءة كلمات فقط، والكلمات المعتمدة:
  `كَتَبَ، لَعِبَ، رَسَمَ، فَتَحَ، جَلَسَ`.

### L3

- 10 Core + 12 Reinforcement.
- `L3-CORE-07` لا صورة في الأسئلة المباشرة.
- `L3-REIN-07` ثلاث كلمات في كل جولة:
  - `باب شمس نخلة`
  - `مدرسة عصفور حقيبة`
  - `يلعب يكتب يذهب`
- `L3-REIN-11` الجملة والسؤال والخيارات حقول منفصلة.

### POST

- كان هناك تسرب source في Q8 وQ13 وتم إغلاقه في العقد الكانوني.
- `POST-Q11` الحقيقة الأكاديمية النهائية: **`مَ`**.
- `POST-Q11` الصحيح والصوت المستهدف والStimulus والمعيار كلها `مَ`.
- لا خيار رابع مصطنع في POST-Q11.
- Q25–Q29 أسئلة قصة بلا Story Image في جولة السؤال.

---

## 6) الصوت — الأصول والعقد الأكاديمي

حزمة الصوت الرسمية: `assets/audio/HIMMA_AUDIO_V1/`.

الـManifest يحتوي **54 Asset**، ولكل Asset WAV وMP3، أي 108 ملفًا صوتيًا في الحزمة المكتملة.

التوزيع المعروف:

- FB = 4
- LET = 6
- SYL = 13
- WRD = 29
- INS = 2

أمثلة حاسمة:

- `LET-01 = مَ`
- `SYL-13 = سَا`
- `WRD-29 = موز`
- `INS-01 = قصة ليان`
- `INS-02 = قصة نادر`

قرار مهم: لا تربط حرفًا غير مشكول مثل `م` آليًا بـ`LET-01` فقط لأنه قريب نصيًا؛ `LET-01` تسجيله الحالي `مَ`. الـAudio Resolver يجب أن يحترم الدلالة الصوتية/التشكيل.

أثناء العمل ظهر عيب أن استبدال `STEP_MEDIA` بصور جديدة كان يحذف Prompt Audio القديم في أنشطة استماع مصورة. تم إصلاح المبدأ جذريًا: **الصورة والصوت عقدان مستقلان**. تغيير الصور لا يلغي الصوت.

تثبيتات مهمة:

- أهداف L1 السمعية المطلوبة: `م، ب، س، ق، ن` حسب عقود الأنشطة ذات الصلة.
- `POST-Q05 = ب`.
- مهام مقارنة onset pair أصبحت تنشر **تسلسل صوتي صريح لكلمتين** عندما يكون العقد متعدد Prompt، ولا يقبل النظام إنشاء multi-prompt ضمني بلا عقد صريح.

---

## 7) سياسة مراجعة تسجيل الطالب — ما يجب الحفاظ عليه وما لم يُنقل بعد

المبدأ الأكاديمي/التشغيلي المعتمد:

- التسجيل المرفوع `uploaded/pending` لا يعتبر نجاحًا ولا رسوبًا أكاديميًا؛ Evidence محايد حتى مراجعة المشرف.
- لكن التسجيل المعلق **لا يجب أن يوقف تنقل الطالب بين الأنشطة والجولات الباقية**.
- يمكنه أن يمنع الترقية/إغلاق المستوى فقط إذا كانت نتيجة التكيف ستنقل الطالب لمستوى أعلى أو تكمل المستوى الثالث قبل حسم الصوت.
- `rerecord_required` يظهر كمهمة للطالب، ولا يقطع مساره إلا عندما يفتح الطالب مهمة إعادة التسجيل صراحة.
- التقييم البشري المعتمد هو المرجع النهائي للصوت؛ لا تحول pending إلى درجة آلية.

في Sandbox يوجد مرجع تنفيذ جيد للنية:

- `services/api/audio_review_policy.py`
- `services/api/audio_review_navigation.py`

وفيه Navigation State منفصل عن Academic State، مع hold قبل promotion وليس قبل كل نشاط.

**الحالة الحالية في الفرع الرسمي:** هذان الملفان غير موجودين حتى نقطة هذا Handoff، ولذلك هذا البند **ما زال مفتوحًا ويجب تنفيذه/تكييفه** مع معمارية الرسمي بدل نسخه أعمى.

في الرسمي الحالي `activity_runtime.py` ما زال `effective_step_state` الأكاديمي يتعامل مع pending كخطوة غير منتهية، وهذا هو السبب الذي يمكن أن يمنع `/next` من التقدم. المطلوب فصل Navigation Completion عن Academic Evidence.

---

## 8) قرار معماري جذري للمحتوى الكانوني

تم رفض نموذج Sandbox القديم الذي يبني الحقيقة عبر سلسلة Seed/Projection/Repair overlays متتالية.

المعمارية الحالية المقصودة:

`Historical/Bootstrap Sources → Canonical Compiler in memory → Canonical Release Validation → Transactional Publisher → Structured DB Runtime → Shared Student Serializer`

المعنى:

1. المصادر القديمة تستخدم لإنشاء الهوية والبنية التاريخية فقط عند الحاجة.
2. كل القرارات الأكاديمية تُجمع في Release واحد منظم في الذاكرة.
3. يتم فحص الـRelease كاملًا قبل الكتابة.
4. Publisher واحد ينشر إلى PostgreSQL في Transaction واحدة.
5. لا يوجد Final Repair Seed بعده.
6. Runtime لا يعود للمصدر التاريخي.

الملفات المركزية:

- `services/api/content_approval_contract_2026_09_08.py`
- `services/api/canonical_content_compiler.py`
- `services/api/canonical_release.py`
- `services/api/canonical_content_publisher.py`
- `services/api/content_projection_digest.py`
- `services/api/content_runtime.py`
- `services/api/content_student_view.py`
- `services/api/posttest_presentation_2026_09_01.py`
- `services/api/seed_all.py`
- `services/api/readiness.py`

---

## 9) دورة حياة الخيارات وحماية التاريخ

المستودع الرسمي يضيف `ContentOption.is_active` عبر migration:

`services/api/alembic/versions/0011_active_content_options.py`

العقد:

- الخيار الحالي Active.
- إذا تغير النص/الصحة/الترتيب، لا تغير معنى صف قديم استخدمه طالب تاريخيًا.
- الصف القديم يصبح Inactive بدل الحذف.
- `AttemptResponse.selected_option_id` التاريخي يبقى محفوظًا وصحيح المرجع.
- Runtime والطالب يرون Active Options فقط.
- submit لا يقبل Option ID قديمًا أو تابعًا لسؤال آخر.

التطبيع الرسمي `visible_key` يحذف التنسيقات غير المرئية ويطبّع Unicode/المسافات، لكنه **يحافظ على التطويل والحركات والفروق العربية التعليمية**. لا تستبدله بمنطق Sandbox الذي كان أشد حذفًا.

التكرار المرئي مسموح فقط في مهام ORDER عندما يكون جزءًا مقصودًا من الإجابة، مثل تكرار حرف في بناء كلمة.

---

## 10) الوسائط والصور

حزمة الصور التعليمية الأصلية تحتوي 60 أصلًا منطقيًا تقريبًا: Vocabulary + Sentences + Sequences + Stories. تم التحقق سابقًا أن أغلب فجوات الـSequence التي ظهرت في تقارير قديمة كانت موجودة بالفعل في المستودع الرسمي عبر generated sequence map، لذلك لم تُولد بدائل مكررة.

الفجوة الحقيقية كانت صورة `بيت` لـ`PRE-Q17`.

تم إغلاقها فعليًا في الفرع الحالي:

- Stable ID: `HIMMA-GEN-VOC-001`
- manifest: `assets/education/developer/generated-vocabulary-map.json`
- الملف: `assets/education/generated_vocabulary/webp/hem-gen-voc-001-house-512.webp`
- الصورة مفردة، بلا نص مضمن، ومخصصة كخيار Vocabulary آمن للطالب.

لا تنشئ صورة بديلة ثانية لنفس المعنى ما دام هذا الأصل موجودًا ويمر QA.

قواعد ربط الوسائط:

- Choice Image ترتبط بخيار بعينه دلاليًا، ثم Option ID.
- Supporting/context media لا تتحول Choice.
- لا positional inference.
- عند أي غموض Fail Closed.

---

## 11) عرض الطالب وترتيب الخيارات

كان هناك عدم اتساق: Assessment يخلط، Learning يعتمد DB order، وPreview قد يعرض ترتيبًا آخر. تم توحيد Presentation Order في السيرفر داخل:

`services/api/content_student_view.py`

العقد:

- `order_index` في DB = Academic Order المستخدم في التصحيح/بناء الإجابة.
- Presentation Order = ترتيب عرض مستقل وحتمي للطالب.
- Assessment / Learning / Preview يجب أن تستخدم نفس Serializer.
- إذا أعيد ترتيب الخيارات المرئية، تنتقل صورة كل خيار معه حسب `option_id`، لا حسب موضع الصورة القديم.
- Prompt Audio وContext Image لا تتحرك كأنها خيار.

---

## 12) القصص والقراءة الزمنية

- `INS-01` قصة ليان: شاشة استماع مستقلة قبل الأسئلة.
- `INS-02` قصة نادر: شاشة استماع مستقلة قبل الأسئلة.
- لا Story Player جديد داخل كل سؤال بعد الاستماع.
- لا Recording إضافي في أسئلة القصة إلا إذا العقد يقول ذلك.
- الأسئلة ذات سياق القراءة تعرض السياق مرة بالطريقة المعتمدة ثم السؤال.
- Timed Reading يخفي العدّاد عن الطالب لكن يحتفظ بقياس الزمن داخليًا.

---

## 13) الـDigests والجاهزية

هناك مستويان للحماية:

### Canonical Release SHA-256

يمثل المصدر الكانوني النهائي نفسه.

### Canonical Projection SHA-256

يمثل ما يستهلكه الطالب فعليًا في DB: العناصر، المهارات، الجولات، Active Options وصحتها، الوسائط الحالية، والعرض المنظم.

الخيارات التاريخية Inactive تبقى في DB لكنها لا تدخل في Digest العرض الحالي.

الـPublisher يثبت Projection Digest في نفس Transaction ويعيد حسابه قبل Commit. `/ready` يعيد التحقق ويغلق الجاهزية عند الاختلاف.

Readiness يجب أن يفشل عند:

- عدد غير 125.
- توزيع PRE/LEARNING/POST خاطئ.
- Runtime Version قديم.
- Release Version/Digest غير متطابق.
- Projection Digest لا يطابق DB.
- أكثر/أقل من Release واحدة Active.
- عنصر حالي غير Approved.
- حزمة الصوت الـ54 غير مكتملة.
- DB/Redis/Object Storage/Config غير جاهز.

---

## 14) Seed Twice والذرية

المسار الكانوني تطور بعد نقطة checkpoint الأولى:

- النشر الكانوني أصبح مسؤولًا عن **Atomic Bootstrap** للبنية المطلوبة بدل تشغيل سلسلة legacy seeders ثم الإصلاح فوقها.
- تم إزالة legacy seeders من publication path النهائي.
- اختبارات أضيفت لإثبات rollback الذري عند الفشل، ولتثبيت أعداد bootstrap.
- `seed_all.py` يحافظ على عقد النتيجة/العدد لكنه لم يعد يجعل repair overlays القديمة مصدر الحقيقة النهائي.

يوجد Gate:

`services/api/verify_canonical_seed_idempotency.py`

والمطلوب منه على PostgreSQL حقيقي:

- نشر الإصدار مرتين على نفس DB.
- Release SHA ثابت.
- Projection SHA ثابت.
- لا تغييرات غير لازمة في Options/Media في التشغيل الثاني.
- IDs للعناصر والجولات والخيارات والمهارات والRelease ثابتة.
- 125 عنصرًا و44 مهارة.
- Release Active واحدة.

لا تعتبر Unit Test بديلًا عن هذا PostgreSQL gate.

---

## 15) آخر تنفيذات مهمة بعد ملف Checkpoint السابق

بعد checkpoint الذي كان عند `f97b3a3...` تقدم الفرع بـ17 commit حتى `2df6ce5...`، ومن أهم القرارات التي تمت:

- توثيق checkpoint الكانوني.
- جعل Canonical Publication يقوم بالـbootstrap ذريًا.
- إزالة legacy seeders من publication path النهائي.
- اختبارات rollback atomic وأعداد bootstrap.
- الحفاظ على تعليمات وتلميحات وعرض الأنشطة المعتمدة بدل فقدها أثناء compiler projection.
- تثبيت عقد Seed Result Count.
- تثبيت عقد onset-pair الصوتي.
- نشر تسلسلات مقارنة كلمتين صوتيًا عندما يكون العقد صريحًا.
- اختبارات playback وserializer للعقود متعددة الـprompt.
- استبدال assertions التي كانت تختبر overlays متقاعدة بمعاني Canonical V2.
- استخدام item media helper صريح لStory Intro في الاختبارات.
- إزالة metadata العرض الخاصة بالoverlays المتقاعدة من `canonical_content_publisher.py` حتى لا يبقى مصدران ظاهران للحقيقة بعد النشر الكانوني.

آخر commit كود قبل هذا Handoff:

`2df6ce570c3254cf8f482b80a439d3bc3d83f99b` — `fix(content): retire superseded runtime overlay metadata`

---

## 16) الاختبارات المهمة الموجودة حاليًا

أهم اختبارات الانحدار التي يجب المحافظة عليها وتشغيلها:

- `test_content_approval_contract_2026_09_08.py`
- `test_sep8_approval_projection.py`
- `test_canonical_content_compiler.py`
- `test_listening_media_resolution.py`
- `test_posttest_structured_presentation.py`
- `test_student_presentation_order.py`
- `test_full_student_content_integrity.py`
- `test_content_surface_parity.py`
- `test_seed_all.py`
- `test_readiness.py`
- اختبارات bootstrap atomic/rollback.
- اختبارات onset-pair audio/playback/serializer.

أي محادثة جديدة يجب ألا تحذف هذه الاختبارات لمجرد جعل suite تمر؛ تصلح السبب.

---

## 17) حالة CI الحالية

لا يوجد حتى الآن دليل CI أخضر صالح للدمج.

الـGitHub Actions التي تم فحصها سابقًا كانت تنشئ Jobs frontend/backend/security ثم تنتهي failure خلال ثوانٍ مع `steps=null` وبدون logs، بينما integration يصبح skipped. هذا يعني أن الاختبارات نفسها لم تبدأ في تلك الـRuns.

إذًا:

- لا تصفها كفشل pytest أو TypeScript.
- ولا تصف الفرع بأنه Green.
- يجب أولًا التأكد أن Runner/Account/Workflow بدأ تنفيذ Steps فعلية، ثم قراءة نتائجها.

بعد أي commits جديدة، افحص أحدث Run بدل الاعتماد على Run قديم.

---

## 18) ما تم إنجازه مقابل ما بقي

### مغلق هندسيًا على مستوى التصميم/الكود، لكنه ما زال يحتاج تشغيل فعلي

- Source of Truth الكانوني بدل سلسلة repair overlays.
- Active option lifecycle مع حماية history.
- Compiler + Release validation + Transactional Publisher.
- Structured DB Runtime.
- Shared student serializer/presentation order.
- POST-Q11 = `مَ` دلاليًا وصوتيًا.
- حفظ Prompt Audio عند تحديث الصور.
- Posttest structured presentation.
- Semantic image mapping.
- صورة البيت PRE-Q17 موجودة فعليًا في الفرع.
- Story intro / timed reading contracts.
- Release/Projection digests وReadiness.
- Atomic bootstrap direction + retirement of legacy publication path.
- explicit onset-pair multi-audio semantics.

### ما زال مفتوحًا ويجب أن يبدأ منه الوكيل التالي

1. **Audio review navigation**: فصل Navigation State عن Academic State حتى pending upload لا يوقف بقية الأنشطة، مع hold قبل promotion فقط، وrerecord explicit task.
2. إيجاد/تثبيت route الطالب الذي يسجل بداية `rerecord_required` بشكل صريح عبر AuditLog أو عقد مكافئ، قبل الاعتماد على منطق Sandbox كما هو.
3. تعديل `learning_experience.py` ليختار الخطوة حسب Navigation State الجديد، مع إبقاء evidence الأكاديمي محايدًا حتى grade.
4. مراجعة ترتيب تسجيل routers في `main.py` إذا تم استخدام Overlay Router؛ يجب أن تكون الملكية صريحة وليست مصادفة ترتيب. الأفضل إن أمكن دمج القرار في architecture الرسمي بدل duplicate routes غير واضحة.
5. تشغيل/إصلاح Backend Unit+Integration tests عندما يبدأ Runner فعلًا.
6. تشغيل migration roundtrip و`alembic upgrade head` ثم seed twice على PostgreSQL حقيقي.
7. تشغيل media/audio validators على الحالة المنشورة.
8. مراجعة frontend student activity/assessment/preview والتأكد أنها تستهلك Serializer المشترك ولا تعيد منطق shuffle/media من عندها.
9. التأكد من ثبات زر الصوت: play/pause/resume، hit area ثابت، بدون scaling animation يسبب فقد الضغط.
10. تشغيل رحلة E2E كاملة: login → pretest → placement → L1/L2/L3 → reinforcement → pending audio behavior → rerecord → supervisor grade → promotion → posttest → reports.
11. Security/lint/typecheck/build/frontend tests.
12. عند اكتمال الأدلة فقط يتم إعداد تقرير قبول نهائي، ثم انتظار موافقة المستخدم قبل Merge/Deploy.

---

## 19) نقطة البدء العملية للمحادثة التالية

ابدأ من البند الصوتي، لا من إعادة كتابة المحتوى من جديد.

التسلسل المقترح:

1. اقرأ هذا الملف كاملًا.
2. اقرأ `docs/maintenance/CANONICAL_CONTENT_EXECUTION_CHECKPOINT_2026-09-09_AR.md`.
3. اقرأ `docs/maintenance/CANONICAL_CONTENT_PORT_2026-09-08_AR.md`.
4. اقرأ `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`.
5. افحص HEAD الحالي للفرع ولا تفترض أنه ما زال `2df6ce5` إذا جاءت commits بعد هذا الملف.
6. افحص `activity_runtime.py`, `learning_experience.py`, `main.py`, `adaptation.py`, `adaptation_runtime.py`, وRoutes الطالب الخاصة بإعادة التسجيل.
7. قارن نية Sandbox في `audio_review_policy.py` و`audio_review_navigation.py` مع الرسمي، ثم نفذ الحل الأنسب في الرسمي.
8. أضف اختبارات تثبت: pending يسمح بالتقدم، pending يمنع promotion فقط عند الحاجة، rerecord لا يقطع المسار حتى فتح المهمة، graded evidence يدخل التكيف بصورة صحيحة.
9. بعدها انتقل للبوابات التشغيلية الكاملة.

---

## 20) ممنوعات واضحة للوكيل التالي

- لا تبدأ Branch جديدة ما دام `integration/canonical-content-2026-09-08` هو فرع العمل المتفق عليه، إلا إذا وجد سبب قهري وطلب المستخدم ذلك.
- لا تدمج `stage/02-content` أو Sandbox ككتلة واحدة.
- لا تعيد `student_experience_version`, `onset_pair_version`, `onset_pair_compare`, `auditory_story_version`, `auditory_story` كطبقة Runtime authority بعد أن أصبحت Metadata overlays متقاعدة.
- لا تعيد source parsing إلى Runtime.
- لا تعيد positional image mapping.
- لا تحذف inactive options/history.
- لا تحول pending audio إلى score.
- لا تسمح لـpending audio أن يجمد الطالب في نفس النشاط للأبد.
- لا تقفز مباشرة إلى Merge/Deploy بسبب أن الكود يبدو صحيحًا.
- لا تعتبر GitHub Action بلا Steps دليل جودة.

---

## 21) كيف تتعامل مع طلب المستخدم

المستخدم يريد تنفيذًا فعليًا لا تقارير نظرية متكررة. عندما يقول «كمل» نفّذ، وعندما تسأله عن قرار اجعله قرارًا لا يمكن حسمه من المصادر فقط. اشرح باختصار أين وصلت، ما الذي أُغلق بالدليل، وما الذي بقي. إذا وجدت عيبًا، أصلحه جذريًا ثم اختبره بدل إضافة ترقيع جديد.

المستخدم لا يريد Merge/Deploy قبل اكتمال العمل والتحقق. الحفاظ على التصميم الأنيق والمحتوى المعتمد والصور والأيقونات والقصص والصوت جزء من جودة المنتج، وليس مرحلة تجميل لاحقة.

---

## 22) البرومبت القصير لمحادثة جديدة

انسخ هذا النص في بداية المحادثة الجديدة:

> افتح المستودع الرسمي `7eaur/himma-` على الفرع `integration/canonical-content-2026-09-08`. اقرأ أولًا وبالكامل `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-09_AR.md` ثم الملفات التي يحددها بترتيبها. افهم الحالة الحالية ولا تعِد التحليل من الصفر. تابع التنفيذ من أول بند مفتوح، وحل جذريًا لا عبر Repair/Overlay جديد. لا تستخدم Docker، ولا Merge/Deploy حتى تكتمل اختبارات backend/frontend/integration/security/seed-twice/media/audio/E2E فعليًا وتعرض لي النتيجة. إذا كان HEAD أحدث من المذكور في الملف فاعتبر Git الحالي هو الحقيقة التنفيذية وحدث سجل التوثيق مع تقدمك.

---

## 23) الخلاصة التنفيذية في سطرين

المحتوى الكانوني ومعماريته انتقلا جذريًا من سلسلة إصلاحات متراكمة إلى Release واحد منظم يُتحقق منه ثم يُنشر ذريًا إلى DB مع حماية history وربط دلالي للوسائط والصوت. أكبر بند وظيفي مفتوح الآن هو **فصل تنقل الطالب عن حالة المراجعة الأكاديمية للصوت**، ثم إثبات النظام كاملًا بتشغيل PostgreSQL/CI/E2E حقيقي قبل الدمج أو النشر.
