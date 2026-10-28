# هِمّة V2 — سجل الحالة الحقيقي وجميع الأعمال المتبقية وتسليم الاستكمال
**تاريخ الجرد:** 2026-10-28 (Asia/Aden)  
**النوع:** سجل تنفيذي موحد / Handoff / Release blockers — وليس شهادة جاهزية.  
**مستودع التنفيذ:** `7eaur/himma-`  
**فرع التنفيذ المباشر المعتمد من المالك:** `v2/01-learning-foundation-20261007`  
**فرع V1 مرجع قراءة فقط:** `stage/02-content`  
**HEAD تم التحقق منه قبل إنشاء هذا الملف:** `e378575cacb3c3354b4757686664bb9be964dd9b`. **بعد إنشاء هذا الملف سيكون HEAD أحدث بوثيقة فقط؛ يجب إعادة فحصه.**

## 0. طريقة استخدام الوثيقة / قاعدة الفصل بين الحالات
- `SOURCE_IMPLEMENTED`: الكود موجود على الفرع، لا يساوي مرور الاختبارات.
- `TESTED_TARGETED`: اختبارات محددة ناجحة في بناء موثق؛ لا يساوي E2E أو الموافقة التربوية.
- `DEPLOYED`: Railway SUCCESS على SHA محدد؛ لا يساوي إنجاز مسارات الويب.
- `LIVE_VERIFIED`: تحقق متصفح مصادق + HTTP/DB + screenshots على النشر الحالي.
- `OWNER_APPROVED`: اعتماد المالك للصيغة/المحتوى/السياسة؛ مختلف عن `P10_RELEASE_READY`.
- `OPEN`: مطلوب، أو نُفذ بعضه لكن دليل قبوله/تكافئه ناقص. `NOT_STARTED`: لم يتم تنفيذ الكود المتعلق به. `NEEDS_RECHECK`: مصدر تغير أو توثيق قديم ويجب التحقق لا الجزم.
- عند تعارض الوثائق، المصدر الحالي ونتائج الاختبارات والنشر المباشر أحدث، ثم القرارات D26 > D25 بالنسبة إلى **المراجعات والتسكين**. هذا الملف لا يلغي السجلات التفصيلية الأصلية؛ يوجه إلى الحقيقة الأحدث ويصحح وصفها.

## 1. حالة Github / Railway الفعلية وقت الجرد — لا تُستبدل بادعاءات سابقة
| المورد / Gate | النتيجة الموثقة | الدليل / الحكم |
|---|---|---|
| GitHub فرع V2 | HEAD `e378575cacb3c3354b4757686664bb9be964dd9b` قبل توثيق التسليم | آخر تغيير: اختبار Student360 انتظار تحميل طالب جديد |
| Railway API `himma-api` | **SUCCESS** على `d2046d0fe4834c5d9f28defab69f078531372497` | Deployment `a9d053cb-46a3-4a5a-9206-9c8f07565d48`؛ /health 200؛ بدأ الخادم |
| API targeted Pytest | **82 passed / 82**، خمسة تحذيرات | إعداد build عزل الاختبارات عن إعداد Redis للإنتاج: `ENV=development` للاختبار فقط؛ تشغيل الإنتاج بقي محميًا |
| قاعدة PostgreSQL الإنتاجية | ترحيل `0029_v2_system_placement` و`0030_v2_audio_rubrics` نفذا بنجاح مع نشر API | لا تثبت سجلات النجاح إجراء نسخة احتياطية/استعادة/rollback؛ تلك البوابة **OPEN** |
| Railway Web `himma-web` | آخر نجاح **قديم** `ad0243022563ccd09d3518223ce37d75cff996f3` | Deployment `cbfd5a87-2f5c-4eeb-815e-6944aab18224` |
| Web الجديد `e378575...` | **FAILED**؛ لم تُرقَّ واجهة الطالب/المشرف | Deployment `d4899c09-c57e-47c2-a0bd-622b36e69a72`؛ Jest/ملف الطالب بعد lint، آخر السجل مقطوع |
| Web Jest قبل آخر تعديل | **170 passed / 172، 2 failed** | `Student360` (تبديل A→B) و`proxySecurity` بيئة Railway؛ عُدّلت الاختبارات، لكن إعادة البناء اللاحقة FAILED، فلا تعلن 172/172 |
| Vercel GitHub status | failure من `build-rate-limit` | حد حساب النشر، **ليس دليلًا على فشل/نجاح صحة V2** |
| CI + M04 + M09 على HEAD الأخير | **لم يتحقق لها نجاح موحد** | الدليل القديم P09.0 (`4115fa2`) لا ينطبق على HEAD الجديد |
| Browser authenticated / صور الهاتف | **NOT_VERIFIED على Web الجديد** | لا توجد شهادة فحص مباشر للمشرف/الطالب على آخر إصدار |
| الـSHA بين Web/API | **مختلف حاليًا** | API حديث / Web قديم؛ لا يُعلن إصدار موحد حتى نشر Web واختبار توافقه |
| تغيير بيانات الطلاب أو تنظيف V1 | لا حذف شامل/ترحيل مستخدم معتمد | لا تمس البيانات القائمة أو الأصول دون قرار وحماية قانونية/نسخة موثقة |

