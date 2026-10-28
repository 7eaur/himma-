> **مرجع معايير/أدلة سابق، وليس خطة تنفيذ حالية.** حالة الإغلاق والقرارات الأحدث وقائمة المتبقي الوحيدة في [الخطة الموحدة](HIMMA_V2_MASTER_STATUS_GAPS_REMAINING_WORK_HANDOFF_20261028_AR.md). أي كتابة حرة أو تسكين/بعدي يدوي أو اشتراط فيديوهات فردية أو حفظ الحسابات التجريبية الثلاثة في النص أدناه تجاوزه قرار المالك الأحدث.

# هِمّة V2 — تدقيق واجهات المشرف وبنك الدروس ومراجعة الصوت وتجربة الهاتف
التاريخ: 2026-10-28
الحالة: SOURCE_AUDIT_COMPLETE / UX_IMPLEMENTATION_PENDING / AUTHENTICATED_BROWSER_QA_PENDING
الفرع التنفيذي الوحيد: v2/01-learning-foundation-20261007
المرجع التاريخي للمقارنة: stage/02-content
الطلب: فحص أقسام لوحة المشرف واحدًا واحدًا، استعادة إمكانات مراجعة الصوت النافعة من V1، تقسيم الصفحات الطويلة، ووضع خطة UX عملية للهاتف والحاسوب.

## 0. حدود الدليل ومبادئ الاعتماد
- فحصت ملفات الصفحة والخدمات الخاصة بالتقييم في الفرع الحالي وملفات صفحة الصوت وملف الطالب في فرع V1، مع مراجعة وثائق P01-F وP09 وخطة العمل. هذا **فحص كود ومعلومات معمارية**؛ لم ألتقط في هذه الدفعة لقطات جديدة من متصفح مصادق، ولم أتحقق بصريًا من Railway على هاتف أو سطح مكتب. كل حكم عن الازدحام والأخطاء التفاعلية **فرضية UX تستلزم إثباتًا حيًا**، أما حقائق الاستدعاءات والتبويبات والحقول فمن المصدر.
- القرار الأحدث D26: التسكين والتكيف والدعم والبعدي تلقائيون؛ المشرف لا يعتمد المستوى ولا يختار علاج الضعف. دوره الأكاديمي اليدوي المؤقت هو تقييم التسجيل الصوتي وطلب إعادة تسجيله إلى حين اختبار/معايرة/اعتماد AI. لا تصحيح كتابة حرة بعد تحويل بنك V2 إلى تركيب حروف/كلمات.
- المرجع التعليمي الوحيد هو بنك V2 المثبت بالإصدار (300 سؤال، 19 درسًا، 12 مجموعة دعم، 30 قبلي +30 بعدي). لا نعرض تاريخ V1 في المنتج النهائي، ولا نحذف تسجيلات أو بيانات فعلية قبل نسخة آمنة وتفويض مستقل.
- المحافظة على قوة V1 وظيفيًا ليست نسخ مساراته أو إرجاع منطق 10 أنشطة/35 تقوية أو 50/70/80/85. لا تبنى لوحة تحرير ثانية أو محرك درجات موازٍ، ولا تُكتب CSS ترقيعية متكررة.
- مستويات الأولوية: P0 = سلامة التعليم/المراجعة أو منع التعطل/الفشل الخاطئ؛ P1 = UX ومعلومات/إنتاجية/أجهزة أساسية؛ P2 = تحسينات راحة غير مانعة. كل بند أدناه مفتوح إلى إثبات اختبار.

