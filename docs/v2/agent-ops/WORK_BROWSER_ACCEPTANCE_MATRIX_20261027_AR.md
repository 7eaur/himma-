> **تحديث التسليم والقبول 2026-10-28:** ارجع إلى [سجل جميع المهام والمشاكل والحالة المنشورة الفعلية](HIMMA_V2_MASTER_STATUS_GAPS_REMAINING_WORK_HANDOFF_20261028_AR.md). API الجديد منشور ومرّ ترحيل 0029/0030؛ Web الجديد فشل في آخر بناء؛ فحوص المتصفح أدناه **قائمة عمل مفتوحة لا نتائج نجاح**. يشمل نطاق الفحص أيضًا `/admin/v2-review-center` بثلاثة تبويبات، Student360 السباعي، rubric الرقمية وأرشيف آخر صوت، وتصفية وسائط 12 بطاقة.

# مصفوفة اختبار Work الفعلي — واجهات هِمّة V2 المنشورة
**Target:** https://himma-web-production-eafd.up.railway.app  
**النسخة:** رصد SHA/runtime قبل وبعد كل دفعة. **المالك يريد فحصًا تفاعليًا حقيقيًا من متصفح Work**، لا مراجعة لقطات GitHub وحدها.

## تسجيل الأدلة
لكل صفحة: `route | device/viewport | login-role | state | action | HTTP/status | screenshot/trace | expected | observed | P0/P1/P2 | commit-fix | test-SHA | reverified-live`.
اجمع لقطات بعد مصادقة اختبارية فقط، مع تنقيح الأكواد/البيانات الشخصية قبل المشاركة. لا تتعامل مع 200 وحدها كدليل عمل الزر؛ افتح الزر وتحقق من أثره الخادمي الصحيح.

