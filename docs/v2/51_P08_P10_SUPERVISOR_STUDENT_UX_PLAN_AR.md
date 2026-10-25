# هِمّة V2 — خطة مراجعة لوحة المشرف ورحلة الطالب والمحتوى والوسائط والمكافآت

**الوثيقة:** 51 | **تاريخ فحص المصدر:** 2026-10-25 | **النوع:** ANALYSIS_AND_PLANNING_ONLY  
**الفرع:** v2/01-learning-foundation-20261007 | **HEAD محل الفحص:** f8d5b6b81a0f47698afdfd7e4c2721e38793495c  
**الحالة:** اقتراح هندسي موثق للمراجعة والاعتماد، لا تنفيذ، لا ترقية مرحلة، لا دمج، لا نشر.  
**مراجع:** 09_IMPLEMENTATION_ROADMAP_AR، 22_FULL_SYSTEM_COVERAGE_AND_ACCEPTANCE_MATRIX_AR، 25_V1_TO_V2_FEATURE_PARITY_REGISTER_AR، 30_P01C_STUDENT_DASHBOARD_AND_JOURNEY_AUDIT_AR، 33_P01F_ADMIN_AND_SUPERVISOR_AUDIT_AR، 39_P06_ASSESSMENT_PLACEMENT_SUPERVISOR_REPORTING_DELIVERY_AR، 45_P07_MEDIA_READINESS_AND_BINDING_CONTRACT_AR، 46–50 الخاصة بـP08.

## 0. القرار وحد الإثبات

1. لم تُعدل في هذه الجولة صفحات React أو API أو قواعد البيانات أو بيانات الطلاب أو المتغيرات أو الاستضافة. هذه وثيقة تحليل وتخطيط فقط، وتُدمج في خارطة P08–P10، لا تُنشئ منصة ثانية أو مرحلة إطلاق جديدة.
2. جرت مراجعة شجرة المسارات وملفات الصفحات والخدمات والعقود والأبحاث السابقة على GitHub. فحوص CI/M04/M09 على SHA المذكور ناجحة؛ Railway Web/API/Postgres/Redis حالتها SUCCESS. **نجاح البناء لا يثبت بصريًا أو وظيفيًا كل صفحة.**
3. لا توجد جلسة مشرف مخوّلة في هذا الفحص لإجراء نقرات، تعبئة، معاينة محتوى حي داخل لوحة المحمية، أو التقاط لقطات جديدة من الهاتف/الديسكتوب. جميع أحكام التصميم المرئي والتحقق من ربط بيانات الواجهات الفعلية تُوسم NEEDS_LIVE_UI_QA، لا PASS.
4. لا نزيل وظائف V1 النافعة قبل تسجيل التكافؤ والمسارات البديلة واختبارات الرجوع؛ واجهات V1 الطلابية لا ينبغي أن تظل وجهة افتراضية عند اعتماد V2. توافق بيانات V1 القديمة مستقل عن الهوية والأصول التعليمية التي ينبغي حفظ النافع منها.
5. تعريف حالة كل بند: CONFIRMED_SOURCE = ثبت من قراءة الكود؛ HISTORICAL_AUDIT = تقرير سابق يحتاج إعادة تحقق؛ PROPOSED = إضافة/تصميم مطلوب؛ NEEDS_LIVE_UI_QA = غير مثبت من شاشة حية.

## 1. أهم الفجوات المؤكدة من المصدر