## 1. تدقيق بنك الدروس والأسئلة — /admin/content-preview
**المصدر الحالي:** apps/web/src/app/admin/(dashboard)/content-preview/page.tsx؛ API المعاينة V2 الحالي. تعرض الصفحة بنكًا read_only مع section filter/search، تجمع القبلي، 3 مستويات، الدعم، والبعدي؛ 25 سؤالًا في الصفحة، وكل عنصر details قابل للتوسيع ثم details آخر للإجابة والمرجع، ومعاينة بعض الوسائط عند فتحه.
**المقارنة V1:** كانت المعاينة قائمة طويلة ومكررة لعرض بيانات المحتوى التاريخي؛ تم بالفعل نقل المصدر إلى 300 سؤال V2 وإزالة mount بنك V1 من الواجهة؛ لا نعيده.
- UXA-01 / P1: لا يكون البحث عبر مُعرّف القسم وحده هو وسيلة اكتشاف الدرس؛ نحتاج شجرة/تبويبات مألوفة: قبلي | المستوى الأول | المستوى الثاني | المستوى الثالث | بعدي، داخل كل مستوى 6/6/7 دروس ومع كل درس دعمُه، وعرض مراحل تمهيد/فيديو/تدريب/اختبار مستقل/دعم.
- UXA-02 / P1: في desktop لوحة جانبية للقائمة والفلترة ومساحة تفاصيل السؤال؛ في الهاتف شاشة قائمة مختصرة ثم تفاصيل عنصر واحد مع رجوع واضح. لا تُعرض 25 إجابة ووسائطها مفتوحة دفعة واحدة، ويحفظ رابط العرض section + lesson + question والفلتر عند الرجوع.
- UXA-03 / P1: ملخص بنود كل درس يميز أنواع الأسئلة الستة، عدد GP/IC/Support، وجود الميديا، status، واجهة إظهار الإجابة للمشرف فقط، رسائل خاصة لـmedia pending/missing. بدلاً من طباعة answer/rubric JSON الخام كواجهة أساسية استخدم حقولًا عربية مقروءة؛ JSON في تبويب تقني اختياري بصلاحية.
- UXA-04 / P0 Release: الواجهة الحالية **معاينة فقط**، لا إدارة تأليف أو نشر. لا نسميها «تحرير البنك» ولا نضع حفظًا وهميًا. أي احتياج لاحق لتحرير البنك يكون workflow إصدار authoring draft → validation → academic/media signoff → immutable release، بتصريح مستقل، دون تعديل سؤال طالب في إصدار مثبت.
**قبول:** كل 300 سؤال يمكن الوصول له حسب قبلي/درس/دعم/بعدي مع عرض خياراته وصوته وصوره وإجابته للمشرف وحده، وبدون كشف private_answer إلى الطالب؛ 19/12 تظهر متسلسلة؛ deep-link والعودة والفلاتر واختبارات الضغط/التكبير والـRTL.