## 1. المشرف: كل الـ15 صفحة ومسار
| route | اختبارات وظيفية مطلوبة |
|---|---|
| `/admin/login` | دخول وخروج وفشل دخول وsession expiry ورجوع للتسجيل، laptop + iPhone |
| `/admin` | لوحة V2 لا V1: مؤشرات صحيح/0/partial/error، حالات التسكين والقراءة والدعم من مصدر V2، لا access_code ظاهر |
| `/admin/account` | معلومات الحساب والتغيير/الحماية/جلسة/صلاحيات بدون أسرار |
| `/admin/students` | بحث وفلترة وفرز وتقدم 19 درسًا لا أنشطة V1، إخفاء الرمز عند كل حجم |
| `/admin/students/new` | إنشاء طالب اختبار جديد، كود صحيح، عدم إنشاء سجل V1 يعرقل القبلي، double-submit |
| `/admin/students/[id]` | Student360: جلسة/تسكين/دروس/دعم/أصوات آخر مراجعة/درجات رسمية/عدم ظهور جواب أو رمز افتراضي؛ switching profile A→B→A |
| `/admin/v2-assessments` | pending/approved/retake/placement، الموافقات والتفويض والأخطاء، عدم تكرار العمل |
| `/admin/v2-lesson-review` | دروس/قراءة/انتظار/رد/إعادة، آخر صوت معتمد فقط وسلامة الصلاحيات |
| `/admin/v2-reviewed-recordings` | approved / rejected / empty / error، playback مصادق وآمن و403 لطالب آخر |
| `/admin/audio-review` | حصر V1 بأرشيف staff-only أو redirect آمن دون عرضها كقسم منتج V2 |
| `/admin/content-preview` | بيانات 300 سؤال V2 متسلسلة + نوع وخيارات وصوت/صور وأجوبة للمشرف فقط/لا تعرض للمستخدم العادي |
| `/admin/v2-media` | معرض 89 أصلًا وفلاتر+معاينة صوت/فيديو/صورة وحالة واعتماد كل أصل وحماية TEST_ONLY وRTL بلا overflow |
| `/admin/reports` | تقارير V2 المعتمدة، pre/post، تقدم، دعم، توزيع مستويات، exports فعلية PDF/Excel، أرشيف V1 منفصل |
| `/admin/skill-reports` | مصادر أدلة مهارات V2 الرسمية، نطاق/نسخة/empty/error/Excel وعدم نسب V1 للتلميذ |
| `/admin/settings` | RBAC ومشرفون/أدوار ومفاتيح تغيير دون كشف أسرار أو تغيير إعدادات نشر |
**أي صفحة إضافية أو زر/مودال أو hidden tab يكتشفها Work يدخل المصفوفة، لا يكتفي بهذا الجرد.**
## 2. الطالب: كل الـ7 صفحات
| route | اختبارات وظيفية مطلوبة |
|---|---|
| `/student/login` | رمز صحيح/خاطئ، حماية brute-force، session/logout ودخول مستخدم ثان |
| `/student` | أول دخول حقيقي → البدء القبلي، رجوع/انتظار/retry، progress/rewards V2 فقط، لا migration_review لحساب جديد بلا تاريخ |
| `/student/assessment-v2/[sessionId]` | جميع مراحل قبلي وبعدي، تسلسل 1/30 .. 30/30، role/ownership/GET/POST/ACK lost/401/409/503/reload/duplicate |
| `/student/learning-v2` | الـ19 درسًا وحالات locked/current/done/skipped, دعم تلقائي، منع التقدم الوهمي |
| `/student/learning-v2/[sessionId]` | تمهيد+فيديو+تدريب+اختبار+صوت+تلميح+دعم ثم استئناف/انقطاع/مراجعة |
| `/student/activity/[id]` | تأكد أنه V1 تاريخي لا يمكن للطالب الجديد دخوله أو يجرّه لمسار قديم؛ redirect/guard مناسب |
| `/student/session/[id]` | نفس حاجز legacy، لا يظهر تقدم V1 أو نقاطه في V2 |
## 3. الحسابات والتجارب
- **N:** طالب أُنشئ الآن من المشرف، لم يبدأ أي تقييم؛ يجب أن يعرض `start_pretest` فعليًا. لا تبدأ بجلسة موجودة ثم تسميه جديدًا.
- **L:** طالب V1 تاريخي فعليًا (أو fixture), رحلة غير موجودة وتقييم سابق؛ لا تقم بإتلاف evidence أو بدء قبلي جديد بلا تفويض.
- **P:** طالب قبلي في progress answered=1 ثم refresh؛ لا تكرار لسؤال/إجابة.
- **R:** قبلي waiting_review/placement_pending_review؛ **المشرف يراجع الصوت فقط**؛ وبعد استكمال آخر مراجعة صوتية معتمدة يُحسب المستوى تلقائيًا ويصدر قرار `PlacementDecisionV2` من النظام وفق D26 دون موافقة أو اختيار مستوى يدوي.
- **S:** طالب موضوع L1/L2/L3، 19 درسًا assigned+skipped، دعم، قراءة، بعدي.
- **U:** مستخدم غير مسجل وآخر طالب للوصول العابر؛ 401/403/404 كما العقد، private audio لا يُسترجع عبر الرابط.
اختبر `GET /api/v2/student/home` و`/api/v2/assessments/current-action` فقط عبر واجهة ومراقبة شبكة Work الآمنة لا نشر payloads الحساسة في التقارير.