| ID | الأولوية | الملاحظة | الدليل الحالي | نوع الإثبات |
|---|---|---|---|---|
| F-01 | P0 | لوحة الطالب تجمع رحلة V1 مع بطاقة V2 مستقلة، وتعرض عبارة رحلة V2 المرشحة وTEST ONLY | apps/web/src/app/student/page.tsx (profile/journey/rewards + v2 current-action)، apps/web/src/app/student/v2-preview-card.css | CONFIRMED_SOURCE |
| F-02 | P0 | صفحة محتوى المشرف مبنية على pretest/posttest/core_activity/reinforcement_activity وإحضار researcher/content-preview؛ ليست فهرس بنك V2 المتسلسل 300 بندًا مثبتًا بإصدار | apps/web/src/app/admin/(dashboard)/content-preview/page.tsx | CONFIRMED_SOURCE |
| F-03 | P1 | شاشة v2-media سجل حالة 89 أصلًا وتبعياتها دون مكونات فعلية لمشاهدة الصورة/الفيديو أو سماع الصوت | apps/web/src/app/admin/(dashboard)/v2-media/page.tsx | CONFIRMED_SOURCE |
| F-04 | P0 | توجد ثلاث وجهات مراجعة موزعة: audio-review لـV1 وv2-lesson-review وv2-assessments؛ التنقل نفسه يسمي V1 | apps/web/src/app/admin/(dashboard)/layout.tsx | CONFIRMED_SOURCE |
| F-05 | P0 | لوحة/قائمة الطلاب تعرض مؤشرات core_* وaccess_code ومعلومات قديمة في قائمة عامة؛ يجب تصميم Projection V2 وقصر كشف الأكواد | admin/(dashboard)/page.tsx، students/page.tsx، services/api/admin_student_projection.py | CONFIRMED_SOURCE |
| F-06 | P1 | ملف الطالب يملك 7 تبويبات لكنه يعتمد researcher/students/{id}/journey,rewards,adaptation ويحوّل التسجيل إلى audio-review التاريخي؛ لا يثبت اكتمال رحلة V2 في كل تبويب | admin/(dashboard)/students/[id]/page.tsx | CONFIRMED_SOURCE |
| F-07 | P1 | منح النجوم والشارات الحالي في adaptation.py مرتبط بمحاولات core القديمة، بينما كتالوج reward_catalog.py يحوي 1–3 نجوم وشارات 3 مستويات. لا توجد في v2_adaptation_runtime.py سياسة منح مماثلة مثبتة | services/api/adaptation.py، reward_catalog.py، v2_adaptation_runtime.py | CONFIRMED_SOURCE |
| F-08 | P1 | شخصية girl في واجهة V2 هي صورة ثابتة؛ توجد خمسة أوضاع رسومية للفتاة (welcome/explain/encourage/try-again/success)، وملفات boy أيضًا، مع أصوات UI بسيطة؛ لا نظام انتقالات سردية متعدد الحالات مثبت | public/characters، apps/web/src/components/StudentExperienceEffects.tsx، student/learning-v2 | CONFIRMED_SOURCE |
| F-09 | P1 | عبارات فنية ظاهرة للطالب: معاينة رحلة التعلم V2، TEST ONLY، والمراحل/IDs الفنية على بعض الشاشات | student/learning-v2/page.tsx، student/learning-v2/[sessionId]/page.tsx، student/page.tsx | CONFIRMED_SOURCE |
| F-10 | P1 | صفحة assessment-v2 تحمل رابطًا إلى /student/dashboard؛ لا يوجد هذا المسار كدليل صفحات مستقل في src/app/student عند الفحص. يحتاج تحقق من أي redirect/middleware ثم تصحيح المسار القانوني | student/assessment-v2/[sessionId]/page.tsx وشجرة student | CONFIRMED_SOURCE للرابط وعدم وجود ملف المسار، NEEDS_LIVE_UI_QA لسلوك التوجيه |
| F-11 | P0 | Sidebar يوحّد هوية الباحث researcher وصفحات V2 وV1 في قائمة واحدة؛ لا تمييز frontend بين مدير النظام ومراجع تعليمي ومُصدّر تقارير | admin/(dashboard)/layout.tsx، settings/page.tsx | CONFIRMED_SOURCE |
| F-12 | P1 | التقارير الحالية researcher/reports وresearcher/reports/skills وليست عرضًا إداريًا شاملًا لحالات V2/المراجعة/الدعم والإصدار، بينما توجد summary منفصلة للتقييمات V2 | admin/(dashboard)/reports/page.tsx، skill-reports/page.tsx، v2-assessments/page.tsx | CONFIRMED_SOURCE |
| F-13 | P2 | تصميم الإدارة يمتلك shell مشترك وبطاقات Mobile وتبويبات؛ لكن التشابه بين الصفحات وقابلية قراءة الجداول على هاتف صغير لم يُفحص بصريًا حيًا | dashboard-layout.module.css، AdminUI، CSS لكل صفحة | NEEDS_LIVE_UI_QA |
| F-14 | P0 | انتهاء التسجيل/المراجعة في P08 لا يعني جاهزية live monitoring أو AI scoring؛ Human-First قائم وقرار الاحتفاظ/التصدير وأجهزة فعلية غير مكتمل | docs/v2/47 و48 و50 | CONFIRMED_SOURCE |
| F-15 | P1 | سجل المحتوى في V1 يعرض content approved من أكثر من سياق حسب تقرير 33؛ يجب revalidate release pin لا البناء على حالة approved فقط | content_preview.py + تقرير 33 AF06/AF07 | HISTORICAL_AUDIT يحتاج اختبارات V2 مستقلة |