## 2. فحص مراجعة الصوت في V1 مقابل V2
**مصادر V1:** apps/web/src/app/admin/(dashboard)/audio-review/page.tsx في stage/02-content؛ services/api/review.py.
**V1 بالفعل:** طابور اختيار تسجيل واحد، اسم الطالب/الدرس/النص المرجعي/مشغل الصوت، قرار «اعتماد القراءة» أو «إعادة تسجيل»، عند الاعتماد target_units + deletions + substitutions + insertions، ملاحظات النطق والطلاقة، أزرار حفظ/إلغاء؛ حساب rubric_score = max(0,1-(D+S+I)/target_units). كانت واجهة عملية موجهة لقرار واحد.
**عيب V1 موثق في كوده:** response.is_correct = rubric_score > 0؛ لا يجوز نقل هذه القاعدة لأنها تمنح true لقراءة ضعيفة غير صفرية. كذلك لا يجوز نقل صوت المراجعة القديم للطالب الجديد.
**V2 بالفعل:** قائمتان منفصلتان، /admin/v2-assessments (25 بطاقة/صفحة)، /admin/v2-lesson-review (20 بطاقة/صفحة)، مع /admin/v2-reviewed-recordings (20 سجلًا/صفحة)؛ كل بطاقة تعرض الدليل/المرجع/تشغيل الصوت المحمي، note، ومخرجي is_correct=true/false، وطلب إعادة مستقل موثق عبر v2_retry_runtime؛ V2ReviewedAudioPlayer لا يفعّل القرار قبل end + acknowledgement. تسجيلات الطفل الأخيرة تُحفظ وفق D24، والمستبدلات تدار بسياسة الاحتفاظ. هذا فصل أمان مفيد يجب الاحتفاظ به.
- UXA-05 / P0: **إعادة معيار تقييم صوتي منظم إلى V2**: فصل حالة صلاحية التسجيل (صالح/صوت غير واضح/تسجيل تالف/إعادة مطلوب) عن جودة القراءة (عدد الوحدات، حذف، استبدال، إضافة، ملاحظات نطق/طلاقة)، وعن نتيجة المهارة. لا يُنسب تقييم إلى AI حاليًا. إضافة schema/evidence/rubric_version/Audit/API/report بنموذج واحد للاختبار والدرس؛ عدم الاكتفاء بتغيير UI وإرسال Boolean.
- UXA-06 / P0: منع الدرجة المزيفة. كل المدخلات أعداد صحيحة غير سالبة، target_units>0، لا تتجاوز D+S الوحدات المستهدفة؛ مراجعة تربوية لطريقة حساب المقياس ونطاقه وحالات الحروف/الكلمة/الجملة قبل اعتماده. **لا نستخدم score>0 كنجاح**. عند رفض التسجيل وطلب إعادة، يبقى الدليل pending غير صحيح/غير خاطئ حتى وصول آخر تسجيل صالح ومراجعته. اعتماد المراجع لا يعوض بيانات صوتية مفقودة.
- UXA-07 / P0: state machine صوتي وحيد واضح: pending_review → in_review/claimed → reviewed(graded) OR retry_requested → new_audio_submitted → pending_review → reviewed. نجاح الطلب يتأكد من الخادم، مع سياسة idempotency/concurrency؛ المستخدم لا يستطيع اعتماد ملف superseded، ولا تقييمه مرتين ولا مشاهدة تسريب لطالب آخر. الادّعاءات القديمة في شاشة الكتابة تُزال بعد parity؛ bank write_text=0.
- UXA-08 / P1: **مركز مراجعة صوت واحد**: تبويبات «بانتظار المراجعة / طلبات إعادة / وصلت إعادة / تم تقييمه»، ثم فلتر «قبلي/دروس/بعدي + طالب + التاريخ + حالة الصوت». البطاقة المختصرة تحدد الأولوية، ويُفتح **تسجيل واحد** في مساحة عمل قرار؛ يمين desktop قائمة، ويساره النص/الصوت والدرجات والقرار (يتكيف RTL)، هاتف: قائمة ثم تفاصيل ثم footer للحفظ/الإعادة ضمن safe area. الواجهة تحفظ claim/scroll/filter والعودة دون فقد مسودة ملاحظات.
- UXA-09 / P1: في التسجيل المختار تظهر المرجعية التعليمية بشرح مفهوم ووحدات الفحص، زر التشغيل/إعادة الاستماع، سرعة التشغيل إن سمح العقد، الحالة المسموعة، مجموع الأخطاء/معدل محسوب بوضوح، ثم «حفظ التقييم» أو «طلب إعادة التسجيل». لا تجعل خطأ الجودة الصوتية «إجابة خاطئة» آليًا، لا تسمح بقرار دون الاستماع المكتمل وتوثيق السبب. استخدم حوار تأكيد على إعادة التسجيل إذا لزم، لا حوار فوق حوار.
- UXA-10 / P1: /admin/v2-reviewed-recordings يعرض آخر تسجيل معتمد فقط مع نتيجة أصلية ومقاييسها ومصدر تقييم (المشرف؛ AI فقط بعد اعتماده)، ورابط «ملف الطالب» و«السؤال» بدون storage_key مكشوف أو أصوات نسخ تم حذفها. الاستعراض وarchive لا يحملان القائمة كاملة إلى DOM.
**قبول:** V1 numeric rubric parity بعد تصحيح الدلالة؛ approve/retry/submit/review/history بأدلة audio مؤمنة؛ محاولات pending محايدة، rubric grade لا تنشئ score بدون دليل، latest only والخصوصية والعودة بعد إعادة التسجيل، لا تدخل المشرف في التسكين/التحكم التكيفي.

