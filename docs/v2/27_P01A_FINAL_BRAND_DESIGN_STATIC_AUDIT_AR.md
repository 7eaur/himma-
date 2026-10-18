# هِمّة V2 — P01-A: التقرير الختامي لفحص الهوية والأصول ونظام التصميم من المصدر

**التاريخ:** 2026-10-19  
**الحالة:** `ready_for_review_source_only` — **اكتمل نطاق التدقيق الثابت الذي يمكن إثباته من GitHub**؛ الاختبارات البصرية والسمعية وتشغيل UI/Build لا تزال **NOT_VERIFIED** وتنفذ إلزاميًا ضمن المراحل البرمجية، وليست نتيجة لهذا التقرير.  
**المشروع:** تحديث **نفس** هِمّة V1 إلى V2 داخل `7eaur/himma-`، فرع العمل `v2/01-learning-foundation-20261007`.  
**المراجع:** `25_V1_TO_V2_FEATURE_PARITY_REGISTER_AR.md`، `26_V1_IDENTITY_PAGES_AND_FIXED_REGRESSIONS_AUDIT_AR.md`، وحزمة الهوية `assets/brand/ASSET_MANIFEST.json`.  
**ملحوظة:** V1 ليست منشورة؛ لم نصل إلى قاعدة طلاب أو ننفذ نشرًا أو نغير الأصول أثناء الفحص.

## 1. أدلة فحص الملفات مباشرة