**مهم:** اسم Railway environment هو `production`؛ ورد في بعض الوثائق وصف بيئة Trial أو معاينة قديم. لا تنشئ بيئة موازية جديدة، ولا تعتبر أن DB اختبارية. أي نسخة احتياطية لا يمكن إثباتها = غير معتمدة. لا تُعد تشغيل migration 0030 يدويًا دون حاجة مثبتة.

## 2. قرارات المالك النهائية التي لا يجوز الرجوع عنها
1. تحديث منصة هِمّة نفسها كـV2 كأنها أول إصدار مرتب؛ **لا تأثير وظيفي ظاهر للمستخدم من V1** ولا فروع معاينة جديدة، لكن الاحتفاظ بالأصول التعليمية والهوية والوظائف النافعة وحقوق بيانات السابقين.
2. المسار **اختبار قبلي → تسكين آلي → مستوى 1/2/3 → درس/تمهيد فيديو → تدريب بتلميح → اختبار درس → دعم متكيف مدمج → بعدي آلي**. لا محرك تعلم موازٍ ولا "أنشطة V1" في رحلة الطفل.
3. **D26 أعلى من D25**: التسكين **آلي** بعد إنهاء القبلي وتصحيح تسجيلاته البشرية؛ <50% L1، 50–<80% L2، >=80% L3؛ لا تدخل مشرف لتعديل المستوى. إضافة الضعف والدعم واختيار السؤال والعودة والبعدي آلية؛ دور المشرف **مراجعة تسجيلات القراءة فقط** مؤقتًا.
4. الدرس يحتاج فيديو تمهيد الهدف و3 أمثلة (المحتوى النهائي لاحقًا)، ثم تدريب 3–4 أسئلة وتلميح، واختبار 3–4 أسئلة، دعم/إعادة تحقق دون حبس الطالب في حلقة. الانتقال بعد دعم غير مثبت لا يعني mastering، ولا تُمنح شارة/نجمة إتقان مزيفة.
5. بنك المحتوى المعتمد: **300 بندًا، 19 درسًا، 12 دعمًا، 6 أنماط نشطة** (`choose_one`, `listen_choose_one`, `sequence`, `build_word`, `choose_image`, `read_aloud`)، منها **62 قراءة صوتية**. `write_text=0`: تحويل 21 حالة كتابة حرة إلى 9 بناء كلمة و12 ترتيب جملة؛ اختبار وتقييم تلقائي لتركيب الكلمة والجملة.
6. الاحتفاظ **بآخر تسجيل صوتي معتمد فقط** لكل نشاط/طالب، والتخلص الآمن من الملغى والمؤقت/المستبدل؛ حفظ سجل وصف المحاولات دون تعريض الملفات القديمة. لا تقييم ASR حقيقي ولا رفع صوت طرف ثالث قبل عقد موافقة ومعايرة، ومراجعة المشرف مستمرة.
7. عمل لوحة إدارة منظمة، صفحات قصيرة، الهاتف والتابلت والكمبيوتر، تبويبات ملف طالب مستقلة، مركز مراجعة واحد، بنك محتوى مرئي، تقارير ومكافآت صادقة، تصميم وهوية هِمّة دون صفحات طويلة أو ازدواجيات. إصلاح جذري في المصدر، لا ترقيعات CSS متراكمة.
8. المستخدم طلب **التعديل والنشر في المشروع الأصلي الحالي**، لا Branch/Preview إضافي. لكن سلامة البيانات، الـgate واختبارات قبول العميل لا تُتجاوز.

