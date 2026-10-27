# W0 — تجهيز المعاينة المعزولة / BLOCKED_EXTERNAL

2026-10-27 Asia/Aden. السبب خدمة Railway/حد الموارد، وليس نقص موافقة نشر نهائي.

## ما جُهّز فعليًا
- فرع GitHub مستقل `v2/work-owner-staging-20261027` من4d7cec1fda88bba9ccc643522a5da7b404036aaf. لا auto deploy لهذا الفرع على مشروع الرابط القديم؛ لن تُرفع الدفعات اللاحقة إلى فرع الإنتاج المتصل أثناء هذا العزل.
- مشروع خاص `himma-v2-work-preview-20261027` بالمعرف6da7e630-f1d4-4d6c-90d1-c711cb14007c، في workspace المشروع الأصلي نفسه.
- environment `staging` معرفd62f6391-484d-4a66-bacd-5cdb941870b7.
- PostgreSQL جديد مستقل بمعرفf4f3d8e3-8618-46d9-a312-e913da75963f؛ read-back environment_status أثبتOnline/SUCCESS deployment8306a13e-5aa2-40b0-8d6c-cc48bf87b633. لا بيانات أطفال أو dump من المشروع السابق. لم تُشغّل migrations/seed للتطبيق عليه بعد.
- bucket جديد `himma-v2-synthetic-audio` معرفc3892a04-f3c8-468c-9644-d19e00cb16c5، regioniad؛ أنشئ بمشروع المعاينة، ولم تُنقل إليه تسجيلات قديمة أو تُستخرج مفاتيحه.

## العائق المثبت
طلب create_service لخدمة `himma-v2-api` رُفض بالنص:

> Free plan resource provision limit exceeded. Please upgrade to provision more resources!

القراءة اللاحقة list_services/environment_status أظهرت **Postgres فقط**، ولا API/Web/Redis. طلب template Redis رجع workflow لكنه لا يثبت إنشاء خدمة؛ لا ندعي جاهزيته. لا إعادة محاولات للتحايل على الحد، ولا نقل النشر إلى موارد الإنتاج.

## الخطوة الخارجية المطلوبة
رفع/إتاحة حد موارد workspace المستهدف أو توفير بيئة اختبار معزولة جاهزة مصرح بها. بعد ذلك فقط تُجهز خدمات API/Web/Redis ومفاتيح جديدة ومصدر code مثبت بـSHA مجتاز للبوابات، مع بيانات اختبار فقط، ثم فحص Work على عنوان staging الفعلي. لا يحتاج ذلك دمج main ولا اعتماد release نهائي.

## حالة القبول
`W0_STAGING=BLOCKED_EXTERNAL`. يوجد مشروع وقاعدة وبucket، **لا توجد منصة معاينة عاملة بعد**. P09/P10/W2–W6 لا تُقبل قبولًا شاملًا اعتمادًا على هذه البنية الجزئية. أعمال الفرع/الاختبارات وقراءة الجرد مستمرة، والبيئة السابقة وبيانات V1 محفوظة.