| ID | العنصر | نتيجة مؤكدة من المصدر | الحكم |
|---|---|---|---|
| A01 | حزمة الهوية الرسمية | `ASSET_MANIFEST.json` يسجل **48** ملفًا؛ جرت مطابقة مسارات **48/48** مع شجرة Git و**48/48** أحجام ملفات مع قيم Manifest دون اختلاف. **لم تُحسب SHA256 للأصول الثنائية** ولم تُفحص بصريًا. | `SOURCE_PRESENT` |
| A02 | نسخ شعار الواجهة | الأربع `logo-{gradient,flat,white,navy}.svg` في `apps/web/public/brand/` مطابقة **بتطابق Git blob SHA** للنسخ الرسمية `assets/brand/assets/logo/svg/himma-logo-*.svg`. | `SOURCE_IDENTICAL` |
| A03 | أيقونات الهوية / PWA | يوجد بالـ48 manifest رموز favicon وapple-touch وPWA في `assets/brand/assets/icons/`، لكن مجلدات التطبيق المرصودة لا تعرضها كلها مباشرة في `apps/web/public`؛ يوجد `apps/web/src/app/favicon.ico`. هذا **نقص تحقق في ربط الأيقونات وليس إثبات كسر**؛ يشترط فحص `metadata/icons` و`webmanifest` قبل اعتبار تطبيق PWA متاحًا. | `VERIFY_INTEGRATION` |
| A04 | الشخصيات | **10 PNG** من `public/characters/boy` و`girl`، لكل شخصية `welcome/explain/encourage/success/try-again`. الوجود مؤكد وليس فحص جودة/أبعاد بعد الرندر. | `KEEP + VISUAL_QA` |
| A05 | شارات المكافآت | **6 SVG** تحت `public/assets/rewards/svg/`؛ `CanonicalRewardBadge.tsx` يعرض `assetPath` ديناميكيًا؛ يجب بقاء catalog والحدث الفعلي مع الاختبار. | `KEEP + PARITY` |
| A06 | صوت التعزيز | **4 MP3** `fb-complete/correct/encourage/wrong` في `public/audio`؛ لم نستمع إلى الملفات ولا نحكم بمستواها أو ضرورة إعادة تسجيلها. | `KEEP + AUDIO_QA` |
| A07 | أصوات وصور التعليم من V1 | البنك الجديد يختار **33 MP3 + 23 WebP** لإعادة الاستخدام؛ **56/56 مصدرًا موجودًا** في شجرة Git. هذه بيانات تعليمية لا تسجيلات الطلاب السابقة. | `PRESENT_PENDING_REVIEW` |
| A08 | أصول V2 التي لم تُوفر | **19 فيديو + 14 ملف صوت جديد** بحالة `missing_new` في بنك الـ89 أصلًا، ولا توجد صور معلّمة `missing_new` في نسخته الحالية؛ الصور الموجودة قد تحتاج استبدالًا بعد QA. | `PRODUCTION_BLOCKER_NOT_CODE_BLOCKER` |
| A09 | درجات العلامة الرسمية | الأزرق `#347FD9`، الأخضر `#51B985`، الأصفر `#FFC857`، الكحلي `#20364D`، خلفية `#F7FBFF` وحدود `#DCE8F2` موجودة في الحزمة و`globals.css`. | `KEEP` |
| A10 | درجات التباين | `accessibility.css` يعيد تعريف `--color-primary` إلى `#2466B8` و`--color-green` إلى `#217A55` لأغراض التباين؛ اختلاف مثبت بين ملفات CSS **ليس تلقائيًا خطأ مرئيًا**، ويحتاج نظام tokens دلالية (brand/accent/text-on-light) وتدقيق computed styles. | `DESIGN_DEBT_P1` |
| A11 | تباين لوحة الاختبار | `session/[id]/session.module.css` يستخدم `--task-blue:#1478f2` و`--task-navy:#07153a` بخلاف درجات الحزمة/الأنشطة، بينما `activity.module.css` يكرر `--blue:#347fd9`. الدرجات المرصودة ليست كلها خطأ؛ يلزم توحيد مبدأ tokens وبيان الاستثناءات. | `DESIGN_DRIFT_P1` |
| A12 | الخطوط والتبعيات | `layout.tsx` يستخدم `next/font/google` لـTajawal وIBM Plex Sans Arabic، و`fonts.css` يربط متغيراتهما. `globals.css` يتضمن `@import fonts.googleapis.com` **لكن** `postcss.config.mjs` يحمل `postcss-strip-google-fonts.cjs` الذي يزيل أي `@import` يحوي `fonts.googleapis.com`. يوجد `font-loading.spec.ts` يختبر عدم إرسال طلبات runtime. | `STRIP_RULE_PRESENT`؛ **لا ندعي وجود تحميل مزدوج دون تشغيل build/network** |
| A13 | ملف CSS الجذري | `globals.css` طوله **50,313 حرفًا / 1,763 سطرًا**، وفيه وظائف تصميم من مجالات متنوعة؛ تبسيطه يجب أن يحافظ على layout والتفاعلات القديمة. | `REFACTOR_CANDIDATE_P1` |
| A14 | طبقات CSS التصحيحية | `ux-corrections.css` ~9.9KB ويحوي **80 `!important`**، و`ux-student-surfaces.css` ~2.6KB فيه **29 `!important`**. `student-dashboard-corrections.css` ملف تصحيحي إضافي. هذا **تعقيد صيانة مثبت** وليس دليلًا وحده على خلل ظاهر. | `ROOT_REFACTOR_P1` |
| A15 | الأنظمة المحسّنة الموجودة | `student/question-system.css` (8.7KB) و`student/dashboard-system.css` (12.9KB) و`admin/(dashboard)/admin-workflow.css` (16.7KB) تمثل عمل V1 السابق لتحسين السؤال والرحلة والمراجعة؛ لا تُزال حتى تنتقل قدراتها إلى نظام تصميم موحد وتنجح regression. | `KEEP_BEHAVIOR` |
| A16 | الحركة والحساسية | `accessibility.css` و`reduced-motion.css` يحتويان قاعدتين متداخلتين لتفضيل الحركة المنخفضة؛ الثانية تحفظ scroll reveal ظاهرًا. لا نحذف واحدة قبل فحص أثرها على الدخول والعناصر. | `DEDUP_AFTER_QA` |
| A17 | العلامة في الواجهات | `layout.tsx` يحدد `lang=ar`, `dir=rtl`؛ `page.tsx`, `student/login`, `student/page`, `student/activity`, `student/session`, `admin/login`, `admin/layout`, `StudentAdaptiveHoldOverlay`, `StudentActivityStateBoundary` تستدعي أصولًا صحيحة من المسارات الثابتة المفحوصة. | `SOURCE_REFERENCES_MAPPED` |
| A18 | تغيير الأسماء/المسارات | مقارنة V1→V2 توضح حذف أسماء الصور العلوية `public/characters/boy-*.png` مع بقاء الصور المقابلة في `public/characters/boy/*.png`، وكذلك إزالة `StudentAudioReviewOverlay.tsx` القديم. لا إثبات فقد مرئي/وظيفي، لكن يجب تتبع أي رابط قديم قبل حذف alias أو إصلاحه. | `REGRESSION_RISK_P1` |
| A19 | مراجع الأصول من API | صور الأسئلة والخيارات تعتمد media assets من API وليس فقط URLs ثابتة. وجود WebP/MP3 المصدر لا يثبت صحة `/api/media/{id}` ولا نطقها. | `MEDIA_CONTRACT_QA_P02/P07` |
| A20 | اختبارات regression التاريخية | `font-loading.spec.ts` يفحص منع Google runtime request، `media-fidelity.spec.ts` يفحص بايتات الصور/الصوت واستعدادها، `reward-lifecycle.spec.ts` يفحص بقاء الشارة بعد التحديث، و`ux-system-visual-qa.spec.ts` + Responsive/axe files تغطي صفحات وحالات. | `TEST_SOURCES_PRESENT` — **لا تدعي نجاحها على V2** |

