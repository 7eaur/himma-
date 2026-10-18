# هِمّة V2 — فحص P01-C للوحة الطالب ورحلته التعليمية

**التاريخ:** 2026-10-18

**الحالة:** `ready_for_review_source_only` — لا اختبارات تشغيل/مرئيات جديدة ولا تعديل كود أو DB أو نشر

**فرع العمل:** `v2/01-learning-foundation-20261007`

**HEAD المفحوص قبل التوثيق:** `080505674889a7fc4e8a8220756892b7565bc37b`

**مرجع V1:** `stage/02-content` عند `4ecb27590f7c19cbe7823804b9919d91000415ef`

## 1. القرار التنفيذي المختصر

لوحة الطالب الحالية ورحلة V1 **ليستا مهملتين ولا تستبدلان بمنصة موازية**. نحافظ على: الدخول والعودة، إجراء أساسي واحد، التسكين، حالات المستويات، التقدم، التعليق المحايد للصوت، إعادة التسجيل المنفصلة، التقوية والعودة، المكافآت، النتائج، الشخصيات وهوية هِمّة. لكن لا يمكن توصيل بنك V2 بها بتغيير الأرقام فقط.

الفجوة الجذرية ذات الأولوية `P0` هي أن عقد الرحلة الحالي يبني التعلم على **جلسة core فيها 10 ContentItems لكل مستوى**، بينما عقد V2 المعتمد يبني المسار على **19 درسًا (6/6/7)**، وكل درس: `تمهيد → فيديو → تدريب → تحقق` مع استئناف داخل المرحلة. نماذج `AssessmentSession/Attempt/AttemptResponse` الحالية لا تمثل درس V2 ومرحلة الفيديو/التدريب/التحقق تمثيلًا صريحًا. الحل هو **توسيع نفس المنصة بعقد رحلة/تقدم دروس مُصدّر ومالك حالة واحد**، مع إعادة استخدام المصادقة، التسجيلات، المراجعة، المكافآت، idempotency، والتدقيق، لا نسخها.

## 2. نطاق الفحص ومنهجه

تمت قراءة مستندات V2 الحاكمة والبنوك الأربعة وسجلات UX التاريخية، ثم تتبع المسار من:

`student/page.tsx → BFF /api/* → FastAPI profile/journey/activity/adaptation/assessment → SQLAlchemy models/migrations → unit/E2E/visual tests`.

شمل الفحص حالات: قبل القبلي، جلسة قبلي نشطة، التسكين، core نشط، إكمال/تخطي/قفل مستوى، ترقية مبكرة، تقوية، صوت معلق، إعادة تسجيل، البعدي، الاكتمال، الخروج/العودة، الأخطاء، الهاتف/اللوحي/الديسكتوب على مستوى المصدر والاختبارات الموجودة.

**حد الإثبات:** لم تُشغّل V1 لأنها غير منشورة، ولم تُنشأ معاينة V2، ولم تُشغّل CI أو Playwright أو API/DB tests في هذه الجولة. كل نتيجة تشغيلية غير منفذة موسومة `NOT_VERIFIED`.

## 3. تصحيح لازم لحالة الفرع والتقارير السابقة

1. تقارير P01-A وP01-B صحيحة في قولها إن **جولات الفحص نفسها** لم تعدل Runtime. لكن فرع V2 ككل ليس `docs-only`: المقارنة الثلاثية مع V1 تعرض **83 ملفًا** و`60668 additions / 1942 deletions`، وتشمل محتوى وتغييرات Runtime/اختبارات سابقة.
2. ملفات P01-C المركزية التالية متطابقة بالـGit blob بين V1 وHEAD المفحوص: `student/page.tsx`, `student/layout.tsx`, `StudentRerecordTasks`, `StudentAdaptiveHoldOverlay`, `StudentActivityStateBoundary`, `protected.py`, `journey.py`, `activity_runtime.py`, `learning_state_machine.py`, `level_completion.py`, `assessment_completion.py`, `assessment_retake.py`, `reward_catalog.py`, `db/models.py`.
3. توجد فروقات Runtime ذات صلة يجب ألا تُنسب إلى هذا التدقيق: صفحة جلسة التقييم حسنت عرض stimulus المرجعي؛ صفحة النشاط أضافت `rerecord_available`؛ و`adaptation.py` قيد إشارات القرار إلى أدلة core. أضيف اختبار يمنع تصنيف إعادة التسجيل كإكمال مستوى.
4. لا توجد GitHub Actions runs لـHEAD؛ الحالة الخارجية الظاهرة `Vercel=failure` مرتبطة بحد المعدل، ولا تثبت سلامة التطبيق أو فشله الوظيفي. لذلك لا نكرر وصف اختبارات V1 التاريخية على أنها اجتياز V2.