## 3. ما نُفّذ مؤخرًا (حالة الكود مقابل الإثبات)
| ID | المنفذ ومكانه | حالة المصدر | ما لم يُغلق بعد |
|---|---|---|---|
| D26-A | قرار التسكين الآلي وإتاحة البعدي آليًا، `v2_assessment_runtime.py`, `v2_student_accounts.py` و`0029` | SOURCE_IMPLEMENTED + API DEPLOYED | E2E لثلاث مستويات وملفات طالب حقيقية وصوت القبلي/بعدي والـSHA الواحد |
| D26-B | تحقق إضافي ودعم موجه من محرك التكيف بعد اختلاف الأخطاء وإعادة حدود الدعم، `v2_adaptation_runtime.py`, `v2_adaptation_policy.py`, `v2_rewards.py` | SOURCE_IMPLEMENTED + targeted backend pass | جدولة العودة لفجوة لم تُثبت، دعم فجوات القبلي، قرار استحقاقات كل السيناريوهات |
| UX-01A | ملف طالب 7 تبويبات وread-only دعم/سجل قرارات، `students/[id]/page.tsx` + `v2_student_readmodel.py` | SOURCE_IMPLEMENTED + بعض backend tests pass | آخر Web Jest أعاد الفشل في حالة A→B؛ تحقق الخصوصية بعد تبديل المستخدم وURL state |
| UX-01A | المراجعة تسجيل واحد في الواجهة، مكون `V2ReviewQueuePicker.tsx` بين قبلي/بعدي ودروس | SOURCE_IMPLEMENTED | بصري حقيقي، حالات القفل/الأذونات والقائمة الطويلة |
| UX-01A | بنك read-only مصنف للمراحل وسؤال واحد، `content-preview/page.tsx` | SOURCE_IMPLEMENTED | شجرة درس/مرحلة/سؤال متكاملة وpreview صور/صوت صحيحة وتجربة 300 بندًا |
| UX-01B | Rubric تسجيل `target_units/deletions/substitutions/insertions` وملاحظات النطق/الطلاقة، `V2ReadingRubricEditor.tsx`, `v2_audio_rubric.py` | SOURCE_IMPLEMENTED + targeted Python pass | معايرة أكاديمية للعتبات وE2E مع تشغيل كامل و422/409/503 وباقي المستهلكين |
| UX-01B | جدول V2 مستقل `V2AudioRubric` + `0030` (لا إعادة استعمال V1 `audio_reviews`) | API DEPLOYED / migration SUCCESS | مراجعة backup/restore وبيانات التقييم الحية وصحة Postgres ثم compat rollback |
| UX-01B | مركز صوت `/admin/v2-review-center` ثلاث تبويبات، sidebar مختصر، الأرشيف يعرض rubric للملف الأخير | SOURCE_IMPLEMENTED | تمييز pending/retry/requested/submitted/reviewed، بحث طالب عملي، صلاحيات، أخذ screenshot |
| UX-01B | معرض الوسائط `/admin/v2-media` 12 بطاقة/صفحة وفلترة | SOURCE_IMPLEMENTED | تجميع بحسب الدرس/الحالة، حالة 89 أصلًا الفعلية وplaceholder/final وتصريحات الوسائط |
| P09-WEB | ESLint أخطاء JSX/hooks أُصلحت؛ اختبار Jest `NODE_ENV=test` أصلح React.act؛ تعديلات على `proxySecurity.test.ts` و`students/[id]/page.test.tsx` | SOURCE_IMPLEMENTED | **آخر WEB build FAILED**، لا TypeScript/Next production pass مُثبت ولا نشر للويب |

**التفسير الصحيح:** API جرى نشره وأصبح مثبتًا تقنيًا ضمن الجزء الذي اختُبر؛ **قائمة شاشات UX الجديدة كلها غير منشورة بعد**. لا تدّعِ أن إعادة كتابة اختبار تضاهي إثبات سلامة تبديل طالب فعليًا. بعض البيانات المصدرية والتوثيقية القديمة توحي خلاف ذلك.

## 4. سجل العوائق الحرجة P0 — يجب إغلاقها بهذا الترتيب
| ID | المشكلة / السبب الجذري المحتمل | المطلوب للإغلاق / الدليل |
|---|---|---|
| P0-01 | **Web deployment FAILED على `e378575`**؛ آخر Jest يرسل dump DOM طويلًا في تقرير طالب رقم 2؛ قائمة أخطاء كاملة غير متاحة من آخر 500 event | اعزل test المتعثر `students/[id]/page.test.tsx` وحده بـ Jest --runInBand --silent / --json output؛ افحص تبديل ID كـroute remount أو reset لكل state والنتائج والرموز مع سباق fetch، أصلح سلوك التطبيق لا التوقع فقط، ثم rerun كل suites |
| P0-02 | 172/172 Jest وNext TypeScript/production build لم يثبتا بعد | `npm run lint`، `NODE_ENV=test npm test -- --ci`، `npm run build` على SHA واحد مع logs وأرقام نجاح حقيقية؛ بعدها Railway Web SUCCESS + /health |
| P0-03 | **API/Web deployed SHA mismatch** | انشر واجهة Web على الخدمة الحالية بعد اجتياز الفحوص، أعد تشغيل targeted API/tests المطابقة لنفس SHA أو أثبت parity مع SHA API بشكل مشروح؛ فحص BFF/API والصفحات |
| P0-04 | **اختلاف صلاحيات حالة طالب A→B→A، السر/الصوت** | اختبر identity switch قبل/بعد عرض رمز الدخول، تبديل tabs وback/forward وresponses out-of-order؛ لا ظهور لحظي لبيانات A في B، لا access_code أو answer/audio leak، 401/403 |
| P0-05 | لم يثبت Backup/Restore قبل ترحيلات الإنتاج رغم أنها نُفذت بنجاح | حصر النسخة الاحتياطية الحقيقية، تأكيد السعة والاستعادة في بيئة غير إنتاجية بإذن (بدون إعادة إنشاء معاينة منتج)، خطة rollback متوافقة مع قاعدة 0030؛ لا حذف |
| P0-06 | D26 التسكين/التكيف والبعدي تحتاج قبول حالات الحواف | ثلاث مستويات وحدود 49/50/79/80، audio pending محايد، lost ACK/reload/idempotency، دعم محدود لا يمنح mastery، بعدي يتطلب أدلة رسمية مكتملة، لا رجوع إلى تبديل مستوى المشرف |
| P0-07 | صوت طفل حقيقي: أمن storage + client replay + retry + latest-only غير مقبول حيًا على الجديد | Safari/Android، S3 auth/presigned, storage outage 503, corrupted/missing 409, playback acknowledgement، lock/concurrency/double-approve، إعادة تسجيل صحيحة وتقرير grade محفوظ |
| P0-08 | حماية إصدار المحتوى Bank snapshot غير مغطاة end-to-end على الإصدار الأخير | pin original release لكل سؤال/درس/دعم/قبلي وبعدي، no private answer, no cross-release grading، رفض missing snapshot بمعلومة واضحة |
| P0-09 | إعطاء رابط/تسليم نسخة عميل بينما صور Browser/E2E الحالية غير مكتملة | تمشي جميع مسارات الطالب والمشرف على Web LIVE الجديد وبأدلة network/DB وصور 320..1440، عتبات وصول وصحة تصميم |
| P0-10 | P10 المحتوى التعليمي النهائي غير معتمد: 19 فيديو + ملفات أصوات وصور/نصوص مرتبطة | تسلم الأصول النهائية وقائمة النواقص الحية، ربط كل درس مع الملف/النص/الإيقاف الزمني، ضمان media_approved وacademic_signoff؛ لا اعتبار فيديو TEST_ONLY منتجًا نهائيًا |
| P0-11 | مستخدمون حقيقيون/قرارات صوت وما يُحذف | ضمان الخصوصية والاحتفاظ وحفظ آخر صوت وحده وتنظيف الملفات المؤقتة بأمان، اتفاق سياسة مدة الحفظ والتصدير/المحو؛ لا حذف سابق دون تفويض |
| P0-12 | GitHub CI/M04/M09 على آخر SHA غير مثبت وVercel build-rate-limit | تحقق من Actions على SHA نفسه أو تشغيل suite من البيئة المتاحة دون تعطيل الحماية، توثيق run IDs؛ Vercel ليس بوابة وحيدة ولا تحايل عبر تخطي الاختبارات |