## 3. ملف الطالب — /admin/students/[id]
**V1:** سبعة تبويبات فعلية: overview | journey | tests | recordings | adaptation | account | history.
**V2 الحالي:** تبويبان فقط v2/التقدم الدراسي وaccount/الحساب، حيث v2 يجمع مؤشرات التسكين، عدد الدروس والـ19 درسًا في disclosure، نتيجتي القبلي/البعدي، النجوم، الحالة والتقييمات، وروابط مراجعة خارج الصفحة؛ مصدر القراءة V2 صحيح، لكن التقسيم لا يخدم موظفًا يبحث عن إجراء محدد.
- UXA-11 / P1: إعادة **هيكل تبويبات سباعي من وظيفة V1 دون منطقها القديم**: 1 نظرة عامة (الاسم، الحالة، CurrentAction، عدد القراءات المعلقة)، 2 المسار والدروس (19 مع أقسام L1/L2/L3 والدرس الحالي والدعم والسبب)، 3 الاختبارات والنتائج (محاولات قبلي/بعدي الرسمية، الاختبارات pending، مصدر الدرجة)، 4 التسجيلات (المعلقة/المعتمدة، آخر ملف، روابط مراجعة خاصة بالطالب)، 5 التكيف والدعم (الفجوات ودليلها وإجراء المنصة الآلي، لا أزرار تدخل المشرف)، 6 الحساب والدخول (الرمز لا يُكشف إلا بفعل صريح)، 7 السجل (قرارات النظام والمراجعة والأحداث، مع redaction).
- UXA-12 / P1: header واحد صغير يحتوي الهوية + status + primary action، تبويبات أعلى المحتوى واضحة مع deep-link query ?tab=...؛ على الهاتف شريط أفقي قابل للتمرير أو اختيار القسم dropdown حسب اختبار الاستخدام، مع visible active state وعناوين قصيرة، من دون تمرير أفقي للمحتوى. افصل البيانات والاستعلامات تبعًا للتبويب لتقليل الحمل والتكرار؛ احتفظ بعزل الحالة عند تبديل Student A→B→A وامسح رموز الدخول من state عند التنقل والتبديل.
- UXA-13 / P0 Data correctness: درجات official فقط، skipped-by-placement ليس completion، ضعف الدعم غير المثبت ليس mastery؛ status pending_audio ليس فشلًا. مصدر lesson/skill/review/reward pinned release، وعرض partial-error بإعادة المحاولة على مستوى القسم لا إخفاء خلل المصدر بقيمة 0.
- UXA-14 / P1: وصول مباشر من جدول الطلاب والتسجيلات إلى التبويب/السؤال المناسب، روابط العودة تحفظ search/page/filters. لا بطاقات لا نهائية لكل 19 درسًا على الهاتف؛ عرض حسب المستوى وعدّاد completed/pending، تفاصيل الدرس عند فتحه.

## 4. بقية صفحات لوحة المشرف الطويلة — مراجعة ملفًا ملفًا
| الوجهة | الواقع في المصدر الحالي | القرار ودرجة الأولوية |
|---|---|---|
| /admin | dashboard حق V2، مهام وروابط ومؤشرات؛ sidebar ما زال يسمي «الاختبارات والتسكين» بعد إلغاء التسكين اليدوي | UXA-15 P1: تسمية «مراجعة تسجيلات الاختبارات»، مؤشرات actionable للـpending/retry، أولوية التسجيلات لا بطاقات معلومات غير قابلة للفعل |
| /admin/students | server paging مع بحث وحالة، وAdminResponsiveTable يعرض بطاقات على الهاتف | KEEP + regression P1: بحث debounced، pagination واضح، لا كشف access_code، اختبار A→B والهواتف |
| /admin/students/new | إنشاء طالب/رمز وأمن | KEEP + smoke P1: أخطاء 409/422، عدم تكرار submit، منع إفشاء رمز خارج النتيجة المخصصة |
| /admin/content-preview | 25 سؤالًا، details متداخلة، متصفح read_only، الصفحة تصبح طويلة عند فتح عناصر متعددة | UXA-01..04؛ واجهة استكشاف قسم/درس/سؤال بدل scroll مطول |
| /admin/v2-media | شبكة جميع 89 أصلًا مع client-side filter وبدون page sizing؛ الحالة المؤقتة قد تصاغ وكأنها معتمدة | UXA-16 P1: عرض حسب درس/نوع/حالة، pagination أو loading محدود؛ التمييز الصريح fixture vs final، media-preview ومسار مراجعة المفقود؛ لا إعلان approval من temporary |
| /admin/v2-assessments | 25 بطاقة مراجعة مطولة، Boolean + note | UXA-05..09؛ مركز الصوت الموحد |
| /admin/v2-lesson-review | 20 بطاقة مطولة، Boolean + note، شيفرة write_text تاريخية | UXA-05..09؛ المركز ذاته، إزالة نصوص الكتابة الحرة بعد ضمان parity |
| /admin/v2-reviewed-recordings | 20 بطاقة مع صوت لكل عنصر وبحث الطالب برقم ID فقط | UXA-10؛ searchable student وstatus، تفاصيل السجل عند الفتح، latest only |
| /admin/reports | table/list لكل الطلاب مع exports، ResponsiveTable جيد في المبدأ | UXA-17 P1: فلاتر نطاق/مرحلة وبطاقات ملخص، pagination/cohort scalable، عدم تحميل عشرات/مئات الأسطر بلا حاجة، اختبار الصادرات |
| /admin/skill-reports | grid لجميع دلائل المهارات، جلب مشترك، فلتر طالب/مرحلة بالواجهة | UXA-17 P1: group by 13 skill + phase ثم detail on demand، cohort pagination، توضيح graded vs mastery |
| /admin/settings | 3 تبويبات account/security/supervisors مع tablist/keyboard موجودة | KEEP + visual/ARIA regression؛ فصل الصلاحيات وإدارة آخر admin قضية RBAC مستقلة عن UX |
| /admin/audio-review | redirect إلى /admin/v2-assessments | RETAIN safe redirect لروابط V1 فقط، لا إظهار أرشيف V1 |
| Sidebar/layout | مجموعات روابط وتصميم desktop sidebar + mobile dialog وuseAccessibleDialog لتركيز/إغلاق | UXA-18 P1: إعادة تسمية وتجميع الملاحة حسب المهام ومراجعة الهاتف، مع الحفاظ على ESC/focus trap/return focus/scroll lock، وتبويب نشط قابل للفهم |

