# تقرير تسليم مشروع هِمّة — 2026-08-24

## معلومات Git
- الفرع الحالي: stage/04-production-slice
- HEAD SHA (قبل): 9636eed7054717536e2aedd4341afd527882a7b1
- HEAD SHA (بعد): 9636eed7054717536e2aedd4341afd527882a7b1
- Remote: himma-github → git@github.com:7eaur/himma-.git
- رابط الفرع: https://github.com/7eaur/himma-/tree/stage/04-production-slice

## حالة Git
- عدد الملفات المعدلة: 0
- عدد الملفات الجديدة: 0
- عدد الملفات المحذوفة: 0
- Commits محلية غير موجودة في GitHub: لا يمكن التأكد بشكل كامل بسبب رفض الاتصال (Connection refused) مع GitHub.

## البنية التقنية
### Frontend
- Framework: Next.js 16.3.0
- TypeScript: نعم
- CSS: Pure CSS (globals.css)
- المنفذ: 3000
- أمر التشغيل: `cd apps/web && $env:NEXT_PUBLIC_API_URL='http://localhost:8000'; npm run dev`

### Backend  
- Framework: FastAPI (>=0.100.0)
- Python: 3.x
- المنفذ: 8000
- أمر التشغيل: `cd services/api && $env:DATABASE_URL='...'; $env:API_SECRET_KEY='...'; python run_dev.py`

### قاعدة البيانات
- النوع: PostgreSQL
- طريقة التشغيل: Windows Service (بدون Docker)
- Migrations: Alembic (>=1.11.0)
- أمر الـ Seed: `python seed.py`

### التخزين
- MinIO: يعمل كعملية Windows مستقلة (بدون Docker)
- المنفذ: 9000 (API) / 9001 (Console)
- أمر التشغيل: `C:\himma-services\minio\minio.exe server E:\himma-services\minio-data --console-address :9001`

### Redis
- يعمل كـ: Windows Service
- المنفذ: 6379

## متغيرات البيئة المطلوبة (بدون قيم)
### Backend (services/api/.env):
- DATABASE_URL
- API_SECRET_KEY
- MINIO_ENDPOINT
- MINIO_ACCESS_KEY
- MINIO_SECRET_KEY
- MINIO_BUCKET
- REDIS_URL

### Frontend (apps/web/.env.local):
- NEXT_PUBLIC_API_URL

## أوامر التشغيل الكاملة
```powershell
# 1. تشغيل PostgreSQL (Windows Service — يعمل تلقائياً)
# 2. تشغيل MinIO
C:\himma-services\minio\minio.exe server E:\himma-services\minio-data --console-address :9001
# 3. تشغيل Redis (إذا كان مطلوباً)
# 4. تشغيل FastAPI
cd services/api
$env:DATABASE_URL='...'; $env:API_SECRET_KEY='...'; python run_dev.py
# 5. تشغيل Next.js
cd apps/web
$env:NEXT_PUBLIC_API_URL='http://localhost:8000'; npm run dev
```

## إنشاء بيانات الاختبار
```powershell
# إنشاء حساب الباحث والبيانات الأولية
cd services/api
python seed.py  # يُنشئ researcher1 وعدداً من الطلاب والمحتوى
# رمز الطالب للاختبار: يُنشأ من لوحة الباحث على http://localhost:3000/admin
# صفحة الادمن: http://localhost:3000/admin/login (URL مباشر — غير مرتبط بالصفحة الرئيسية)
```

## نتائج الاختبارات
| الاختبار | الأمر | exit code | النتيجة | الوقت |
|---|---|---|---|---|
| TypeScript check | `npx tsc --noEmit` | 2 | فشل (أخطاء في الـ Types) | - |
| Next.js build | `npx next build` | 1 | فشل | - |
| Backend tests | `python -m pytest tests/` | 4 | فشل (مجلد الاختبارات tests/ غير موجود) | - |
| Alembic check | `alembic check` | -1 (أو 1) | فشل (تغييرات في الـ models لم يُنشأ لها migrations) | - |
| API smoke | `curl /health` | - | فشل (الـ API لا يعمل حالياً) | - |
| Frontend smoke| `curl /` | - | فشل (الـ Frontend لا يعمل حالياً)| - |

## الملفات المرفوعة
(جميع ملفات المستودع المتتبعة الحالية باستثناء المستبعدات)

## الملفات غير المرفوعة وسبب الاستبعاد
- `**/.env*` — بيانات حساسة
- `**/node_modules/` — مكتبات قابلة للتثبيت
- `**/.next/` — ملفات بناء مؤقتة
- `**/__pycache__/` — ملفات Python المحولة

## نتيجة Secret Scan
لا توجد أي أسرار في الملفات المتتبعة التي لم تُرفع (Working tree نظيف تماماً).

## حالة Git النهائية
```
On branch stage/04-production-slice
nothing to commit, working tree clean
```

## هل GitHub يحتوي جميع التغييرات المقصودة؟
غير معلوم — تعذر الاتصال بمستودع GitHub بسبب خطأ `Connection refused` على المنفذ 22.

## الفجوات والملاحظات للمهندس القادم
1. interaction_type mismatch: catalog.json يستخدم `read_aloud` لكن session page تتوقع `audio_record`
2. ألوان inline في page.tsx (#7C3AED, #D97706) خارج نظام التصميم
3. إيموجي في سؤال واحد في catalog.json
4. P04 E2E Playwright test لم يُكتب بعد
5. توجد تغييرات في Schema في `content_items` و `content_asset_links` وغيرها تحتاج لـ alembic revision جديد.
6. مجلد الاختبارات `tests/` غير موجود في `services/api`.
7. يوجد خطأ Typescript يمنع الـ Build في تطبيق Next.js.