## 5. سجل الفجوات الأصلية P09-F01..F14 (تاريخي ← حالة اليوم)
هذا السجل ينقل IDs من `56_P09_0_LIVE_UI_SOURCE_BASELINE_AND_GAP_REGISTER_AR.md` بدقة ولا يغلقها بالتخمين.
| ID | أصل المشكلة / طلب المالك | الحالة الآن / الباقي |
|---|---|---|
| F01 | مصدر طالب يجمع V1/V2 | أُعيد توجيهه للمسار V2 في المصدر سابقًا؛ **NEEDS_LIVE_RECHECK** للطالب الجديد والتاريخي/حماية routes |
| F02 | content preview يستعرض بيانات V1 لا بنك V2 | source replaced بمتصفح V2 300 سؤال + واجهة اختيار سؤال؛ **P1** استكمال IA وproof |
| F03 | الوسائط بلا preview صحيح وoverflow | source preview/paging 12؛ **P1** grouping/availability/RTL/media playback actual |
| F04 | قائمة الطلاب تعتمد 0/10 نشاط V1 بدل 19 درسًا | source V2 readmodels؛ **P1** تحقق 19/skipped/graded/bad states على الويب |
| F05 | كشف access_code في جدول وبطاقات الهاتف | code conceal/reveal مقيّد؛ **P0 privacy live QA** مع profiles وخروج |
| F06 | لوحة المشرف وتقارير المهارات تعتمد أجزاء قديمة | source readmodel/report جزئيًا؛ **P1** accuracy/cohort paging/exports و13 مهارة |
| F07 | مراجعات صوت مشتتة بين صفحات كثيرة | source review-center + queue single item؛ **P1** tabs الحالة وفلترة retry ومراجعة الأرشيف |
| F08 | نجوم V1 خاطئة ومكافآت غير موثوقة | v2_rewards event ledger في المصدر؛ **P0** تحقّق من استحقاق بدون mastery ومزامنة مرة واحدة |
| F09 | لغة UI تقنية وTEST ONLY داخل رحلة الطفل | **P1** تدقيق صياغة intro, catalog, progress, rewards وموضع banner |
| F10 | نقص screenshots/E2E لحالات مشرف مصادق | خط أساس P09.0 قديم اكتمل؛ **P0** صور للحالات الجديدة على SHA منشور حديث |
| F11 | توثيق قديم `write_text=21` | البنك الحالي write_text=0؛ **P1** تنظيف النصوص/legacy route/نسخ التوافق دون فقد |
| F12 | لا قبول Safari/Chrome/S3 retention backup | **P0** أجهزة حقيقية + نسخة احتياطية/restore وسياسة صوت |
| F13 | احتمال sticky bar يغطي محتوى preview بالهاتف | **P1** إعادة فحص scroll والفراغ الآمن بعد تحسين الواجهة |
| F14 | الواجهة تقول «سبعة أنواع» أو «أكتب» | **P1** ستة أنواع نشطة وتركيب كلمة/جملة بلا تأليف حر |