## 2. صفحة صفحة — لوحة المشرف (الوظيفة المطلوبة، لا الشكل فقط)

| الصفحة الحالية | الحالة/القيمة الحالية | العمل المخطط | تحقق القبول |
|---|---|---|---|
| /admin | ملخص طلاب ومراجعة صوت ونتائج على عقود قديمة | V2 SupervisorOverview من مصدر واحد، إحصاءات: درس حالي، مراجعات كتابة/قراءة، دعم، تسكين، قبلي/بعدي، نواقص وسائط، إنذار فشل مصدر مستقل | reconciliation مع API/DB، فارغة/بطء/500، هاتف وRTL |
| /admin/students | قائمة وبحث بالاسم أو access_code محلي وعرض الكود في الجدول | بحث/ترقيم خادمي مع فلترة ومجموعات وحالة CurrentAction، أقل بيانات لازمة، masked code بإجراء موثق | آلاف الطلاب، no secrets by default، بطاقات هاتف |
| /admin/students/new | إنشاء طالب برمز حقيقي | إبقاء الإنشاء الموثق؛ تحقق الأخطاء والنماذج والوصول والظهور المقيد للكود | create/duplicate/capacity/429/422 وFocus |
| /admin/students/[id] | 7 تبويبات (عام، رحلة، اختبارات، تسجيلات، تكيف، حساب، سجل) | Student360 V2: 19 درسًا، supports، rubrics، official attempts، مراجعات/نسخ، مكافآت V2 وسجل Audit؛ tab deep-link | حالات طالب جديد/منتظر/مكتمل، partial failure، هاتف |
| /admin/audio-review | طابور تسجيلات V1 | إما سجل تاريخي مؤرشف داخل المراجعات الموحدة أو إتاحة توافق وفق سياسة بيانات V1؛ لا باب تعليمي مزدوج | عدم ضياع سجل قديم وعدم وجود عملين متضاربين |
| /admin/v2-lesson-review | مراجعة بشرية وطلب إعادة لدرس V2 | مصدر Queue موحد مع عوامل تصفية وطلب مراجعة وأسباب ونسخة صوت/كتابة والسجل والحجز | claim collision, idempotency, privacy, replay |
| /admin/v2-assessments | طابور قراءة/كتابة والتسكين وsummary | دمجه منطقيًا بمركز المراجعة للتقييم، مع صفحة فرعية للتسكين والتقرير لا تكرر القرار | 30/30، pending/placement، academic signoff |
| /admin/content-preview | معاينة V1 readonly قابلة للبحث | تصبح واجهة بنك V2 read-only وفق 3+19+12+2 سياقات فعلية دون اختلاق معتمد، أو تستبدل بصفحة موحدة /admin/content مع تحويل آمن | 300 سؤال، active release، الخيارات والrubrics |
| /admin/v2-media | inventory read-only؛ لا player/gallery | Media Browser read-only مع grid/list + Preview/Audio/Video، وربط استخداماتها وسياقها، مع الحالات والـversion | جميع الأصول، 403/404/codec/seek/mobile |
| /admin/reports | PDF/XLSX والتقدم والنتائج البحثية | Report V2 من official attempts فقط، progress/missingness/release/skills/support/review؛ الاحتفاظ بالتصدير الآمن | تطابق summary/export وCSV/Excel injection guard |
| /admin/skill-reports | ملخص وصفى لدرجات المهارات | فصل تدريب/تحقق/دعم/قبلي/بعدي والنسخ المعادة في التقرير مع مقامات واضحة | نوع evidence لا يختلط؛ no fake mastery |
| /admin/settings | الحساب والأمان والمشرفون، غالبًا دور researcher واحد | RBAC وحياة الحسابات وسجل نشاط وصلاحيات محفوظة من API، وUX للمدير فقط | least privilege، آخر مدير، reset/revoke/audit |
| /admin/account | تحويل توافق قديم | إبقاء تحويل صامت إلى settings دون صفحتين متنافستين | Redirect/Back/No loop |
| /admin/login | دخول مشرف مستقل | فحص التصميم/الأخطاء/التوافر والتجاوب وعدم كشف حالة المستخدمين | 401/429/keyboard/mobile |
| الإشعارات في Admin Shell | إشعارات وتنقل responsive | Recipient-scoped Inbox وسياق review الصحيح، اختبارات القراءة لكل مشرف والتنقل | A/B notification isolation؛ no dead links |

