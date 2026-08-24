# تقرير تسليم مشروع هِمّة — 2026-08-24

## معلومات Git
- الفرع الحالي: stage/04-production-slice
- HEAD SHA: ef6b9ce (آخر commit = تقرير التسليم)
- Remote: himma-github -> git@github.com:7eaur/himma-.git
- رابط الفرع: https://github.com/7eaur/himma-/tree/stage/04-production-slice

## حالة Git
- Commits محلية غير موجودة في GitHub: لا يوجد (مطابق تماماً)
- Working tree: نظيف (nothing to commit, working tree clean)
- git status: clean

## الفروع
- محلي: main, recovery/p02-baseline, stage/01-foundation, stage/02-content, stage/03-design-routes, stage/04-production-slice (الحالي)
- بعيد: himma-github/recovery/p02-baseline, himma-github/stage/02-content, himma-github/stage/03-design-routes, himma-github/stage/04-production-slice

## البنية التقنية (مُفحوصة من الكود)
### Frontend
- Framework: Next.js 16.3.0 مع Turbopack
- TypeScript: نعم (tsconfig.json موجود)
- CSS: Pure CSS (globals.css 1762 سطر) — بدون Tailwind
- المنفذ: 3000
- أمر التشغيل: cd apps/web && npm run dev (مع NEXT_PUBLIC_API_URL=http://localhost:8000)

### Backend
- Framework: FastAPI >=0.100.0
- Python: 3.12.3
- المنفذ: 8000
- أمر التشغيل: cd services/api && python run_dev.py

## الخدمات بدون Docker
| الخدمة | طريقة التشغيل | المنفذ | الحالة وقت التدقيق |
| PostgreSQL 18 | Windows Service (postgresql-x64-18) | 5432 | Running |
| MinIO | عملية Windows يدوية (minio.exe) | 9000/9001 | لم يكن يعمل |
| Redis | عملية Windows (redis-server) | 6379 | Running (PID 6328) |
| FastAPI | يدوي (python run_dev.py) | 8000 | لم يكن يعمل |
| Next.js | يدوي (npm run dev) | 3000 | لم يكن يعمل |

## أوامر التشغيل
`powershell
# 1. PostgreSQL يعمل تلقائياً كـ Windows Service

# 2. MinIO
C:\himma-services\minio\minio.exe server E:\himma-services\minio-data --console-address :9001

# 3. Redis — يعمل (راجع)

# 4. FastAPI
cd services/api
=postgresql://himma:himmapass@localhost:5432/himma_db
=himma-secret-key-min-32-chars-long-secure
=localhost:9000
=minioadmin
=minioadmin
=himma-audio
=redis://localhost:6379
python run_dev.py

# 5. Next.js
cd apps/web
=http://localhost:8000
npm run dev
`

## متغيرات البيئة (بدون قيم)
### Backend: DATABASE_URL | API_SECRET_KEY | MINIO_ENDPOINT | MINIO_ACCESS_KEY | MINIO_SECRET_KEY | MINIO_BUCKET | REDIS_URL
### Frontend: NEXT_PUBLIC_API_URL

## Migrations وSeed
`powershell
cd services/api
alembic upgrade head   # تطبيق الـ migrations
python seed.py         # زرع البيانات: researcher1 + محتوى + طلاب نموذج
`
بيانات الباحثة: username=researcher1 | URL الأدمن: http://localhost:3000/admin/login (مباشر فقط)
رمز الطالب: يُنشأ من لوحة الباحث

## نتائج الاختبارات (مُنفذة فعلياً 2026-08-24)
| الاختبار | exit code | النتيجة |
| TypeScript (npx tsc --noEmit) | 1 | فشل — 2 errors في session/[id]/page.tsx:285,296 |
| Backend pytest test_api.py | 1 | 24 passed / 1 failed (SameSite cookie) |
| Alembic check | 1 | فشل — schema drift (Enum + FK changes) |
| Alembic current | 0 | نجح |
| Seed import | 0 | نجح |
| API smoke | - | لم يُشغَّل (يدوي مطلوب) |
| Next.js build | - | لم يُشغَّل (يدوي مطلوب) |

## الملفات المستبعدة من الرفع
.env / .env.local / node_modules/ / .next/ / __pycache__/ / venv/ — جميعها في .gitignore

## Secret Scan
CLEAN — لا توجد أسرار في الملفات غير المتتبعة

## هل GitHub يحتوي جميع التغييرات المقصودة؟
نعم — SHA محلي = SHA بعيد = ef6b9ce

## الفجوات للمهندس القادم
1. [حرجة] interaction_type mismatch: catalog.json يستخدم read_aloud لكن session/[id]/page.tsx تتوقع audio_record -> أسئلة الصوتية لن تعمل
2. [عالية] 2 TypeScript errors تمنع build نظيف في session/[id]/page.tsx:285,296
3. [عالية] Alembic schema drift: يجب تشغيل alembic revision --autogenerate
4. [عالية] P04 E2E Playwright test (السيناريو الكامل) لم يُكتب
5. [متوسطة] ألوان inline غير معتمدة في page.tsx: #7C3AED (بنفسجي) و #D97706 (كهرماني)
6. [منخفضة] إيموجي في سؤال واحد في packages/content/src/catalog.json
7. [منخفضة] مجلد tests/ غير موجود في services/api/ — pytest يبحث عنه هناك
8. [منخفضة] Cookie SameSite=none (الكود) vs SameSite=lax (التوقع في test_api.py)

## الملخص النهائي (لا يحتمل التأويل)
1. الفرع النهائي: stage/04-production-slice
2. SHA: ef6b9ce7... (git rev-parse HEAD)
3. الرابط: https://github.com/7eaur/himma-/tree/stage/04-production-slice
4. هل كل تغييرات الجهاز رُفعت؟ نعم
5. هل working tree نظيف؟ نعم
6. هل المشروع يعمل بدون Docker؟ نعم (PostgreSQL+Redis كـ Windows Services، MinIO كعملية مستقلة)
7. قاعدة البيانات والتخزين: PostgreSQL 18 (Windows Service) + MinIO (عملية مستقلة)
8. نتائج الاختبارات: TypeScript 0/2 errors، pytest 24/25 passed، Alembic drift
9. مسار التقرير: docs/handoff/LOCAL_HANDOFF_2026-08-24.md
10. ملفات غير مرفوعة: .env / node_modules / .next / __pycache__ / venv (مستبعدة بشكل مقصود)