## 6. سجل UXA-01..UXA-18 — ماذا صار وماذا بقي
المرجع التفصيلي `agent-ops/HIMMA_V2_ADMIN_UX_AUDIO_REVIEW_AND_CONTENT_AUDIT_20261028_AR.md`.
| IDs | التنفيذ أو الصفة | الإغلاق الناقص |
|---|---|---|
| UXA-01..04 | بنك V2 متدرج وأنماط وأسئلة في واجهة مشرف read-only: **PARTIAL SOURCE** | filter درس + intro/video/GP/IC/support، وسائط وanswer privacy، search/pagination/back context، 300/19/12 |
| UXA-05..09 | استماع وبينة ومراجعة رقمية آمنة وطلب إعادة: **PARTIAL SOURCE + API DEPLOYED** | full recording UX، rubric academic signoff، approve/retry/error/lock E2E، التمييز بين التقدير الوصفي والقرار |
| UXA-10 | أرشيف آخر صوت وتصفية/score: **PARTIAL SOURCE** | بحث بالاسم/الرقم، latest only، حالات إعادة الصوت، privacy RTL |
| UXA-11 | ملف طالب 7 تبويبات: **SOURCE** | اختبار Identity A→B، tabs, URL, data isolation, عدم كشف رموز |
| UXA-12 | IA/header/tabs/mobile 7 sections: **SOURCE** | layout/ARIA/200% zoom/keyboard screenshots، lazy sections |
| UXA-13 | درجة رسمية، pending ليس صفرًا، skipped لا يعني completed، unmastered ليس mastery: **PARTIAL BACKEND** | real report reading and error states |
| UXA-14 | وصول من قائمة الطلاب/التسجيل للدرس، 19 درسًا حسب المستوى: **PARTIAL SOURCE** | links/back preserving filters/pagination، responsive cards |
| UXA-15 | dashboard actions/nav ودور المشرف: **PARTIAL SOURCE** | counts pending/redo/reviewed، clickable dashboard، no legacy terms |
| UXA-16 | 89 وسائط وأصل/حالة/نوع، paging 12: **PARTIAL SOURCE** | grouped by lesson/status، media QA, fixture ≠ final |
| UXA-17 | reports/skills/tables: **OPEN/NEEDS_RECHECK** | pagination+filters، 13 skills/grouped details، exports Excel/PDF، حسابات mastery صحيحة |
| UXA-18 | sidebar/drawer mobile: **PARTIAL SOURCE** | اختبار ESC/return focus/scroll lock/device sizes |

## 7. مهام P1/P2 الوظائف والتصميم والتشغيل التي لم تُغلق
| ID | العمل المطلوب | بوابة القبول |
|---|---|---|
| A-01 | لوحة المشرف الرئيسية: بطاقات قصيرة actionable لـwaiting_review/retake/طلاب يحتاجون صوت، لا عرض قوائم تاريخية | مصدر V2 وحده، شاشة هاتف، links صحيحة |
| A-02 | `/admin/students`: البحث/التصفية والترقيم وتصدير المجموعات والأمان | paging وعدم انسكاب هاتف وعدم كشف access_code |
| A-03 | `/admin/students/new`: إدخال أنيق وأخطاء 409/422 وdouble submit | طفل جديد يذهب إلى pretest تلقائيًا، لا ينشئ V1 State |
| A-04 | Student360: Account منفصل، Assessment timeline، Recording timeline، Adaptation/History من release المثبت | سبعة أقسام قصيرة، no 19-card wall، no stale data |
| A-05 | `/admin/v2-review-center`: فلترة نوع النشاط والحالة والطالب، next/prev، شاشة واحدة للصوت وقرار/سبب | حالات pending/retry/submitted/reviewed مع حفظ وإعادة بالـAPI |
| A-06 | `/admin/content-preview`: hierarchy pretest→L1/2/3→lesson/GP/IC/support→item، مخطط الهدف/التمهيد | 300 سؤال/19 درسًا/12 دعمًا، الصور/الصوت والحلول مخفية عن الطالب |
| A-07 | `/admin/v2-media`: grouping status/lesson، تمييز مفقود/مؤقت/مرشح/نهائي، lazy loading | إظهار الحقيقة وتجنب false approvals |
| A-08 | `/admin/reports`: cohort/date/level، ملخص درجات قبلي/بعدي وتقدم/دعم، pagination | CSV/Excel/PDF عند وجوده صحيح، no PII leak |
| A-09 | `/admin/skill-reports`: grouping المهارات الـ13 ونوع الدليل، تفاصيل عند الطلب | لا confusion between graded/verified mastery |
| A-10 | `/admin/settings` و`/admin/account`: preserve tabs/security/RBAC والإشعارات | صلاحيات واضحة، منع إزالة آخر مشرف، لا admin secrets |
| A-11 | الطالب: أول دخول/لوحة/التبويب، CTA واحد لحالته، preview تمهيد، بُعد الهاتف | صوت/فيديو وnavigation/resume لا technical errors |
| A-12 | `InteractionPlayer` للأنواع الستة وحروف مكررة وترتيبات جمل بديلة معتمدة | all modes+RTL+keyboard+تعليق الصوت |
| A-13 | التصميم: هوية هِمّة والشعار/الخط/الشخصيات/التشجيع/النجوم دون V1 labels | consistent tokens/UI kit، صور عالية الوضوح، 320–1440 |
| A-14 | خاصية الإشعارات المفيدة وسهولة الوصول | لا duplicate/unread phantom/legacy deep link |
| A-15 | الأداء: pagination وqueries scoped/latency/cold start وCLS/large media | performance budget واقعي + server errors + browser telemetry |
| A-16 | دورة الصوت الشخصية: Cleanup canceled or expired uploads/recordings مع policy وaudit | delete only safe objects, last approved preserved |
| A-17 | مراجعة وثائق الكتابة والتركيب والأمثلة والتشكيل واللهجة العُمانية الخفيفة للفيديو التعليمي | تربوي/لغوي معتمد لكل درس والدعم والقبلي/البعدي |
| A-18 | إغلاق V1 في الواجهات/الخدمات التي تعرضه لطفل V2، إزالة history/archive product UI | parity سجل F01–F36 من `25_V1_TO_V2_FEATURE_PARITY_REGISTER_AR.md` مع عدم حذف بيانات قانونية |
| A-19 | ربط الوسائط النهائية من العميل: ملفات الصوت التربوي، أصوات نطق الطفل المعتمدة، صور الدروس، الفيديوهات و12 دعمًا | Asset manifest/checksum/approved role per owner/release |
| A-20 | تعليمات المشرف/العميل، حسابات التجربة والمساعدة والتسليم | walkthrough وسيناريوهات تشغيل مسؤولة وتوثيق تشغيل فعلي |