**إضافات واجهات مطلوبة بشرط عدم التكرار:** مركز مراجعات موحد؛ «متصفح بنك المحتوى» و«مكتبة الوسائط» للعرض فقط؛ سجل تدقيق وصلاحيات مناسب للإدارة؛ واجهة متابعة المكافآت ضمن Student360 لا Dashboard مكررة. لا تُنشأ شاشة جديدة إذا يمكن تحويل صفحة موجودة مع مسارات توافق.

## 3. مواصفة متصفح بنك المحتوى المعتمد — read-only

### المصادر والملكية
- القراءة من canonical content release/manifests/compiled questions، لا من حقل approved وحده؛ إظهار الإصدار المختار وفرق حالة Approved vs Published vs Pending، ومنع mixing بين نسختين.
- التنظيم التسلسلي الفعلي: **القبلي (30) ← المستوى 1 (6 دروس + دعمها) ← المستوى 2 (6 دروس + دعمها) ← المستوى 3 (7 دروس + دعمها) ← البعدي (30)**؛ إجمالي 19 درسًا و12 دعمًا و300 سؤالًا من البنك، وليس 300 درس.
- للحفاظ على صحة ترتيب بنك المحتوى، تُحدد أرقام ترتيب الدروس والأسئلة والدعم من العقد المعتمد؛ لا تُفرز حروف الـIDs نصيًا إذا يكسر ذلك ترتيب المرحلة.

### الجدول الرئيسي
حقول: ترتيب، القسم/المستوى، الدرس/الدعم، مرحلة المحتوى (تمهيد/فيديو/تدريب/تحقق/دعم/اختبار)، معرف البند، نوع السؤال، نص السؤال المختصر، عدد الخيارات، الوسائط المرتبطة، حالة الاعتماد/الإصدار، تنبيه فجوة. بحث/فلاتر حسب المهارة/النوع/المرحلة/الحالة، وتقسيم صفحات، وتصفح هاتف ببطاقات بدل جدول قابل للتمرير بلا نهاية.

### تفاصيل البند
فتح القراءة فقط: هدف الدرس، نص التمهيد، التعليمات، السؤال، الصورة/الصوت/الفيديو، كل الخيارات مع الترتيب، الإجابة الصحيحة والمعيار **للمشرف المصرح فقط**، التلميح المسموح في التدريب فقط، علامات حاجة مراجعة، مصدر الإصدار وasset IDs. معاينة «كما يراها الطالب» من نفس renderer وعقد Student DTO من دون أي rubric/answer، ومعاينة «للمختص» منفصلة بخادم ذي صلاحية. لا زر نشر/تحرير في هذه الشاشة.

### قبول CNT-01..CNT-09
التسلسل الصحيح، عدد 300/300 دون ازدواج أو نقص، 19 درسًا و12 دعمًا و30+30، أنواع الأسئلة السبعة، لا اختلاط إصدارات، لا كشف خاص للطالب، فلاتر+إفراغ+تحميل+أخطاء، تفاصيل الهاتف، توافق نفس renderer مع الطالب، مراجعة لغوية لكل نسخة منشورة.

## 4. مكتبة وسائط للمعاينة فقط

- تطوير الصفحة الحالية بدل إنشاء نظام تخزين موازٍ: نوع الوسيط (صورة/صوت/فيديو)، اسم/معرف مناسب، thumbnail، حالة ready/pending/missing/rejected/test-only، عدد الاستخدامات والدرس/السؤال، release والمصدر.
- العرض: معرض صور بعارض يمكن تكبيره؛ audio player مع تشغيل/إيقاف/مدة وإمكان Seek؛ video player مع poster وتحكم؛ معاينة حالة الملف المفقود ببديل مفهوم للمشرف، دون عرض placeholder للطالب عند الإنتاج.
- فلاتر/بحث حسب النوع/المستوى/الدرس/الجاهزية/مرشح أم نهائي، وإظهار dependency وpreview conformance، وفصل معلومات المسار التقني داخل «تفاصيل متقدمة للمسؤول» عن النسخة البصرية.
- وضع المعاينة read-only؛ **لا رفع، تحرير، حذف، ربط، اعتماد أو نشر** في هذه الصفحة. عمل import/bind/approval إن لزم يكون خارج شاشة التصفح وفق P07/P10 والعقد الأصلي.
- كل ملفات الطلاب المسجلة ليست ضمن «المكتبة التعليمية»؛ تسجيلات الطلاب تحت Review Evidence private path وصلاحيات مختلفة.

