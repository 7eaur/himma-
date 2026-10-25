# هِمّة V2 — P09.0: استلام خط الأساس للواجهات والوظائف وأدلة الاختبار

**تاريخ التدقيق:** 2026-10-25  
**الفرع:** `v2/01-learning-foundation-20261007`  
**SHA المرجعي:** `9d95d2b2cb13a3fb2a8815226ad7942f483fe537`  
**الحالة:** P09.0 قيد التنفيذ؛ المالك أجاز الانتقال من P08 بعبارة «تم». هذا **جرد مثبت بالمصدر ومعاينة للقطات الاختبار** وليس ادعاء إكمال بوابة P09 كلها.  
**المراجع الملزمة:** `09_IMPLEMENTATION_ROADMAP_AR.md`، `22_FULL_SYSTEM_COVERAGE_AND_ACCEPTANCE_MATRIX_AR.md`، `25_V1_TO_V2_FEATURE_PARITY_REGISTER_AR.md`، `26_V1_IDENTITY_PAGES_AND_FIXED_REGRESSIONS_AUDIT_AR.md`، `51_P08_P10_SUPERVISOR_STUDENT_UX_PLAN_AR.md`.

## 1. أدلة صحيحة على HEAD نفسه

| الدليل | الوضع | التفاصيل |
|---|---|---|
| CI — Quality Gate | PASS | [Run 40219322373](https://github.com/7eaur/himma-/actions/runs/40219322373)، Backend/Frontend/Security/Integration ناجحة على SHA المرجعي |
| M04 — Responsive Visual Gate | PASS لنطاقها فقط | [Run 40219322456](https://github.com/7eaur/himma-/actions/runs/40219322456)، الأثر `m04-responsive-screenshots` يحوي **15 لقطة**: landing/student-login/supervisor-login في 360 و390 و768 و1024 و1440، **لا يشمل لوحات مصادقًا عليها** |
| M09 — Release Readiness Gate | PASS لنطاقها | [Run 40219322496](https://github.com/7eaur/himma-/actions/runs/40219322496)، نجاح بوابة الاختبارات لا يعني صلاحية الأصول التعليمية الإنتاجية |
| Playwright report | 65 screenshots | artifact `playwright-report` في Run 40219322373، يحوي admin-responsive وstudent-responsive وP05 ومشاهد V1؛ بعضها سيناريوهات E2E وليست جميع حالات V2 |
| Railway | نجاح آخر deployment | `himma-` API و`himma-web` وPostgres وRedis = SUCCESS عند فحص 2026-10-25؛ منصة trial وليست قبول إنتاج |
| Media / bank | SOURCE_CONFIRMED | 300 سؤالًا، 19 درسًا، 12 دعمًا، 30 قبلي +30 بعدي، 89 أصلًا؛ الأنواع النشطة 107 choose_one و52 listen_choose_one و57 sequence و18 build_word و4 choose_image و62 read_aloud و**0 write_text** |
| Dev devices | NOT_VERIFIED_IN_ARTIFACT | رسالة المالك «تم الاختبار» و«تم» تقبل القرار، لكنها لا تتضمن بروتوكول الجهاز الفعلي DEV-01..DEV-16 مع تسجيل النتيجة/لقطة/متصفح/نظام. تُستكمل قبل توقيع القبول الإنتاجي |

**حد الدليل:** صور Playwright مخصصة لسيناريوهات موجودة في الاختبارات، وليست مسحًا بصريًا بشريًا لكل صف V2. لم ننتج صورًا مصطنعة. لا يثبت screenshot نجاح السلوك الفعلي وحده.

## 2. جرد صفحات Next.js — 23 مسارًا

**عام (1):** `/` — الصفحة التعريفية.  
**طالب (7):** `/student/login`، `/student`، `/student/activity/[id]` (مسار V1 تاريخي)، `/student/session/[id]` (V1 تاريخي)، `/student/assessment-v2/[sessionId]`، `/student/learning-v2`، `/student/learning-v2/[sessionId]`.  
**إدارة (15):** `/admin/login`، `/admin`، `/admin/account`، `/admin/audio-review` (V1)، `/admin/content-preview`، `/admin/reports`، `/admin/settings`، `/admin/skill-reports`، `/admin/students`، `/admin/students/new`، `/admin/students/[id]`، `/admin/v2-assessments`، `/admin/v2-lesson-review`، `/admin/v2-media`، `/admin/v2-reviewed-recordings`.

العد يخص **ملفات page.tsx الحقيقية** ولا يشمل API routes ولا layouts أو حالات query. كل URL في الجدول يجب اختبار `loaded / empty / error / populated / unauthorized / narrow RTL` بحسب دوره، بما لا يقل عن الهاتف 320/360/390/430، التابلت 768، سطح المكتب 1280/1440، وZoom 200%.

## 3. سجل فجوات P09.0 المثبتة

| ID | الأهمية | السبب الجذري والدليل من المصدر | إجراء الإصلاح الجذري | مرحلة العلاج |
|---|---|---|---|---|
| P09-F01 | P0 | `student/page.tsx` يستدعي profile/activities/status/journey/rewards **V1** مع `v2/assessments/current-action`، ويعرض بطاقة V2 إضافية `TEST ONLY`، بدل مصدر قرار رحلة واحد | جعل CurrentAction V2 السلطة الوحيدة لبداية رحلة طالب V2، وحصر V1 في route توافق محدد | P09.1 ثم P09.4 |
| P09-F02 | P0 | `admin/content-preview/page.tsx` يقرأ `researcher/content-preview` ويدور على نوع محتوى V1، لا متصفح 300 سؤال V2 مرتّب | read-only V2 content browser متسلسل مثبت بالإصدار؛ لا إنشاء CMS تعديل | P09.2 |
| P09-F03 | P1 | `admin/v2-media/page.tsx` جدول بيانات للأصول بلا تشغيل صوت/فيديو/صورة في نفس الصفحة، وعلى الهاتف جدول بعرض أدنى 680px | متصفح وسائط read-only بتشغيل/معاينة فعلي، responsive cards وإفصاح TEST_ONLY | P09.2 |
| P09-F04 | P0 | `admin/students/page.tsx` يستخرج `core_completed_items/core_total_items` ويعرض تقدم V1، رغم أن رحلة V2 تتكون من 19 درسًا | Student360 وطلاب V2 من نموذج قراءة موحّد، مع إظهار التاريخ القديم صراحة | P09.1 / P09.3 |
| P09-F05 | P1 أمن/خصوصية | قائمة الطلاب تعرض `access_code` نصًا صريحًا على Desktop/Mobile وتسمح البحث به؛ رغم قصر الوصول على المشرف يبقى كشفًا واسع النطاق غير ضروري | إخفاء افتراضي ورؤية مقيّدة عند الحاجة، وضبط الوصول والتدقيق | P09.1 / P09.3 |
| P09-F06 | P1 | `admin/page.tsx` و`admin/reports/page.tsx` و`skill-reports/page.tsx` تستخدم مصادر V1 researcher/summary ومقاييس محاولات قديمة ولا يوجد عقد جمع رسمي شامل لدروس V2 | تعريف عقود read-model وتقارير رسمية منفصلة من SkillEvidence/AssessmentQuestionResponse/Journey V2 | P09.1 / P09.3 |
| P09-F07 | P1 | صفحات `v2-assessments` و`v2-lesson-review` و`v2-reviewed-recordings` و`audio-review` ما زالت موزعة دون مركز واضح للانتظار والمنجز والتاريخ | توحيد navigation وstatus/read-model مع الإبقاء على compatibility والحقوق الآمنة | P09.3 |
| P09-F08 | P1 | `student/page.tsx` يحسب النجوم من `/api/rewards` القديمة؛ لم يثبت V2 ledger مستقل يمنح نجومًا حسب الدرس/القبلي/الإنجاز | اعتماد وتنفيذ سجل أحداث rewards محصن ضد التكرار وفق قرار المالك؛ لا استخدام fake stars | P09.5 |
| P09-F09 | P1 | `student/learning-v2/page.tsx` تعرض رسائل تقنية وعبارات `TEST ONLY` وتضع مستويات في مسار منفصل عن لوحة الطالب الأساسية | رحلة طالب واحدة مناسبة للعمر، مع وضع TEST_ONLY في banner تشغيلي واضح لا يختلط بالمهمة | P09.4 / P09.5 |
| P09-F10 | P0 قبول | لقطات M04 الـ15 تختبر صفحات دخول عامة فقط؛ Playwright 65 صورة لا تتضمن كل شاشات `v2-reviewed-recordings` و`v2-media` و`v2-assessments` وحالاتها | توسيع مصفوفة Screenshot/E2E لصفحات V2 المُصادَق عليها وحالاتها، واعتماد تقييم بشري للصور | P09.0 ثم P09.6 |
| P09-F11 | P1 وثائق | بعض الجداول التاريخية في `22` و`09` تصف `write_text=21` وسبعة أنواع متاحة؛ ذلك منسوخ قبل قرار تركيب الحروف | اعتماد تعريف الأنواع الستة النشطة مع إبقاء التوافق التقني `write_text` للإصدارات المجمدة فقط | P09.0 |
| P09-F12 | P0 إطلاق، ليست عطل P09.0 | الصوت الحقيقي على Safari/Chrome وS3 backup/versioning وحذف نسخ القصر القانونية لم تُوثق جميعها بدليل جهاز مستقل | إبقاء gate صريحًا ولا تعطيل تغطية CI أو ادعاء اعتماد ASR | P09.6 / P10 |

## 4. مصفوفة الصور — مراجع صريحة

- `m04-responsive-screenshots`: 15/15 موجودة، لكنها فقط **landing + two logins**. المعايير المطلوبة لأسطح الإدارة والطالب لم تتحقق عبر هذا الأثر.
- `playwright-report/screenshots/student-responsive`: home/assessment للهاتف 320 و360 و390 و430، تابلت/ديسكتوب؛ تُعد لقطات E2E فعلية لبعض الحالات، وليست دليل صف الطالب V2 الموحد أو جميع مراحل 19 درسًا.
- `playwright-report/screenshots/admin-responsive`: dashboard/students/students-new/content-preview/content-preview-detail/audio-review/reports/skill-reports/settings على 390 و768؛ مقارنات مرئية فعلية لواجهات قائمة.
- `playwright-report/screenshots/p05`: catalog/mobile video error/resume وguided-practice/targeted-support؛ تحقق تجربة P05 الجزئية فقط.
- **غير مغطى بملف لقطة معرّف يثبت الصفحة والحالة بشكل مباشر:** أرشيف التسجيلات V2 الجديد، متصفح وسائط V2، تقييمات V2، مراجعة دروس V2، Student360 الموحّد، مسار النقاط بعد اعتماده، معظم حالات فشل/انتظار/دعم على جميع المقاسات؛ العلامة `NOT_SHOT` حتى تضاف.
- كل صور Playwright مصدرها [CI 40219322373](https://github.com/7eaur/himma-/actions/runs/40219322373)، لا مصدر محلي مفترض. وينبغي حفظ مراجع artifacts/لقطات جديدة لكل HEAD مهم.

## 5. عقد/أولوية أول تحسين بعد هذا الجرد (P09.1)

1. **وحدانية المصدر:** لا ربط مسار طالب V2 ببيانات V1 للتقدم والمكافآت؛ إبقاء التوافق لحسابات V1 عند الاحتياج دون فقدان تاريخها.
2. **نموذج واجهات القراءة فقط:** typed DTO لرحلة V2/تقدم الطالب/محتوى البنك/حالة الوسائط/التقييمات، مصدره جلسات ومحتوى مثبتا بالإصدار؛ ليس تجميعًا من React endpoints متعارضة.
3. **الأمان:** least privilege لرموز دخول الأطفال وسجلات الصوت/النتائج، عدم إعادة private_answer أو Storage Key إلى واجهات غير مخولة، idempotent grant عند الأحداث.
4. **التصحيح/الاختبارات:** لكل DTO اختبار صلاحية وتفويض وcount وإصدار وجلسة قديمة، ثم E2E مبدئي قبل إصلاح الصفحات.
5. **حد المراحل:** لا تنفيذ P09.2 أو P09.3 أو P09.4 في مرحلة baseline فقط. لا تعديل DB من غير نموذج مراجَع واختبار ترحيل؛ لا نشر إنتاجي.

## 6. حالة القبول الفعلية

- **P08:** `owner_accepted` بعبارة «تم»، مع الحفاظ على فجوات ضمان الجهاز الحقيقي والاحتفاظ النهائي إلى ما قبل P10؛ نجاح CI على SHA أعلاه مثبت.
- **P09.0:** `source_inventory_and_existing_artifacts_verified`، **`visual_completeness_pending`** للأماكن المحددة P09-F10. القائمة هنا ليست تصريحًا بإغلاق P09.0 قبل تكملة تغطية Screenshots/States.
- **P09.1–P09.6:** `not_started` لهذه الجولة.
- **P10:** `blocked_until_P09_functional_gate_and_approved_media`.

**التسليم التالي:** إغلاق فجوات تغطية Screenshots/V2 QA في P09.0 وتثبيت مواصفات source-of-truth قبل تنفيذ P09.1. بعد إقرار المالك للمرحلة («تم») يبدأ بناء read models في P09.1، وليس دمج/نشر الإنتاج.


## 7. تحديث التغطية القابل للتنفيذ في P09.0 — 2026-10-25

**الأعمال المسجلة بعد الجرد:** الاختبار `apps/web/tests/e2e/admin-responsive.spec.ts` توسع إلى 13 صفحة إدارة ومنها `/admin/v2-assessments` و`/admin/v2-lesson-review` و`/admin/v2-media` و`/admin/v2-reviewed-recordings` و`/admin/account`، على هاتف 390 وتابلت 768، و7 صفحات أساسية على سطح مكتب 1440. **الملف الجديد** `apps/web/tests/e2e/v2-assessment-visual-baseline.spec.ts` يغطي أربع حالات حقيقية للمكون (answering/waiting_review/placement_pending_review/completed) باستخدام API fixture مصرح به في Playwright على خمسة عروض 360/390/430/768/1440: 20 صورة مشروطة بنجاح E2E. وُسّع `v2-lesson-runtime.spec.ts` لتوثيق كتالوج الدروس على 360/390/430/768/1440، والتقوية الموجهة على 360/390/768/1440 مع التحقق من overflow.

**أمان الإثبات:** fixture هنا هو بيانات استجابة واجهة صريحة، فلا يُستعمل برهانًا على مخرجات scoring الفعلية أو مراجعة صوت حقيقية. أما اختبارات الخلفية المستقلة من CI فقد كانت ناجحة قبل الإضافات، ولا يحل الاختبار المرئي محلها. الاختبارات لا تستخدم تسجيلات طفل حقيقي في المستودع أو الصور.

**حالة workflow على Commit الكود `3d482665f8e57ce5662c2dff6fb42d2f4ed20e26` عند التوثيق:** [M04](https://github.com/7eaur/himma-/actions/runs/40223049691) PASS؛ [CI](https://github.com/7eaur/himma-/actions/runs/40223049722) و[M09](https://github.com/7eaur/himma-/actions/runs/40223049686) قيد التنفيذ. **لا يُكتب PASS لـE2E قبل اكتمال هذا التشغيل**. بعد النجاح يتعين تحميل artifact الجديد، عد الصور الفعلية، فحصها بصريًا، ثم تغيير الحالة من `PENDING` إلى `PASS` في تسليم لاحق.

## 8. ملاحظات التدقيق البصري من الصور الحقيقية قبل توسيع الاختبارات

تم فتح صور هاتف 390px من Artifact `playwright-report` في [CI 40219322373](https://github.com/7eaur/himma-/actions/runs/40219322373)، دون الاعتماد على مسارات UI متخيلة:

| ID | الدليل المرئي/المصدر | النتيجة والحل |
|---|---|---|
| P09-F13 | `admin-responsive/phone-390x844-content-preview.png` | شريط تنقل السابق/التالي الثابت يظهر متراكبًا على مساحة جزء من التفاصيل أثناء العرض؛ يلزم فحص سلوك التمرير وsafe bottom padding في P09.2 ولقطة ثانية بعد scroll؛ **ملاحظة مرئية تتطلب إعادة فحص تفاعلي لتقرير إن كان يحجب خيارًا**، لا ادعاء bug نهائي دون تحققه |
| P09-F14 | `p05/mobile-390-catalog.png` + `student/learning-v2/page.tsx` | الكتالوج يعرض «سبعة أنواع تفاعل» واسم «أبني وأكتب كلمة بسيطة» من الوصف القديم؛ بنك V2 المعتمد الآن **ستة أنواع نشطة** بعد إلغاء الكتابة الحرة، والصيغة يجب أن تعكس **تركيب كلمة** لا التعبير الحر. يُعالج ضمن توحيد نصوص الطالب في P09.4/5 |
| P09-F05-visual | `admin-responsive/phone-390x844-students.png` | تبين ظهور رمز دخول الطالب كاملًا حتى في بطاقة الهاتف، وتقدم 0/10 للأنشطة القديمة، فتأكدت مشكلتا أمن العرض/تضارب V1-V2 في P09-F04/F05 |
| P09-F09-visual | `p05/mobile-390-catalog.png` | بطاقات المستويات تأخذ طولًا ملحوظًا مع نصوص تقنية `TEST ONLY`، والمستوى الثاني والثالث مقفلان. يُحتفظ بتمييز الاختبار حتى P10، لكن تُراجع الصياغة والتسلسل والارتفاع في P09.4/5 |

**بوابة المرحلة:** لا توجد حتى الآن مصفوفة صور `ALL_23_ROUTES × REQUIRED_STATES × DEVICE_WIDTHS` مكتملة باعتماد بصري؛ التوسعة الحالية تغطي مسارات إضافية ولا تُغني عن إكمال بيانات Student360 وحالات التقارير والمحتوى والأخطاء. السبب الجذري للفجوات P09-F01..F14 يمر إلى التنفيذ المخصص P09.1–P09.5 دون تقديمه على أنه أُصلح في مرحلة الجرد. يحتفظ الملف 56 بأرقام مرحلية ولا يُعد قرار نشر.


## 9. تحقق QA الفعلي بعد إصلاح بوابة Playwright — 2026-10-25

**أُنجز فحص أدلة فعلي، لا توقع صور:** جميع البوابات [CI](https://github.com/7eaur/himma-/actions/runs/40224693263) و[M04](https://github.com/7eaur/himma-/actions/runs/40224693255) و[M09](https://github.com/7eaur/himma-/actions/runs/40224693288) ناجحة على Commit واحد `cfae9188f981571e063d054e06b53ddc3e1d5ac2`. تم تنزيل Artifact `12611122739` وفهرسة **109 ملفات PNG** بالفعل، منها **20** لقطة P09.0 للاختبار القبلي بأربع حالات وخمسة مقاسات، مع فتح عينات من صورها ومراجعة ظهور الحروف وبطاقات انتظار المشرف والتسكين والإكمال بصريًا.

**المتبقي من فجوات الصور:** لقطة أرشيف الصوت السابقة تغطي الحالة الفارغة فقط؛ بعد ذلك نُفذ اختبار `v2-reviewed-recordings-visual-baseline.spec.ts` لتغطية 12 لقطة متوقعة على 4 مقاسات وحالات empty/reviewed/error، وأضيف إلى CI/M09 في Commit `19dedd1481946169934b689701751b009d640458`. نتائجها لا تعد نجاحًا إلا عند اجتياز Actions وفحص الملفات. يؤكد الفحص أيضًا أن صفحة وسائط V2 بالهاتف قائمة طويلة لـ89 أصلًا، فتُعالج ضمن P09.2 لا بواسطة التصوير وحده.

**السجل الموحد الجديد:** [57_P09_0_VERIFIED_VISUAL_QA_EVIDENCE_AR.md](57_P09_0_VERIFIED_VISUAL_QA_EVIDENCE_AR.md) هو بيان الصورة الفعلية والمصفوفة والبوابات وحدود النتيجة ويصحح توصيف `NOT_SHOT` السابق لبعض مسارات V2؛ البنود القديمة في الأعلى كانت حالة ما قبل توسعة الاختبارات. **P09.0 لا يزال مفتوحًا** إلى أن تغلق الصور الناقصة والحالات والمراجعة البصرية المفصلة. لا بدء تلقائي لـP09.1.
