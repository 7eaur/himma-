> **HISTORICAL / SUPERSEDED:** هذه الوثيقة محفوظة للتاريخ والدليل فقط. الحالة الحالية بعد 2026-09-18 موجودة في START_HERE_AR.md وdocs/ops/RELEASE_DEPLOYMENT_CURRENT_AR.md. أي عبارة هنا مثل NOT MERGED / NOT DEPLOYED / ACTIVE / STOP أو branch قديم لا تصف الوضع الحالي.

# منصة هِمّة — سجل إصدار Railway — 2026-09-17

الحالة: **BASELINE DEPLOYED + VERIFIED / UX REBUILD NOT DEPLOYED YET**

## الإصدار الرسمي المنشور حاليًا

الفرع الرسمي:

`stage/02-content`

SHA المنشور والمتحقق منه عند آخر نقطة تشغيل رسمية قبل دفعة UX الحالية:

`765c42d769624ad13683798f68177f6597f2149f`

هذا الإصدار يضم إصلاح عقد Pending Audio / Rerecord واختبارات E2E المحدثة، وتم نشره إلى Railway بعد نجاح بوابات الإصدار.

## أدلة الاختبار/الإصدار

- Integration Quality Gate #911 — Run `35241996615`: SUCCESS.
- M09 #215 — Run `35241996654`: SUCCESS.
  - Playwright: 20 passed.
  - PostgreSQL backup/restore: ناجح، مع 125 عنصرًا و44 مهارة بعد الاستعادة.
  - Object Storage backup/restore: 35 ملفًا/كائنًا تم التحقق منها في ذلك الـRun.
- Official Quality Gate #912 — Run `35243714139`: SUCCESS على الـSHA الرسمي نفسه.

## حالة Railway عند آخر تحقق رسمي

الخدمات المطلوبة كانت موجودة وناجحة:

- `himma-api`
- `himma-web`
- PostgreSQL
- Redis
- `himma-audio` object storage

التحقق التشغيلي:

- `/api/health` → HTTP 200.
- `/api/ready` → HTTP 200.
- Readiness checks الخاصة بـconfig/database/content/approved_audio/storage/redis/security_mode كانت سليمة عند نقطة التحقق.
- Canonical runtime بقي 125 item / 44 skill.

## بنية النشر

ملفات النشر المعتمدة في المستودع:

- `deploy/railway-api.Dockerfile`
- `deploy/railway-web.Dockerfile`
- `deploy/railway-predeploy.sh`

حدود الصوت:

- مزود ASR الإنتاجي الخارجي غير مفعّل حتى الآن.
- لا يوجد Student Audio Skip أو Temporary Audio Skip أو bypass.
- Human Supervisor Review هي السلطة الأكاديمية للتسجيلات في الوضع الحالي.

## دفعة UX الحالية ليست منشورة

الفرع النشط:

`fix/ux-system-rebuild-2026-09-17`

آخر Functional SHA مختبر قبل commits التوثيق فقط:

`09be49102d1aab8f09cf1a3267ccd073c46c7397`

Quality Gate #917 / Run `35261495545`: SUCCESS.

لكن هذه الدفعة **لم تُدمج إلى `stage/02-content` ولم تُنشر على Railway حتى الآن**.

المتبقي قبل نشرها:

1. Visual QA لصور/واجهات الهاتف والديسكتوب مقابل مشاكل المالك الأخيرة.
2. إصلاح أي mismatch ثم QG exact-head جديد إذا تغير الكود.
3. M09 Release Readiness على final UX SHA.
4. Merge/fast-forward إلى الفرع الرسمي.
5. Official exact-head CI.
6. Railway deploy.
7. Production QA لمسارات Student/Admin/Audio/Pending/Rerecord/Toasts/Responsive.

لا تستخدم هذا الملف كدليل أن UX الحالية منشورة؛ الإصدار المنشور الموثق هنا هو baseline `765c42d...` فقط حتى يكتمل الإغلاق التالي.