### قبول MED-01..MED-08
89 أصلًا في الجرد (بحسب العقد الحالي)، بحث/تصفية فعالة، صور واضحة، أصوات مسموعة، فيديوهات قابلة للمشاهدة عند توفر asset، حماية endpoints وعدم كشف private URLs، حالة missing صحيحة، نموذج هاتف/Zoom200%، مطابقة metadata وuse refs وعدم خلط candidate مع approved.

## 5. مركز مراجعة القراءة والكتابة والتسجيلات

**الهدف:** صفحة عمل واحدة للمشرف للحالات المعلقة؛ تبويبات أو فلاتر «الكل / دروس / قبلي-بعدي / إعادة / سجل القرارات» لا ثلاث طوابير في التنقل.

- حالة واحدة Authoritative: pending_review → claimed → decision / rerecord_requested → rerecord_submitted → decision؛ الأصل والبديل والمراجعة محفوظة؛ أسباب ودليل ونص مطلوب وrubric خاص للمشرف.
- Near-real-time queue: استقبال حدث وصول دليل/تحديث دوري مناسب ولوحة عداد مع dedupe، لا بث مفتوح للميكروفون. تسمية «مراجعة مباشرة بعد وصول التسجيل» أدق من «مراقبة حية» ما لم يعتمد منتج بث متزامن وصلاحياته.
- أي طلب «الاستماع الحي أثناء تسجيل الطالب» خيار مختلف يتطلب دراسة موافقة الطفل/ولي الأمر، أمان الاتصال، أداء الشبكة، وإدارة صلاحياته؛ ليس وظيفة قائمة ولا يُفعّل افتراضيًا.
- AI/ASR: مساعد اختياري لاحقًا يُقترح له sandbox benchmark بموافقة مناسبة وأصوات مرخصة/اصطناعية دون إرسال تسجيلات أطفال فعلية أو منح درجات آلية؛ لا يستبدل Human-First ولا يعتمد correct/incorrect دون توقيع تربوي منفصل.
- حالات الحجز المتزامن، توقف المشرف، offline، resend، seek/range، خصوصية الحسابات، والمدة/التصدير مرتبطة ببوابة P08؛ لا يوجد زر «اعتمد» بلا evidence صالح.

### قبول REV-01..REV-10
قائمة موحدة دون ازدواج، مرشحات pagination، وصول حديث، claim/expiry, replay original/retry، rubric فصل الطالب/المشرف، القرار بعد سماع الدليل، عدم كشف ملف من طالب آخر، لا fake grades/AI، سجل تدقيق قابل للمراجعة، UI هاتف.

## 6. توحيد رحلة الطالب وإيقاف ظهور القديم

### المعمارية المستهدفة
- واجهة دخول الطالب /student/login ثابتة. /student يصبح V2 StudentHome مع CurrentAction **صاحب قرار وحيد من الخادم**؛ لا جمع متزامن لـV1 Journey + Core + V2 current action لعرض أزرار متعارضة.
- مسار الطالب: Login → pretest → placement → lesson map → intro → video → guided practice → independent check → support/review if needed → next lesson/level → posttest → completion.
- تبقى المسارات القديمة /student/activity/[id] و/student/session/[id] للتوافق مع الحالات المسموح بها فقط؛ عند الانتقال المعتمد لا تُعرض كخيارات عادية ولا يحذف تاريخها؛ تُختبر سياسة redirect/legacy-session.
- الخريطة: 3 مستويات، 19 درسًا، درس حالي واحد CTA، locked/done/ready/support/waiting، مراحل داخل الدرس، تقدم مبني على حالة الخادم؛ لا نسبة أو نتيجة مختلقة من metadata.
- تقليل بطاقات Dashboard إلى: ترحيب/شخصية، «مهمتك الآن»، تقدم المسار، مكافآتي، تنبيه طلب إعادة/انتظار؛ نتائج الاختبار عند اعتمادها؛ لا تكديس معلومات مشرف أو V1.
- إزالة TEST ONLY، معاينة، release ID، session ID، labels التقنية، notices التجريبية من واجهات الطالب فور اعتماد الجاهزية الوظيفية؛ قبلها تبقى بيئة trial معلّمة إداريًا وبشكل يمنع التباسها كنظام صالح للإطلاق.
- اختبار رابط /student/dashboard واستبداله بوجهة حقيقية موحدة إذا ثبت غياب route أو redirect صالح.

