# خط أساس الاستعادة — هِمّة

**تاريخ التثبيت:** 2026-09-21 (UTC)

هذا المستند يسجل نقطة البداية قبل أعمال التنظيف والتحسين. لا يتضمن هذا الإجراء أي تعديل وظيفي أو نشر جديد.

## المراجع المثبتة

- المستودع: `7eaur/himma-`
- الفرع الرسمي وقت التثبيت: `stage/02-content`
- التزام الإنتاج المؤكد: `4ecb27590f7c19cbe7823804b9919d91000415ef`
- فرع الأرشيف: `archive/production-baseline-20260921`
- فرع التحسين: `improvement/himma-unified-v2-20260921`

تم التأكد من أن رأس GitHub وخدمتي Railway المنشورتين يشيران إلى الالتزام نفسه.

## حالة الإنتاج عند التثبيت

- Railway project: `friendly-dream`
- Environment: `production`
- `himma-web`: SUCCESS — deployment `55dff3b1-a2e3-41de-9416-edc9bc7757b0`
- `himma-api`: SUCCESS — deployment `e9ae4753-bff0-46ce-8133-a330b18b0b34`
- PostgreSQL: SUCCESS مع volume دائم
- Redis: SUCCESS مع volume دائم
- Object bucket: `himma-audio`

لم تُغيّر أي خدمة أو متغير أو قاعدة بيانات أثناء إعداد هذا السجل.

## حالة التحقق الآلي

على الالتزام المثبت:

- frontend: ناجح (type check، lint، unit tests، build)
- backend: ناجح (migrations، model drift، seed idempotency، tests)
- M04 responsive: ناجح
- M09 release readiness: ناجح
- security job: فاشل بسبب 3 مطابقات Gitleaks في ملفات توثيق:
  - `START_HERE_AR.md:153`
  - `docs/ops/RELEASE_DEPLOYMENT_CURRENT_AR.md:32`
  - `docs/ops/progress.json:105`
- integration job: لم يعمل لأن security job أوقف التسلسل.

يلزم فحص المطابقات الثلاث وتحديد إن كانت أسرارًا حقيقية أو أمثلة توثيقية قبل اعتبار البوابة خضراء.

## فجوة نشر مهمة

إعداد Railway الحالي يحتوي `checkSuites: false` لخدمتي الويب والـAPI؛ لذلك يمكن أن يُنشر الالتزام رغم فشل CI. لا يُغيّر هذا الإعداد إلا بعد إصلاح البوابة وتجربة مسار النشر والاستعادة.

## الاستعادة البرمجية المقترحة

1. حدد الالتزام `4ecb27590f7c19cbe7823804b9919d91000415ef` أو فرع الأرشيف.
2. أنشئ فرع استعادة جديدًا من المرجع؛ لا تحرّك فرع الأرشيف.
3. شغّل بوابات frontend وbackend وsecurity وintegration.
4. انشر الويب والـAPI من الالتزام المثبت فقط.
5. تحقق من `/ready` ومن سيناريوهات الدخول، المحتوى، الصوت، والتقدم.

## حدود الاستعادة

فرع الأرشيف يحفظ الكود والتوثيق وإعدادات النشر الموجودة في المستودع. وجود volumes في Railway لا يساوي نسخة احتياطية مستقلة لبيانات PostgreSQL أو Redis أو ملفات الصوت.

لم تُنشأ نسخة بيانات جديدة في هذه المرحلة لأن الأدوات المتاحة لا توفر عملية backup/restore موثوقة قابلة للتحقق. قبل أي migration مدمرة يجب:

- أخذ نسخة PostgreSQL مستقلة واختبار الاستعادة في بيئة غير الإنتاج.
- جرد bucket الصوت ونسخه إلى موقع مستقل.
- تسجيل زمن النسخة وchecksum/عدد العناصر ونتيجة اختبار الاستعادة.
- منع migrations المدمرة حتى نجاح هذا الاختبار.

## قاعدة العمل

- لا تعديل مباشر على `stage/02-content`.
- كل التحسينات على `improvement/himma-unified-v2-20260921`.
- لا نشر إنتاج قبل CI أخضر، اختبار السيناريوهات، وخطة رجوع مجرّبة.
- يبقى `archive/production-baseline-20260921` مرجع قراءة واستعادة فقط.