## 4. ما يجب الحفاظ عليه من V1

| ID | القدرة المثبتة من المصدر | القرار لـV2 | دليل المصدر |
|---|---|---|---|
| C-K01 | لوحة طالب بهوية هِمّة واسم الطالب وإجراء أساسي واحد | `KEEP/REFINE` | `apps/web/src/app/student/page.tsx` |
| C-K02 | تسلسل قبلي → تعلم → بعدي، مع عرض التسكين والنتائج | `KEEP/EVOLVE` | `protected.py`, `journey.py`, `assessment_completion.py` |
| C-K03 | حالات مستوى `locked/skipped/ready/active/completed` | `KEEP SEMANTICS` وتطبيقها على 19 درسًا | `journey.py`, `student/page.tsx` |
| C-K04 | حفظ محاولات/إجابات، جلسة نشطة واحدة، وidempotency | `KEEP/EXTEND` | `db/models.py`, migration `0004`, `OperationIdempotency` |
| C-K05 | الصوت المعلق محايد أكاديميًا ولا يصبح رسوبًا/نجاحًا زائفًا | `KEEP` | `audio_review_state.py`, `activity_runtime.py`, `assessment_completion.py` |
| C-K06 | إعادة التسجيل مهمة مستقلة يحتفظ فيها بتاريخ التسجيل السابق | `KEEP/CONSOLIDATE UI` | `StudentRerecordTasks.tsx`, `activity_runtime.py` |
| C-K07 | التقوية والتحقق والعودة للمسار، وعدم الخفض التلقائي | `KEEP/EVOLVE` | `reinforcement_cycles.py`, `adaptation_runtime.py`, `learning_state_machine.py` |
| C-K08 | الترقية المبكرة مع حد أدنى ودليل إتقان | `KEEP POLICY CONCEPT` ثم معايرته لعقد الدروس | `learning_state_machine.py`, `level_completion.py` |
| C-K09 | المكافآت idempotent والشارات الرسمية الست | `KEEP/REFINE` | `adaptation.ensure_rewards`, `reward_catalog.py`, `public/assets/rewards/svg` |
| C-K10 | النتائج السابقة/الحالية قسم ثانوي لا يزاحم الإجراء التالي | `KEEP/REFINE` | `journey.py`, `student/page.tsx` |
| C-K11 | شخصيات boy/girl وأصوات التشجيع وRTL والاستجابة | `KEEP/QA` | مكونات الطالب وCSS والأصول التي ثبتت في P01-A |
| C-K12 | تفويض المشرف لإعادة القبلي/البعدي مع سجل رسمي | `KEEP` | `assessment_retake.py` |

لا يوجد `RETIRE_APPROVED` لأي قدرة في هذا النطاق.

## 5. خريطة الحالة الحالية من الدخول حتى الإكمال

| حالة المصدر | ما تعرضه/تفعله اللوحة | مالك القرار الحالي | ملاحظة V2 |
|---|---|---|---|
| لا قبلي مكتمل | زر بدء القبلي | `/profile.next_action=pretest` | يحافظ عليه ببنك 30 سؤالًا |
| قبلي/بعدي نشط | استئناف الجلسة؛ انتظار/إعادة تسجيل قد يعطل الإنهاء | `protected._assessment_display_status` | يلزم current action مميز لا `resume` عام فقط |
| قبلي مكتمل | المستوى الحالي وخريطة المستوى | `assessment_completion` + `/journey` | يلزم تسليم نتيجة تسكين صريح وقابل للاسترجاع |
| تعلم/core | استئناف جلسة أو `POST /activities/start` | `/profile` + `/activities/status` | يُستبدل مفهوم core الثابت بعقد درس/مرحلة، لا endpoint موازٍ دائم |
| مستوى مبكر/مكتمل | حالة completed وانتقال للمستوى التالي | state machine + journey | فصل إكمال الدروس عن mastery/early promotion |
| دعم/تعليق | Overlay أو خطأ/انتظار حسب المصدر | adaptation + مكونات عامة | توحيد مالك الحالة ورسالة الاسترداد |
| L3 مكتمل والبعدي مفعّل | زر البعدي | journey + قرار المشرف | الحفاظ على البوابة وعدم فتحه من الواجهة |
| بعدي مكتمل | اكتمال الرحلة ونتيجة | profile/journey | شاشة نهاية مختلفة عن نص التسكين |

## 6. الفجوات الجذرية والقرارات الهندسية