## 4. القياسات البصرية والوظيفية
- iPhone Safari الحقيقي من صور المالك، Android Chrome من صور المالك؛ اختبارات Work Browser على 360/390/430/768/1440 بقدر ما يدعم، وقائمة خارجية للأجهزة التي لم تُختبر حقيقيًا.
- RTL: استقامة القراءة والمكوّنات وعناصر nav، إغلاق القائمة، التمرير، عدم غطاء Sticky footer للنص، touch >= 44 CSS px قدر الإمكان، contrast/focus/reduced motion، لا scroll أفقي خاطئ.
- check real UI on deployed URL after fix: screenshots before/after and actual click trail, not screenshot at compile time alone.
- TEST_ONLY/placeholder/missing media: لا تتحول إلى production content بلا اعتماد. راجع لغة الطفل، إرشاد الصوت والنبرات، تغيّر اللغة أو شرح الاختبار بصورة تربوية.
- كل 300 سؤال و6 أنماط: `choose_one`, `listen_choose_one`, `sequence`, `build_word`, `choose_image`, `read_aloud`; 0 كتابة حرة. حالة data/answer leakage والمنع أثناء التقييم.

## 5. بوابات الحالة المرحلية
- `P09_FUNCTIONAL_PENDING`: أي P0/P1 مفتوح أو نقص وظائف admin/student أو مصفوفة E2E.
- `P09_FUNCTIONAL_READY_WITH_TEST_MEDIA`: all routes/interactions pass + owner-reviewed functional evidence + missing production media itemized.
- `P10_MEDIA_PENDING`: 19 final videos and any missing image/audio approval; لا نشر.
- `RELEASE_READY`: media approvals + two-account private S3 + real-device tests + backup/restore/rollback + gated deploy + release candidate regression + owner signoff.


## ملحق قبول التبويبات والصوت والمحتوى — 2026-10-28
الأصل: docs/v2/agent-ops/HIMMA_V2_ADMIN_UX_AUDIO_REVIEW_AND_CONTENT_AUDIT_20261028_AR.md. هذا مصدر مراجع ولم يُنفذ اختبار متصفح مصادق جديد بعد. ملاحظة: D26 هو قرار أحدث من عبارة «قرار المشرف يفتح المستوى»؛ التسكين الذاتي يحصل بعد اكتمال تقييم الصوت فقط.

| المسار | السيناريو الإلزامي للقبول |
|---|---|
| /admin/v2-assessments | تحديد صوت قبلي/بعدي معلّق، التشغيل الكامل، rubric رقمي بعد اعتماده، اعتماد/إعادة، حفظ API/Audit، منع النقر المكرر والقرار بلا صوت، التسكين الآلي بعد آخر مراجعة |
| /admin/v2-lesson-review | نفس مساحة عمل الصوت للدرس والدعم، لا كتابة حرة، تحقق تسجيل آخر وإعادة/استئناف تلقائي، صوت مفقود/تالف |
| /admin/v2-reviewed-recordings | آخر صوت مقيم فقط مع اسم الطالب والدرس والدرجة/سبب التقييم وفق سياسة الخصوصية، رابط تفاصيل، لا تسرب عبر ID |
| /admin/students/[id] | سبعة تبويبات: عامة/دروس/اختبارات/صوت/تكيف/حساب/سجل؛ A→B→A وURL deep link، عدم كشف الرمز تلقائيًا، pending والضعف غير المثبت لا يوصفان إتقانًا |
| /admin/content-preview | 300 سؤال/19 درسًا/12 دعمًا حسب القبلي→L1→L2→L3→بعدي ثم مراحل الدرس والسؤال، وسائل متعددة، إجابات مشرف خاصة، paging وback context |
| /admin/v2-media | 89 أصلًا grouped/paged، تشغيل الوسائط والتمييز بين fixture والنهائي واعتماداتها، empty/error |
| /admin/reports, /admin/skill-reports, /admin/students, /admin/settings, /admin | بطاقات وفلاتر قصيرة، تقارير رسمية مع تصدير، Tabs إعدادات سليمة، responsive navigation وpartial errors |

كل المسارات: desktop 1280/1440، tablet 768/1024، هاتف 320/360/390/430، تكبير 200%، RTL، no horizontal overflow، touch >=44px، Escape/focus return، audio playback permissions، screenshots محدثة + شبكة HTTP + DB result على SHA منشور واحد. لا إعلان VERIFIED_LIVE من الكود أو E2E fixture وحده.