## 2. خريطة الأصول التي يستخدمها التطبيق فعلًا

| نطاق | الاستدعاءات الرئيسية في V2 | يحفظ أثناء التحديث |
|---|---|---|
| العامة `/` | `logo-gradient`, `logo-navy`, `girl/welcome` | Logo + Landing Artwork |
| `/student/login` | `logo-gradient`, `boy/welcome` | شخصية دخول الطالب |
| `/student` | `logo-gradient`, `girl/{welcome,explain,encourage,success}`, شارات ديناميكية | حالات الرحلة، النجاح، المكافآت |
| `/student/activity/[id]` | `logo-navy`, `girl/{explain,encourage}`, صور الأسئلة من API | التعلم، التشجيع، صور النشاط |
| `/student/session/[id]` | `logo-navy`, `girl/{explain,encourage}`, صور الخيارات من API | الاختبارات والقراءة والانتظار |
| `/admin/login` | `logo-white`, `logo-navy`, `girl/welcome` | تباين الشعار وتوزيع عناصر الدخول |
| `/admin/*` | `admin/layout.tsx` يستخدم `logo-navy` مع `AdminNotifications` | هوية موحدة للمشرف وشريط التنقل |
| `StudentAdaptiveHoldOverlay` | `girl/encourage` | حالة التوقف/الدعم |
| `StudentActivityStateBoundary` | `logo-navy` | حالات الخطأ/الانتظار |
| `CanonicalRewardBadge` | مسار أصل من rewards catalog | مكافآت حقيقية دون hard-code |
| `/characters/girl/idle.png` | Redirect 307 إلى `girl/welcome` | Fallback القديم حتى التحقق من مستهلكيه |

**حدود الخريطة:** مسارات JSX الثابتة والمكونات الأساسية موثقة، لكن مراجع CSS المعقدة والروابط الديناميكية التي تولدها خدمة المحتوى تحتاج فحص تنفيذ/عقود P02/P03؛ **لا نعلن أن كل صورة تُعرض بنجاح دون معاينة**.

## 3. القرارات الهندسية المطلوبة لتنفيذ V2 — جذرية لا ترقيعات