| ID/أولوية | المكان ووظيفة V1 | القصور والسبب الجذري | تأثير V2 والحل المقترح | اختبار الإغلاق |
|---|---|---|---|---|
| C01 `P0` | `activities.py`, `journey.py`, `adaptation.py`: `CORE_ACTIVITY_COUNT=10` وتقدم من أصل 10 | وحدة التقدم Activity ثابتة لا Lesson release | إنشاء عقد رحلة مُصدّر يقرأ 6/6/7 من content release ويعرض lesson IDs وحالاتها؛ إزالة الاستدلال الرقمي من الواجهة مع إبقاء منطق الأدلة | 19 درسًا بالترتيب، لا 10 وهمية، release pinning واختبار counts |
| C02 `P0` | `db/models.py`: Session→Attempt→Response تحفظ core item | لا حالة صريحة للدرس أو `intro/video/practice/check` ولا نقطة استئناف داخلها | توسيع مخطط V2 بـLessonSession/LessonProgress أو مكافئ داخل نفس DB والعقود؛ stable IDs وإصدار محتوى ومرحلة/عنصر حالي؛ إعادة استخدام idempotency والصوت | refresh/device resume عند كل مرحلة، migration up/down، لا duplicate progress |
| C03 `P0` | `student/page.tsx` يجمع profile/status/journey/rewards محليًا | مصادر متعددة وtypes مكررة؛ فشل بعضها ينتج لوحة متناقضة | مالك خادمي واحد لـStudent Home/Journey Projection أو DTO موحد versioned يحوي `current_action`, progress, holds, rewards summary؛ shared generated types | contract + partial failure + stale version tests، لا جمع حالات أكاديمية في React |
| C04 `P1` | اللوحة و`StudentRerecordTasks` يجلبان مهام التقييم؛ المكوّن العام يجلب profile كل 4 ثوانٍ | ازدواج عرض/طلبات وملكية مهمة إعادة التسجيل | Task Center/Projection واحد ومكوّن عرض واحد؛ revalidation مضبوط/backoff بدل polling دائم؛ يحافظ على فتح المهمة اختيارياً | core/pre/post tasks، 0/1/many، لا بطاقتين ولا profile request مكرر |
| C05 `P1` | صفحة النشاط و`StudentActivityStateBoundary` يقرآن `rerecord_available` | مالكا توجيه وطلبان قد يتسابقان | current action/navigation owner واحد، والBoundary لعرض loading/error فقط أو يحذف بعد نقل مسؤوليته | refresh على rerecord، Back، رابط مباشر، لا redirect loop |
| C06 `P1` | `StudentAdaptiveHoldOverlay` يستطلع كل 1.8 ثانية ويستنتج `mapping_gap` | polling عالمي صامت الفشل وحالة blocker موزعة | تضمين hold machine-readable في current action؛ تحديث يدوي/حدث أو backoff وvisibility؛ رسالة وعودة محفوظة | mapping gap/resolve/401/500/offline، قياس عدد الطلبات |
| C07 `P1` | اللوحة تتجاهل غالب فشل journey/status وتستخدم fallbacks | الصفر وunavailable غير متميزين؛ hero قد يقول تعلم والخريطة قبل القبلي | حالة `loading/ready/degraded/error` صريحة مع Retry؛ لا عرض تقدم مختلق؛ telemetry/request-id | فشل كل endpoint منفردًا ومجتمعًا، استعادة بعد الشبكة |
| C08 `P1` | journey يعرض completed items من 10 والترقية المبكرة بعد 6 | إكمال مستوى/إتقان/تخطي تختلط في عداد واحد | Progress V2 يفصل `lessons_completed`, `mastery_evidence`, `support_pending`, `promotion_reason`; يشرح skipped بلا وصم | تسكين L2/L3، ترقية مبكرة، مستوى مكتمل كاملًا، نسب صحيحة |
| C09 `P1` | إكمال القبلي يعيد assigned_level واللوحة تعرض مستوى عامًا | نتيجة التسكين تعتمد على انتقال لحظي ولا توجد handoff durable واضحة | PlacementOutcome في journey/history مع رسالة مرة واحدة قابلة للاسترجاع وسبب مناسب للطالب دون كشف scoring | إغلاق/refresh مباشرة بعد القبلي، L1/L2/L3، صوت معلق |
| C10 `P1` | `student/session/[id]/page.tsx` يعيد لغة “المسار المناسب/المستوى” للقبلي والبعدي | reuse عرضي لا يميز هدف البعدي | outcome component مميز بحسب session_type؛ البعدي يلخص اكتمال الرحلة ولا يعيد تسكين الطالب | قبلي/بعدي snapshots وcopy assertions ونتيجة محفوظة |
| C11 `P1` | أسماء المستويات والنصوص والأعداد hardcoded في React/Python | metadata موزعة وتنجرف عن البنك | level/lesson presentation metadata من release/API، مع stable keys؛ إبقاء أسماء الدوال القديمة ما لم يحتج العقد تغييرًا واضحًا | تغيير fixture metadata بلا تعديل UI، Arabic plural/count tests |
| C12 `P1` | زر البدء يحمي بنقرة عبر state محلي، والـDB يمنع جلستين | الحماية جيدة خادميًا لكن لا دليل لتبويبين/نقرتين في V2 | الحفاظ على unique active session وidempotency وإرجاع الجلسة القائمة بصورة موحدة | double-click، tabين، retry بعد timeout، refresh بعد commit |
| C13 `P1` | `next_action` خمس قيم و`resume` عام | لا يمثل lesson phase/support/audio/supervisor hold بدقة | discriminated `CurrentAction` واحد: assessment, lesson stage, support, pending review, rerecord, supervisor hold, posttest, complete | exhaustive schema/type tests وكل انتقال مسموح/مرفوض |
| C14 `P1` | mapping/escalation تظهر أحيانًا 409 نصيًا وأحيانًا overlay | taxonomy وownership غير متسقين | Problem Details/أكواد ثابتة + current action recoverable؛ نص الطفل غير مشتق من detail الخام | mapping_blocked/verification_escalated/503، رسالة آمنة وCTA صالح |
| C15 `P1` | E2E تاريخي يغطي رحلة لكن `w6-same-student-journey` يصنع history بسكربت | لا اختبار حالي يمر فعليًا بـ19 درسًا ومراحلها؛ لا CI على HEAD | journey E2E حقيقي على V2 fixtures، مع suites سريعة للعقد وسياسة، وتفعيل CI لـ`v2/*` | المسار الكامل + support + audio + resume، run/sha حديثان |
| C16 `P2` | تقدم بصري وjourney track في اللوحة | دلالات progress/focus/live لم تُثبت بالكامل؛ track مخفي قارئياً | semantic progressbar/steps، focus واضح، status live غير مزعج، reduced motion | axe/keyboard/zoom/screen reader على 360/390/tablet/desktop |
| C17 `P2` | layout يستطلع profile كل 4s وadaptation كل 1.8s واللوحة تجلب 3–5 مصادر | حمل دائم وتكرار على كل صفحات الطالب | projection/cache/revalidation موحد، backoff عند الخلفية/الفشل، قياس budget | request budget، slow 3G، tab hidden، 30 دقيقة جلسة |
| C18 `P1` | `StudentExperienceEffects` يحفظ تفضيل الصوت محليًا | المؤثرات محفوظة لكن لا تحكم واضح مثبت في رحلة الطالب | إبقاء التعزيز وتوفير تحكم صوت/حركة مناسب للطفل مع إعداد محفوظ وإتاحة | toggle صوت، refresh، reduced motion، لا تداخل أصوات |