## 8. الأصول التربوية والوسائط — ما لا يجوز اعتباره جاهزًا
- **الموجود في البنك للتطوير:** 300 سؤال، 19 درسًا، 12 دعمًا، 62 قراءة صوتية، 6 أنماط، كل طالب pinned إلى snapshot واحد.
- **89** هو جرد وسائط في تقرير UX وليس تأكيدًا بأن 89 ملفًا كلها إنتاجية وملائمة. تمييز `ready/TEST_ONLY/temporary/pending/missing` لكل أصل يجب إعادة حسابه حيًا قبل توقيع القائمة النهائية؛ لا تختلق أعداد ملفات ناقصة.
- المطلوب 19 فيديو درس نهائيًا، ونصوص الأهداف/3 أمثلة، صور وأصوات تعليمية مطابقة للدرس، أصوات الطفل/أسئلة القراءة وتشكيل صحيح، ودعم متكيف يطابق الفجوة. بعض هذه الأصول قد تكون موجودة/مرشحة وتحتاج QA؛ لا تجزم بأنها كلها مفقودة ولا بأنها كلها اعتمدت.
- `media_approved` و`academic_signoff` و`release_ready` بوابات مستقلة عن النجاح التقني أو وجود فيديو placeholder. لا تتطلب الحزمة الأكاديمية إعادة كتابة محتوى الطالب كله إن كان صالحًا.

## 9. مصفوفة القبول النهائية لكل المسارات — يجب تنفيذها على نشر فعلي
**المشرف**: `/admin/login`, `/admin`, `/admin/account`, `/admin/students`, `/admin/students/new`, `/admin/students/[id]`, `/admin/v2-review-center`, `/admin/v2-assessments`, `/admin/v2-lesson-review`, `/admin/v2-reviewed-recordings`, `/admin/content-preview`, `/admin/v2-media`, `/admin/reports`, `/admin/skill-reports`, `/admin/settings`, redirect آمن `/admin/audio-review`.

**الطالب**: `/student/login`, `/student`, `/student/assessment-v2/[sessionId]`, `/student/learning-v2`, `/student/learning-v2/[sessionId]`, legacy guards `/student/activity/[id]` و`/student/session/[id]`. أضف الصفحة العامة/landing إذا استمر عرضها.

**أدوار وحالات**: مشرف صحيح/منتهي/غير مخول، طالب جديد N، طالب legacy L (دون إتلاف ملفه)، قبلي مستأنف P، انتظار صوت R، طالب L1/L2/L3 S، مجهول/طالب آخر U. لا يُحسب pending قراءة فشلًا، ولا pretest gap تقوية معتمدة دون حلقة دعم.

**مقاسات**: 320/360/390/430 هاتف + 768/1024 تابلت + 1280/1440 ديسكتوب، تكبير 200%، RTL، font/responsive/media query، 44px targets، keyboard/tab/focus/Escape، safe-area no sticky overlay. لكل Route نتيجة فعلية + screenshot + trace/network + مستند التغييرات + SHA.

**قاعدة عدم الإغلاق:** مشاهدة Swagger أو status 200 لا تعني أن زر الاعتماد/إعادة التسجيل أو تقرير PDF أو دخول الطالب يعمل. يجب إثبات الأثر في DB/Evidence وعدم كشف private_answer أو storage_key أو access_code.