## 5. تصميم RTL متجاوب لا يكدس المحتوى
- هاتف 320/360/390/430: top bar مختصر، فتح قائمة المشرف باستخدام drawer، عناوين قصيرة، إجراءات أساسية مرئية؛ التفاصيل المؤجلة داخل تبويبات أو accordions؛ تجنب بطاقات 25 مراجعة كاملة أو 89 أصلًا دفعة واحدة. أهداف لمس ≥44×44 px، safe-area bottom، عدم تغطية أزرار القرار بعد scroll.
- Tablet 768/1024: شبكة 1–2 عمود، قائمة قابلة للطي، مساحة المراجعة تفصل selector/recording عن verdict دون قطع النص العربي.
- Desktop 1280/1440: قائمة جانبية ثابتة، list-detail review workbench، sidebar قائمة دروس + details، لا مسافات فارغة مفرطة أو خط صغير غير مقروء.
- Zoom 200% وkeyboard وscreen reader: لا horizontal overflow للصفحة/النموذج، ARIA tablist/tab/tabpanel أو نمط روابط حقيقي، home/end/arrow navigation حيث يلزم، Escape يغلق drawer دون فقد focus، خطأ معلن role=alert، حالة busy واحدة لكل طلب وملاحظات غير ضائعة.
- تقنيات تنظيمية: واحد AdminUI/Design Tokens؛ لا إعداد layout مختلف لكل شاشة، لا إعادة استخدام بيانات V1، لا زر يعرض نجاحًا قبل تأكيد API، لا loading overlay يعمي كامل الصفحة عند تحديث تبويب واحد.
- Perf/privacy: لا تحميل آلاف الطلاب/الميديا/الأصوات مقدمًا؛ server-side pagination وفهارس وتصنيف حسب الدور، تأخير البحث، عدم إدخال صوت/اسم/رمز إلى سجلات الويب أو لقطات القبول.

## 6. مصفوفة خطوات التنفيذ والفحص (يجب أن تُضاف إلى خطة P09/P10)
| الدفعة | الأولوية | التنفيذ | اختبارات قبول وإغلاق |
|---|---|---|---|
| UX-00 | P0 | تثبيت عقد D26 + فصل سلطة AI/audio عن placement/adaptation + فحص migration/rollback وإصدار snapshot | no-staff-placement/no-manual-support؛ الصوت pending محايد؛ CI/M04/M09 |
| UX-01 | P0 | مراجعة معيار القراءة V1 وتوقيع سياسة درجات V2؛ API/model/evidence وواجهة موحدة قبول/إعادة | numeric boundaries/rubric calibration، audio playback ack، duplicates, changed audio, redo, privacy |
| UX-02 | P1 | مركز تسجيلات واحد مع tabs وfilter/workspace وarchive | pretest/lesson/posttest reviewer flow على desktop/mobile، focus/scroll/deep links، latest only |
| UX-03 | P1 | Student360 سبعة أقسام V2-only مع lazy/data-status والعودة | A→B→A، incomplete/graded/retry/unmastered/no wrong score، 19 lessons، code concealment |
| UX-04 | P1 | بنك الدروس والأسئلة من مستويات → درس → مرحلة → سؤال؛ Media inventory grouped/paged | 300/19/12/89، all answer modes/option media, no private answer leak |
| UX-05 | P1 | اختصار dashboard/reports/skill reports/sidebar/mobile, preserve settings tabs | partial source handling, exports, list pagination, keyboard/RTL |
| UX-06 | P0 Acceptance | E2E authenticated real browser على Web/API deployed SAME SHA بعد CI، visuals + network effects + rollback/backup | screenshots for all states at 320/360/390/430/768/1024/1440 and zoom 200%, owner review |