## 7. أثر بنك V2 على الرحلة

- الأعداد المعتمدة: 19 درسًا (`L1=6`, `L2=6`, `L3=7`)، 12 دعمًا، 300 بند، و7 أنواع تفاعل.
- الـ62 `read_aloud` والـ21 `write_text` يمنعان تعريف تقدم الدرس على أنه “أجبت فورًا”؛ يلزم فصل `submitted/pending_review/accepted/rerecord_required` عن mastery.
- 19 فيديو غير متوافرة نهائيًا الآن؛ استئناف الدرس يجب أن يحفظ موضع/اكتمال الفيديو وفق سياسة واضحة مع fixtures `TEST_ONLY`، ولا يتجاوز الفيديو تلقائيًا.
- 4 حالات صوت اختيار و11 media flags تمنع إطلاق production، لكنها لا تمنع تصميم عقد progress الآن.
- الدعم يعود إلى نقطة درس محفوظة؛ لا ينشئ مسار مستوى ثانٍ ولا demotion تلقائيًا.

## 8. مقارنة التصميم والاستجابة والهوية

مصدر اللوحة يحافظ على Hero، خط الرحلة، بطاقات المستويات، المكافآت، النتائج، شخصيات هِمّة، RTL، ونقاط استجابة CSS. هذه عناصر `KEEP/REFINE`. لا يوجد دليل تشغيل حالي يثبت الترتيب أو عدم overflow على HEAD.