## 10. ما فعله النشر الأخير، ولماذا توقف
1. طُلب النشر مباشرة على الخدمات الأصلية. غُيّر source pin لبناء API، وأُضيفت بوابة `python -m compileall` + مجموعة Pytest. فشلت الاختبارات أولًا بـ503 لأن build يعمل بإعداد Redis production. شُغلت **الاختبارات فقط** بـ`ENV=development` دون تخفيف runtime API الحي.
2. كشف Pytest نقص Evidence رسمي في fixture لتسكين مستوى 2 وتقدم الدروس؛ أُصلحت fixture بجلسة قبلي رسمية و`PlacementDecisionV2`، لا تخفيف للمنطق. كُشف تداخل جلسة مشرف/طالب في TestClient، عُزل ترتيب المصادقة في fixture.
3. نجحت 82 targeted API tests؛ نُشر API `d2046d0`، نُفذ `0029` و`0030`، /health=200. لم يُثبت full 1000+ suite على SHA نفسه.
4. نُشر بناء Web `d2046d0` ثم `3058caa` و`d64dd1e` و`e378575`: فشل lint أولًا JSX غير مغلق ثم React setState-in-effect؛ أُصلح الكود. عند تشغيل Jest في Node production تعطل React.act؛ عُزل الاختبار بـ`NODE_ENV=test`.
5. في إحدى المحاولات: 170 passed / 2 failed / 172 total؛ اختباري student profile switching وproxySecurity origin synthetic. عُدّلا على `e378575`. **آخر بناء `d4899c09-c57e-47c2-a0bd-622b36e69a72` FAILED**؛ العرض الطويل للـDOM في السجل الأخير يمنع معرفة الملخص الكامل؛ لا تعلن النجاح أو تكتفي بتعديل assertion آخر دون اختبار سلوك التطبيق.
6. Vercel CI status على HEAD فشل بسبب account build-rate-limit وليس بسبب كود ثبت فشله؛ GitHub CI/M04/M09 لهذه الدفعة يحتاج دليل جديد.
7. لم يحصل نشر جديد ناجح للـWeb؛ لم يُعمل browser acceptance/owner educational signoff. فلا تقل “النسخة نظيفة جاهزة”.

## 11. خطة الدفعات التالية بالأولوية والتبعيات — داخل نفس الفرع والخدمات
| الدفعة | الإجراء/الترتيب | شرط الخروج |
|---|---|---|
| G0 P0 | إعادة فحص branch SHA وحالة Railway وفشل Jest؛ عدم افتراض أن docs-only HEAD نُشر | تقرير root cause لـStudent360 identity swap مع test وعزل old profile |
| G1 P0 | تشغيل isolated Jest security/student + جميع 172 + lint + Next TS build، ثم CI/M04/M09 المطابقة | all green بأرقام/SHA حقيقية |
| G2 P0 | نشر Web على `himma-web` الأصلي، API compatible، لا إنشاء نسخة معاينة جديدة ولا rollback مدمر | Web+API HEALTHY، خطة compat، توثيق SHA ومعلومات النشر |
| G3 P0 | E2E دخول المشرف والطالب + تسجيل قراءة وقبلي/تسكين/دعم/بعدي ومسارات الأجهزة | browser screenshots + network/evidence/audit وخصوصية |
| G4 P0 | تدقيق DB backup/restore وقفل عناصر البيانات الحساسة والصوت وD26 gaps | backup proof، 409/503/422/403، latest audio |
| G5 P1 | إغلاق IA/UXA-01..18: Admin dashboard/reports/skills/media, student pages, status filters | حالات before/after بصور ومقاييس نجاح |
| G6 P0 | تأليف/توفير واعتماد الوسائط النهائية، المعايرة الأكاديمية وتوقيع العميل | 19 final video، الأصول كاملة أو قائمة نواقص وصلاحية إصدار واضح |
| G7 P0 | قبول العميل/المشرف، proof of V1-to-V2 parity وأداء وأمان وتقرير final release | `RELEASE_READY` فقط بعد لا P0/P1 وowner signoff |

**قاعدة الكفاءة:** تجميع إصلاحات صغيرة في دفعة ثم full QA مرة واحدة، مع فحص targeted عند كل إصلاح P0؛ لا إعادة Full Suite بعد كل تعديل CSS صغير. لا تصنع staging/branch جديد ولا تتجاهل فشل قديم.

## 12. حدود الاعتماد والمهام المطلوبة من المالك
- لا يطلب الآن إعادة إعطاء إجابة سبق حسمها: التسكين والدعم والبعدي آليون، صوت الطفل يراجعه المشرف، 6 قوالب بلا كتابة حرة، 7 تبويبات Student360، واجهة تعمل على الهاتف والديسكتوب، النشر على نفس المشروع.
- يلزم لاحقًا من المالك/العميل: تسليم أو اعتماد **الأصول التعليمية النهائية** (الصورة والصوت والفيديو والأمثلة والتشكيل)، اعتماد تربوي لسياسة تقدير القراءة/حدود الإتقان والتقوية مع أمثلة، واعتماد سياسة حفظ/محو/تصدير صوت الطفل والمدة المناسبة للبحث.
- للاختبار الحقيقي يلزم حساب مشرف/طفل **اصطناعيان** بأذونات سليمة في البيئة المنشورة ووسائط تجريبية مسموح استخدامها؛ لا تكتب رموزهما أو كلمات المرور داخل GitHub أو الوثائق. التحقق من backup/restore يحتاج صلاحية منفصلة أو دليل آمن من مالك PostgreSQL.
- مراجعة العميل النهائية تأتي بعد إثبات النتائج، لا تُفترض من الموافقة على اتجاه التصميم أو طلب النشر.