### اختبارات حالة الصوت الإلزامية
AR-01: تسجيل صالح، استمع حتى النهاية، أدخل rubric، الحفظ مرة واحدة، API يعيد graded + audit.
AR-02: target_units=0 أو عدد خطأ سالب/غير منطقي يرفض 422 بلا grade.
AR-03: grade>0 لكن أقل من حد نجاح تربوي لا يوصف تلقائيًا «صحيح».
AR-04: تسجيل غير واضح يفتح إعادة مستقلة، الحالة pending ولا ترفع mastery ولا reward ولا placement.
AR-05: وصول تسجيل بديل → آخر تسجيل فقط يُعتمد، لا يعرض القديم، والتسجيل المؤقت/المستبدل يمضي بسياسة الخصوصية.
AR-06: المشرف لا يستطيع فتح صوت لطالب آخر عبر تزوير URL/ID، وتبديل الطلاب لا يخلط التسجيلات.
AR-07: ضغط متكرر/double-submit أو تزامن اثنين من المشرفين ينتج قرارًا نهائيًا واحدًا.
AR-08: صوت مفقود/ملف تالف/انقطاع S3/مراجعة طلب إعادة تظهر حالات مميزة ولا ينتج نجاحًا كاذبًا.
AR-09: تغيير تسجيل بعد playback يبطل acknowledgement، ويلزم الاستماع إلى النسخة الجديدة.
AR-10: grading completion يستأنف الدرس/القبلي/البعدي تلقائيًا وفق D26، دون زر اعتماد مستوى.

### اختبارات تنقل الهاتف
MOB-01..03: menu open/close/backdrop/Escape/focus restore/scroll lock؛ 320/390/430.
MOB-04: 7 tabs للطالب accessible + scrollable/dropdown، URL deep links والرجوع.
MOB-05: review queue→audio→grade/rerecord→next، حفظ filter + scroll وعدم قطع footer.
MOB-06: question bank section→lesson→question→back، لا lost context/no overflow.
MOB-07: 89 assets lazy/grouped؛ فشل audio/video/placeholder دون انهيار الصفحة.
MOB-08: reports exports، empty/error/permission/slow server، full keyboard & 200% zoom.
MOB-09: لم يُثبت نجاح هذه الاختبارات على المتصفح بعد؛ لا تُحوّل المصدر إلى VERIFIED_LIVE.

## 7. القرار التنفيذي والعوائق
- تم **إضافة هذه العناصر إلى خطة العمل** فقط في هذه الدفعة؛ لا تعديل لواجهات/درجات/DB الحية على Railway؛ لا تغيير branch؛ لا حذف.
- لا ينشئ أي شخص واجهة مراجعة جديدة قبل ربطها بنفس P08 endpoints/ReviewTask/AudioRetention وسؤال V2 pinned، مع فحص claim/permissions/rollback.
- **P0 المنتج السابق قائم**: التكيف الذاتي للفجوات، قبول محتوى release والوسائط، CI/M04/M09، تطابق Web/API، browser smoke، بيانات الطلاب/backup. تحسين UX يعمل ضمن هذه البوابات ولا يحل محلها.
- لا نسمي النسخة CLIENT_READY قبل الاختبار المتصفحي المصادق (صور/شبكة/سلوك)، QA ملاءمة القراءة لعمر الصف الثالث، وتعريف معيار صوتي موقع وتوثيق الوصول والأداء.
- الملفات السابقة المرجعية: docs/v2/DECISIONS_AR.md (D24/D25/D26)، docs/v2/09_IMPLEMENTATION_ROADMAP_AR.md، docs/v2/33_P01F_ADMIN_AND_SUPERVISOR_AUDIT_AR.md، docs/v2/26_V1_IDENTITY_PAGES_AND_FIXED_REGRESSIONS_AUDIT_AR.md، docs/v2/agent-ops/WORK_BROWSER_ACCEPTANCE_MATRIX_20261027_AR.md، docs/v2/work-owner/CURRENT_STATUS_AR.md.


