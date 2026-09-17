# منصة هِمّة — سجل تجهيز إصدار Railway — 2026-09-17

الحالة: PRE-DEPLOYMENT

تم دمج تاريخ التنفيذ الكامل إلى الفرع الرسمي الافتراضي `stage/02-content` بطريقة fast-forward حتى SHA:

`11e45b756d5be857ef1831aa7efe1d33b1a9a723`

يشمل هذا الإصدار كود W1–W6 الأخضر، توثيق الإغلاق، وم scaffolding النشر على Railway:

- `deploy/railway-api.Dockerfile`
- `deploy/railway-web.Dockerfile`
- `deploy/railway-predeploy.sh`

حدود الإصدار:

- مزود ASR الإنتاجي غير مفعّل مؤقتًا.
- لا يوجد Student Audio Skip أو bypass.
- التسجيلات تبقى ضمن مسار المراجعة البشرية حتى اعتماد مزود ASR.

خطوات الإغلاق التشغيلي لهذا الإصدار:

1. Quality Gate على HEAD الرسمي.
2. نشر API + Web من المستودع الرسمي.
3. ربط PostgreSQL + Redis + Object Storage.
4. تشغيل Alembic + canonical 125-item publication.
5. التحقق من `/ready` والواجهات وتدفق تسجيل الدخول.
6. التحقق من security headers في النسخة المنشورة.
7. إزالة خدمات النشر القديمة بعد نجاح البديل.

لا يُعتبر هذا الملف وحده دليل نجاح النشر؛ يجب إلحاق Run/Deployment IDs ونتائج التحقق بعد التنفيذ.