## 13. ملفات مرجعية يجب أن يقرأها أي وكيل/محادثة جديدة
1. **هذا الملف** (أحدث حقيقة وتسليم): `docs/v2/agent-ops/HIMMA_V2_MASTER_STATUS_GAPS_REMAINING_WORK_HANDOFF_20261028_AR.md`.
2. القرار الأحدث: `docs/v2/DECISIONS_AR.md`، خصوصًا D22–D26، مع تصحيح D25 بالملحق D26.
3. `docs/v2/09_IMPLEMENTATION_ROADMAP_AR.md`، P09–P10 وP09-UX.
4. `docs/v2/work-owner/CURRENT_STATUS_AR.md`، سجل Work التاريخي (تغلب هذه الوثيقة على فقراته القديمة التي تصف عدم نشر API).
5. `docs/v2/agent-ops/HIMMA_V2_ADMIN_UX_AUDIO_REVIEW_AND_CONTENT_AUDIT_20261028_AR.md` — UXA-01..18 وقبول الصوت.
6. `docs/v2/agent-ops/WORK_BROWSER_ACCEPTANCE_MATRIX_20261027_AR.md` — مسارات الصفحات والأجهزة؛ السطر التاريخي «قرار المشرف يفتح المستوى» **منسوخ من ما قبل D26 ولا يعمل به**.
7. `docs/v2/56_P09_0_LIVE_UI_SOURCE_BASELINE_AND_GAP_REGISTER_AR.md` — P09-F01..14؛ `59_P09_0_VERIFIED_GATE_AND_P09_1_HANDOFF_AR.md` — baseline القديم الناجح لا بوابة الإصدار الحالي.
8. `docs/v2/25_V1_TO_V2_FEATURE_PARITY_REGISTER_AR.md` — F01..F36؛ `51_P08_P10_SUPERVISOR_STUDENT_UX_PLAN_AR.md`.
9. `docs/v2/53_V2_WORD_SENTENCE_BANK_CONVERSION_AR.md` — تحويل الـ21 سؤالًا؛ `55_P08_LAST_RECORDING_RETENTION_AND_REVIEWED_ARCHIVE_AR.md` — آخر تسجيل وسياسة الخصوصية.
10. `docs/v2/20_VERIFIED_CONTENT_BASELINE_AND_GAPS_AR.md` و`21_EXECUTION_PROGRESS_AR.md` — مرجع تأريخي **ليس تقرير الحالة الأحدث**.
11. `docs/v2/42_SUPERVISORY_CONTINUITY_WORK_RAILWAY_FULL_HANDOFF_AR.md` — تسليم إشرافي سابق، وبعضه أصبح متجاوزًا.

## 14. رسالة استلام مختصرة لأي وكيل يتابع مباشرة
> استلم هِمّة V2 من آخر حالة حقيقية وفق `docs/v2/agent-ops/HIMMA_V2_MASTER_STATUS_GAPS_REMAINING_WORK_HANDOFF_20261028_AR.md`. افحص GitHub branch HEAD وخدمات Railway لا تعتمد على التوثيق وحده. المستخدم يريد تصحيحًا جذريًا ونشرًا على نفس المشروع الموجود دون فرع معاينة. API منشور `d2046d0` وMigration 0029/0030 نجحت، لكن Web `e378575` FAILED عند Jest بعد تعديل اختبار Student360؛ آخر نجاح Web قديم `ad024302`. البداية P0 إصلاح عزل طالب A→B→A، تشغيل Jest 172/172 + ESLint + Next build وCI/M04/M09 ثم نشر Web وفحص مصادق للطالب والمشرف ومراجعة الصوت. بعده أغلق كل سجل F01..F14 وUXA-01..18 وF01..F36 (parity) والوسائط/P10، بمصفوفة evidence وSHA. لا تعد نجاح API نجاح Web أو قبول العميل، لا تستدعِ تدخل مشرف في التسكين، ولا تظهر V1 في المنتج، ولا تغير/تحذف بيانات أو تخفف الأمان لتجاوز الاختبار.

## 15. قائمة إنهاء الجلسة / قواعد تحديث هذا السجل
- بعد كل تعديل مهم: `symptom → root cause → source change → regression test → CI/run SHA → Railway deploy SHA → browser/DB proof → status`.
- بعد كل نشر: تأكد من مصدر release المثبت وصلاحية الطلاب الحاليين والقدامى، مخططات الترحيل/backup، فرق SHA المقصود، error logs/health، ولا تغيّر DNS/DB/أسرار للالتفاف على بوابات الفحص.
- إذا حدثت Deployments جديدة بعد تاريخ هذه الوثيقة، أضف فقرة مؤرخة، ولا تمحُ دليل فشل/إصلاح سابق.
- **المعيار النهائي:** 19 درسًا، 300 بندًا، 12 دعمًا، 30 قبلي/30 بعدي بحسب المصدر المثبت، دعم وتسكين/بعدي ذاتي، مراجعة صوت موثوقة، تقرير ومكافأة صادقان، 7 تبويبات Student360 سهلة، 6 تفاعلات، لا ماضي V1 ظاهر، صور/أصوات/فيديو نهائية معتمدة، 320–1440 وتكبير 200%، أمن وخصوصية وحفظ أدلة، قبول CI/M04/M09/browser/DB والمالك.