## 8. التنفيذ الفعلي — الدفعة UX-01A على الفرع الرسمي (2026-10-28)
- Student360 `admin/students/[id]/page.tsx`: سبعة تبويبات ARIA، URL ?tab=، دعم لوحة المفاتيح، تقسيم تفاصيل المستويات الثلاثة، نقل النتائج/النجوم/التسجيلات/التكيف/سجل القرارات إلى أقسام مستقلة، إبقاء رمز الدخول مخفيًا عند التنقل.
- `services/api/v2_student_readmodel.py`: إضافات **مشرف فقط** لآخر 30 قرار تكيف و30 مهمة تقوية من نفس `content_release_id` المثبت، دون private answers أو access_code، مع تمييز `unmastered_gap`؛ `test_v2_student_readmodel.py` يختبر الصلاحيات والنتيجة.
- مراجعة الصوت: `V2ReviewQueuePicker.tsx` مشترك لصفحتَي `v2-assessments` و`v2-lesson-review`؛ يعرض تسجيلًا واحدًا مع اختيار السابق/التالي/ملف الطالب، ولا يغير API التقييم أو قيد استماع الملف؛ اختبار selector أضيف.
- `v2-reviewed-recordings/page.tsx`: قراءة filter `?student_id=` قبل طلب الأرشيف لتجنب عرض أصوات الطلاب الآخرين خلال الانتقال؛ الحفاظ على privacy/read-only.
- `content-preview/page.tsx`: تبويبات نوع محتوى قبلي/L1/L2/L3/دعم/بعدي، اختيار درس من قائمة المصدر وقائمة سؤال واحد للتفاصيل/الإجابات؛ نفس المصدر البالغ 300 بندًا دون تعديل أو نشر.
- `admin/(dashboard)/layout.tsx`: إعادة تنظيم القوائم حسب مهمة العمل وإزالة النص القديم «التسكين اليدوي».
- جرى تحديث Jest/E2E المصادر لواجهة 7 تبويبات والبنك، لكن **لم تُشغّل الاختبارات محليًا أو على CI** لهذه الدفعة؛ لم يُرصد مرور Workflow لهذا HEAD. أي تراجع بصري أو تعارض مصادقة يحتاج فحص Work/Browser مصادق، و`CI/M04/M09` على SHA واحد.
- لم تنفذ دفعة UX-01B: rubric الصوت الرقمي V2 مع قاعدة البيانات/المعيار التربوي والتقرير، دمج قوائم الصوت في inbox موحد، وتكميل عرض السجل الصوتي داخل ملف الطالب بدل روابط فحسب؛ هذه بنود منفصلة لا تُعتبر منجزة.
- لم يحصل نشر Web/API ولا migrations، ولم تمس بيانات الإنتاج. **لا تعلن UX_DONE أو CLIENT_READY** حتى ضمان إغلاق gate ونشر آمن/اختبارات الأجهزة الفعلية.


## 9. UX-01B source implementation — voice numeric rubric and consolidated navigation (2026-10-28)
- API: `ReadingRubricV2` optional schema during backward-compatible rollout (UI now required) with `target_units: 1..1000`, `deletions/substitutions/insertions >=0`, deletion+substitution <= target_units, notes. Observation `max(0,1-(D+S+I)/units)`, **never a mastery threshold**. Human `is_correct` remains independent; no automatic grade or AI voice claims.
- DB: model `V2AudioRubric`, unique per reviewed V2 `AudioSubmission`, `0030_v2_audio_rubrics` additive; intentionally isolated from V1 `audio_reviews` to avoid historical contamination. Migration needs separate DB gate.
- Reviewer UI: shared numeric editor used by `v2-assessments` and `v2-lesson-review`, decision buttons disabled until valid observations + complete recorded playback + supervisor reason. One supervisor center `v2-review-center` uses three ARIA tabs, old routes retained; direct Student360 links go to matching tab.
- Archive: `v2_audio_archive` returns a V2-only rubric for the latest reviewed voice with no storage key; reviewer sees numeric details on demand.
- Media: browser gallery limited to 12 visible items/page, filter resets page; no fake media approvals.
- Tests: new unit/UI cases for bad counts, review duplicate, explicit no-pass inference, archive privacy, reviewer tabs, 12 media cards; existing Playwright assertions may still need work. **Static source changes only**: no CI/Browser acceptance was run, no prod migration/deploy. Continue UX-02+ and P0 gates before full delivery.