الفحص المرئي المطلوب لاحقًا لكل حالة رئيسية: 360/390/430px، tablet portrait/landscape، وdesktop؛ مع نص طويل، اسم طالب طويل، 0/عدة مكافآت، خطأ API، pending/rerecord، locked/skipped/active/completed، ودعم. اختبار `ux-system-visual-qa` الحالي يلتقط أساسًا طالبًا جديدًا قبل القبلي، فلا يغلق الحالات الأخرى.

## 9. مصفوفة الاختبارات المطلوبة لـP01-C

| ID | السيناريو | النوع | الحالة الآن |
|---|---|---|---|
| C-T01 | طالب جديد → 30 قبليًا → تسكين L1/L2/L3 → نتيجة durable | API+E2E | `NOT_VERIFIED` |
| C-T02 | دخول وخروج/Back/Refresh ثم استئناف الإجراء نفسه | E2E+Security | `NOT_VERIFIED` |
| C-T03 | درس: تمهيد→فيديو→تدريب→تحقق مع refresh بكل مرحلة | API+E2E | غير ممكن بالعقد الحالي |
| C-T04 | 19 درسًا 6/6/7 دون عداد 10 قديم | Contract+E2E | غير ممكن بالعقد الحالي |
| C-T05 | دعم من نفس المستوى/سابق ثم عودة للدرس الأصلي | Policy+E2E | `NOT_VERIFIED` |
| C-T06 | pending audio محايد مع استمرار ما تسمح به السياسة | API+E2E | تغطية V1 جزئية؛ V2 `NOT_VERIFIED` |
| C-T07 | rerecord core/pre/post مرة واحدة بلا خطف المسار | API+E2E | تغطية مصدر/وحدات جزئية |
| C-T08 | ترقية مبكرة ومكافأة مرة واحدة | Unit+API+E2E | V1 تاريخي جزئي؛ V2 `NOT_VERIFIED` |
| C-T09 | فشل profile/journey/progress/rewards منفردًا ثم Retry | Component+E2E | غير مغطى كفاية |
| C-T10 | نقرتان/تبويبان/start timeout لا ينشئون جلستين | Integration | `NOT_VERIFIED` |
| C-T11 | mapping gap/escalation/resolve مع CTA آمن | API+E2E | `NOT_VERIFIED` |
| C-T12 | البعدي لا يعيد التسكين وتظهر نهاية رحلة صحيحة | API+E2E+Visual | `NOT_VERIFIED` |
| C-T13 | مزامنة تقدم بين هاتف وديسكتوب | Integration+E2E | `NOT_VERIFIED` |
| C-T14 | 360/390/430/tablet/desktop لكل حالات اللوحة | Visual+axe | فقط حالة أولية تاريخية |
| C-T15 | keyboard/focus/progressbar/live/reduced-motion/audio-toggle | Accessibility | `NOT_VERIFIED` |
| C-T16 | request budget وpolling في foreground/background/slow network | Performance | `NOT_VERIFIED` |
| C-T17 | محتوى release تغير مع جلسة قديمة pinned | Integration | `NOT_VERIFIED` |
| C-T18 | مكافآت/نتائج/الشخصيات والأصول لا تختفي بعد refactor | Parity+Visual | `NOT_VERIFIED` |

## 10. ترتيب التنفيذ المقترح دون بدء البرمجة

1. في P02: اعتماد DTO موحد للـJourney/CurrentAction ومخطط تقدم الدرس وإصدار المحتوى؛ حماية migration/idempotency/session uniqueness.
2. في P03: توصيل لوحة الطالب ومشغل الدرس بالعقد نفسه مع fixtures واختبار الاستئناف.
3. في P04–P05: أنواع التفاعل، evidence، الدعم والصوت/الكتابة دون نسخ state machine.
4. في P06–P08: البعدي، المشرف، التقارير، المراجعة والمكافآت على نفس IDs وحالات التقدم.
5. في P09: تنفيذ C-T01–C-T18 وFxx/RGxx على HEAD حديث؛ P10 للأصول النهائية والقبول المرئي/السمعي والنشر.

هذا ترتيب تخطيطي فقط؛ **P01-D لم تبدأ وP02 لم تبدأ**.

## 11. حالة التسليم

- `P01-C = ready_for_review_source_only`.
- الفجوات المفتوحة: `C01–C18`؛ الأولويات الحرجة `C01–C03`.
- لا فقد ميزة معتمد، ولا تغيير كود أو DB أو بيئة نشر.
- P00 وP01-A/B لم يُعاد فتحهما، لكن صححنا وصف الفرع وأضفنا اختبارات تمنع إسقاط أدلتهما.
- ننتظر مراجعة المالك وقوله **«تم»** قبل أي عمل في P01-D.