### قبول STU-01..STU-12
10 حالات رحلة مختلفة، عمل مسار 19 درسًا، عدم ظهور V1 لطلاب V2، حالة neutral pending، استئناف بعد reload/offline, دعم دون هبوط، عدم تسرب مرجع الإجابة، RTL/phone/Zoom، تفريغ errors، مزامنة reward، سهولة الطفل.

## 7. النجوم والشارات — سياسة توزيع مقترحة غير معتمدة

**الوضع الحالي:** الكتالوج يحدد نجمة/نجمتين/ثلاثًا وشارات مستكشف الحروف/بطل الكلمات/نجم الفهم؛ منح النجوم الحالي مرتبط بمحاولات V1. يجب تحديد إصدار V2 مستقل من القواعد قبل ترحيل rewards، مع إبقاء التاريخ كما هو.

**مقترح أولي يحتاج تحكيمًا تربويًا واعتمادًا** (ليس تنفيذًا):
1. نجمة واحدة لإكمال التدريب الموجّه في درس V2 وإرسال خطواته بصورة سليمة، بغض النظر عن عدد الأخطاء.
2. نجمة ثانية لاستكمال تحقق الدرس بعد حسم الأدلة البشرية المعلقة، لا لمنح درجة تلقائية على ملف صوت.
3. نجمة ثالثة عند تثبيت إكمال الدرس وتقدم المسار؛ مجموع حد أقصى 3 نجوم لكل درس. إعادة الضغط/التحديث/المحاولات لا تضيف نجمة لنفس الحدث؛ أحداث الدعم مساندة وليست عقوبة أو خصمًا.
4. شارة واحدة بعد إتمام متطلبات المستوى الفعلي بشكل معتمد (L1/L2/L3)، مع مراجعة خاصة لحالة التسكين الذي يتجاوز مستوى؛ لا تُعطى شارة إكمال بمجرد تخطي قبلي.
5. لا مكافأة على السرعة أو الدرجات النسبية أو القفز على الفيديو أو كثرة إعادة المحاولة. لا لوحات مقارنة بين الأطفال ولا عقوبة على التعثر/التقوية؛ الرسالة تركز على التقدم والجهد.
6. RewardsLedger (student, event-type, lesson/level, version) مع unique event key وAudit والمصالحة: استرجاع لا تكرار؛ مؤشر نجوم Dashboard والإشعارات يتبع ledger ذاته؛ V1 history مميز بشكل صريح لا يُترجم إلى دروس V2 وهمية.
7. الرسوم: حصول خفيف على نجمة في موضع مناسب وتحديث الشارات عند استحقاقها مع reduced-motion، وليس احتفالًا مع كل نقرة.

**قرار مطلوب:** اعتماد/تعديل هذه الثلاث علامات والشارات وفق هدف المنصة واحتياجات طلاب الصف الثالث قبل التنفيذ.

### قبول REW-01..REW-08
القاعدة معتمدة، يستحق فقط بعد state صحيح، pending محايد، دعم لا يحسم نجمة سلبًا، no duplicate/reload، لا انتقال مكافأة بين حسابين، عدد dashboard مطابق للledger، لا مقارنة أطفال، إظهار سبب الحصول على المكافأة.

## 8. الشخصية والتشجيع والانميشن ونسق الواجهة

- الحفاظ على شخصية هِمّة وأصولها النافعة: خمسة أوضاع girl محفوظة، وتقييم أصول boy والترخيص والأبعاد. ينبغي **نظام شخصية موحد** يختار الوضع حسب state لا صور موزعة عشوائيًا.
- حالات الشخصية: ترحيب ← شرح الخطوة ← بدء المهمة ← إرشاد/تلميح دون كشف الإجابة ← إنجاز ← تشجيع بعد التعثر ← انتظار المراجعة. لا إظهار شخصية تحتجب عنها الأزرار أو السؤال.
- لغة Motion صغيرة تعليمية: دخول بطاقة الدرس، انتقال السؤال، تقدم المرحلة، كشف دليل تشجيع، نجمة/شارة، انتقال بين المستويات، مع easing ثابت ومدة معتدلة وتزامن مع اكتمال الحالة من الخادم؛ لا صوت تلقائي مزعج أو حركات لا تنتهي.
- تعليمات عربية قصيرة ثابتة من قاموس محتوى مركزي حسب المرحلة؛ دعم زر «اسمع التعليمات» عندما يتوافر صوت صحيح؛ اختلاف صوتي/لهجة خاضع للمتخصص لا TTS عشوائي.
- Design Tokens مشتركة: ألوان هِمّة/خط/مسافات/أزرار/حقول/حالات/بطاقات/فراغات/رسوم/تركيز/RTL؛ لوحة المشرف نسخة مؤسسية من نفس النظام والطالب نسخة عمرية مناسبة، دون نسخ CSS متنافسة.
- Motion Reduced حسب reduced-motion.css، أدوات focus/keyboard، حجم هدف لمس مناسب للأطفال، عدم جعل الحركة شرطًا لفهم التعليمة.
- Design states كاملة: loading, empty, fail, retry, pending, waiting, locked, support, done، مع عدم ظهور placeholder/developer/debug/error object أو نص مكرر. واجهات المشرف يمكنها إظهار technical status داخل قسم تشخيص مقيد لا في سياق تعلم الطفل.