1. **الهوية ثابتة**: `Brand Asset Kit 1.0` هو المرجع للشعار والألوان والأيقونات والشخصيات؛ تحسين العرض وليس تصميم هوية بديلة.
2. **Tokens دلالية واحدة**: فصل `brand-blue` عن `text-link-on-light` و`focus-visible` و`task-accent`، مع سياسة تباين WCAG وبلا إعادة تعريف مربكة لنفس المتغير في أكثر من ملف عام.
3. **ملفات CSS بحسب المسؤولية**: `foundation/tokens` + UI primitives مشتركة للطالب والمشرف + styles خاصة عندما تكون الوظيفة خاصة؛ نقل إصلاحات سؤال الطالب وDashboard ومراجعة الصوت بعد قياسها، **ثم** إزالة الطبقات التصحيحية المُستغنى عنها بأدلة regression، لا حذف جماعي.
4. **الخط**: الحفاظ على Tajawal/IBM مع `next/font` والتحقق من عمل plugin والناتج/شبكة المتصفح. إزالة الاستيراد التاريخي نهائيًا **فقط بعد اختبار**؛ لا نقرر وجود bug غير مثبت.
5. **مصدر asset ثابت واضح**: Manifest/MediaProvider للتعليم والصوت والشارات، وعدم تحويل صوت الطالب الشخصي السابق إلى أصل محتوى، وعدم استخدام `placeholder` في إنتاج درس.
6. **أيقونات PWA والـfavicon**: تثبيت ما إذا كانت PWA جزءًا مقصودًا وموجودًا فعليًا من V1؛ إن كانت كذلك نفحص `webmanifest` وIcon URLs/Android/Apple ونعيد توصيل الأصول الرسمية بدل اعتبار وجود ملفات في جذر المستودع كافيًا.
7. **قواعد عدم تراجع V1**: الحفاظ على النص والحاوية المرنين، خيارات الصور، Dashboard الحقيقي، تراكب الشخصيات، Audio Queue، إشعارات المشرف المجمّعة، الشارات، reduced motion، RTL، focus/keyboard.
8. **كل تغيير سابق (RG01–RG25) له test ID**، وتثبت النتيجة على نسخة V2 في مراحل التنفيذ، لا يُكتفى بوجود ملف الاختبار أو مرور QA تاريخي.

## 4. مصفوفة تحقق لاحقة ملزمة (ليست نتائج اختبارات منجزة)

| المرحلة | الاختبار | شروط النجاح |
|---|---|---|
| P02 | `ASSET_MANIFEST.json` validator | مسارات وتوافق أحجام، وapproved logo blob lineage، ووجود media identifiers وإمكان تبديل الـprovider |
| P02/P03 | Brand/metadata smoke | عدم فقد شعار أو شخصية أو أيقونة متوقعة؛ عدم كسر مسارات fallback أو شارات المكافأة |
| P03 | Visual Desktop/Mobile | صور حالات صفحة عامة ودخول الطالب والمشرف ولوحة الطالب والفيديو والدعم والمراجعة على 360/390/430/768/1440 |
| P03 | CSS refactor regression | كل RG المعنيّة + non-overflow/zoom/RTL/contrast/focus/reduced-motion، وتدقيق computed tokens |
| P03 | Build + font network | `next build` ثم Playwright `font-loading.spec.ts` للتأكد من عدم طلب Google Runtime ومن الاستقرار البصري الفعلي |
| P04/P05 | Interactions/rewards/audio | `question-experience`, `media-fidelity`, `reward-lifecycle`, `useAudioQueue` وRegression حالات الإنتظار/الدعم |
| P07/P10 | Audio/Image/Video QA | فحص بشري حقيقي لـ56 وسائط مرشحة و33 أصلًا جديدًا، الحقوق والنطق/الشدة/التشكيل والدلالة والحجم، وربط ID→URL |
| P09 | Page parity + full journey | Screenshots للواجهات، التقدم والمشرف والتصدير؛ إغلاق I/PG/RG/F matrices بلا P0/P1 مفتوحة |

## 5. بوابة P01-A

**الذي يمكن قبوله الآن:** تم جرد حزمة العلامة (48 ملفًا/48 حجمًا)، ومقارنة blobs الشعارات 4/4، وجرد الشخصيات 10/10، الشارات 6/6، الأصوات التعزيزية 4/4، وملفات التعليم المرجحة 56/56، وقراءة طبقات CSS وقواعد الخطوط ومقارنة استخدام الأصول في الواجهات الأساسية. هناك خطة جذرية مرتبة وفحوص مستقبلية محددة.

**ما لا يجوز الادعاء بأنه مكتمل الآن:** اختبار تصميم V2 في متصفح فعلي، أو الاستماع إلى MP3، أو معاينة SVG/PNG/WebP بصريًا، أو اختبار Load/CLS/Contrast، أو نجاح Playwright/CI، أو صحة مسارات MediaProvider الحية، أو جاهزية نشر V2. هذه شروط تنفيذ مرحلية لا متطلبات إعادة نشر V1.

**القرار:** `P01-A = ready_for_review_source_only`. **لا انتقال لـP01-B قبل موافقة «تم»**. قبول هذا الجزء يعني قبول جرد المرجع وقائمة إصلاحات التصميم قبل البرمجة، **ولا يعفي** من نجاح Visual/Audio QA في P03/P07/P09/P10.