### قبول UX-01..UX-12
مراجعة نصوص شاملة، قاموس مكرر، اختبارات زحف نصوص UI لحظر TEST ONLY/معاينة/fixture/Lorem/debug على Student routes بعد release gate، التوجيه الصوتي، اتفاق الشخصية حسب الحالة، Reduced Motion، لا jitter/CLS، RTL/contrast/focus/touch/zoom200، ثبات Mobile/Desktop.

## 9. تصميم وتنفيذ الفحص البصري، صفحة صفحة (مخطط فقط)

المنهج الإلزامي خلال P09: شاشة حقيقية في Trial بحسابات **اختبار غير شخصية** لكل route وstate، 360/390/430px + tablet 768 + desktop 1280/1440، وعرض Zoom 200%. التقاط screenshot وDOM/action trace ولقطات قبل/بعد؛ لا اعتماد بالحكم على ملف CSS فقط.

- Admin: login، dashboard، students list/new/detail لكل تبويب من السبعة، audio-review التاريخي، lesson review، assessments review/placement، content explorer filters/item detail، media browser gallery/players، reports/exports، skills، settings account/security/supervisors، notification drawer، account redirect.
- Student: login، dashboard قبل القبلي، اختبار/انتظار/تسكين، catalog L1/L2/L3، تمهيد، فيديو، سبعة أنواع تفاعل، تلميح/محاولة ثانية، read/write، دعم، مراجعة، إعادة، مكافأة، إنهاء مستوى/بعدي/إنجاز.
- بيانات العرض: empty/one/many، 401/403/404/409/422/429/500، slow/failed media، unauthorized, wrong tenant, long Arabic names/title, 200% zoom, keyboard/screen reader heuristics.
- كل screenshot لازم current SHA/device/browser/state/time وPASS/FAIL، وتُربط بمشكلة محددة وأثرها، ثم يصمم root fix ويتحقق بعده. التقارير السابقة مصدر تسلسل لا تعوض الإثبات الحي.

## 10. التوزيع على خارطة المراحل الحالية — بلا فتح مرحلة الآن

| الفترة/الفئة | محتواها | شروط/بوابة |
|---|---|---|
| **P08 — ما تبقى من المرحلة الحالية** | تنفيذ جهاز Safari/Android لـDEV01–DEV16 في وقتها، التحقق من audio evidence/claim/replay والاحتفاظ/التصدير، تحكيم ما يلزم من rubrics، وتحديث تسليم P08. تضاف *التبعيات والمتطلبات الجديدة* تخطيطيًا دون فتح تنفيذ UI | CI/M04/M09 + QA الأجهزة + policy decisions + قبول المالك «تم» |
| **P09.0 — Baseline UI/UX + evidence matrix** | لقطة كل صفحة/حالة Mobile/Desktop، route inventory، runtime/API proof، سجل فجوات P0/P1، التحقق من P01F القديم وتصحيح status | لا تعديل قبل تثبيت تسلسل الاعتماد وbaseline |
| **P09.1 — Data models/RBAC/source-of-truth** | Admin permissions، V2 read models، official attempt/release pin، content/asset view contracts، notification roles، Student CurrentAction موحد | API + security + official counts دون أعطال |
| **P09.2 — Admin: content/media browsers** | تحويل content-preview إلى جدول تسلسلي read-only وv2-media إلى gallery/player read-only؛ عدم بناء CMS تحرير جديد | 300 items/89 assets/version/preview/mobile وعدم كشف الإجابات |
| **P09.3 — Admin: review/student dashboards/reports** | مركز المراجعة، Student360، تقارير V2، notifications، settings؛ إلغاء ازدواج القوائم مع حفظ compatibility | E2E real queues/read models/exports/RBAC/phone |
| **P09.4 — Student journey single V2** | V2 home/catalog/lesson/assessment/support/retry/results؛ عزل V1 عن تجربة V2 العادية | all 19 lessons + role/state/back/refresh/offline |
| **P09.5 — Rewards/character/Arabic copy/motion** | اعتماد reward policy قبل كود المنح، design system/tokens/components، text governance، تشجيع وحركة لا تشوش | reward invariants + a11y/reduced motion + no dev strings |
| **P09.6 — Full audit, visual and functional acceptance** | 300 أسئلة + أنواع + 12 دعمًا + 30/30، كامل صفحات المشرف والطالب/التقارير على Trial، 16 device audio، أداء وأمان ومصفوفة تكافؤ V1 | no P0/P1، screenshots current SHA، functional_ready_with_test_media، قبول المالك |
| **P10 — Final media + academic/production acceptance** | إحلال 19 فيديو، الصور/الأصوات المعتمدة، مطابقة المحتوى، سياسات التسجيلات والتصدير/الحذف، اختبارات Release Candidate الفعلية، Rollback | media_approved+academic_signoff+privacy+security+owner_release_approval |

**التبعيات:** P09.1 قبل صفحات تقرأ بيانات جديدة؛ P09.2 وP09.3 يمكن تقسيم تطويرهما إلى واجهات مستقلة بعد تثبيت العقد؛ P09.4 قبل rewards UI/motion؛ P09.6 لا يبدأ قبولها قبل إغلاق وظائف الصفحات؛ P10 لا تستعمل وسائط حقيقية لتجاوز الاختبارات الوظيفية. لا يفتح P09 إلا «تم» صريحة من المالك بعد بوابة P08.

## 11. تعريف اكتمال كل عنصر قبل «تم»

كل issue/صفحة تُوثق بـ:
- ID / الأولوية P0-P2 / مصدر الإثبات / السبب الجذري / سلوك «قبل وبعد» / مالك source of truth.
- API contract + state model + permissions + error and recovery + mobile/desktop design/RTL/a11y.
- unit/API/integration/E2E tests مبرهنة على HEAD نفسه، لقطة فيديو/صورة فعلية، فحص خصوصية وعدم كشف أسرار أو إجابات.
- قرار KEEP/REBUILD/RETIRE/REDIRECT مُعتمد، وMigration/rollback يحفظ التاريخ والروابط.
- نتيجة PASS/FAIL/NOT_RUN ولا يُحوّل وصف التصميم إلى نجاح تشغيل.

**الحدود الحالية:** P08=in_progress/acceptance_pending. P09=not_started. جميع البنود أعلاه PLANNED أو NEEDS_LIVE_UI_QA، وليست أعمالًا منفذة ولا إذنًا بتغيير الكود الآن.

## 12. قائمة قرارات لا تُفترض

1. سياسة الاحتفاظ بأصوات الطلاب وطلب الوصول والتصدير/الحذف مع المالك والمختص.
2. هل «حي» يقصد وصول التسجيل إلى المشرف فور إرساله (المقترح) أم بث صوت مباشر أثناء أداء الطفل؟ الخيار الثاني ليس ضمن النطاق المطبق ويحتاج تفويضًا مستقلًا.
3. هل يُسمح بـAI/ASR تجريبي مساعد فقط، ومع أي بيانات/موافقة/معيار ومتى؟ الافتراضي Human-First بلا تصحيح آلي.
4. اعتماد آلية النجوم الثلاث لكل درس وشارات المستويات، دون ربطها بالسرعة أو التفوق النسبي.
5. دور المشرف الأكاديمي مقابل المدير ومسؤول التصدير ونطاق الطلاب وحقوق العائلة.
6. عند الانتقال V2، مصير روابط جلسات V1 وتاريخ المكافآت والتسجيلات: توافق مقيد مع الحفاظ على البيانات وليس عرضها كمسار جديد.
7. نصوص التشجيع/أصوات التعليمات وشكل الشخصية ودرجة Motion بعد عرض نماذج بصرية في P09.

**هذه الخطة للإضافة إلى خارطة العمل؛ لم تنفذ تغييرات وظيفية أو تعديلات تصميم أو اختبارات أجهزة في هذا الالتزام.**
