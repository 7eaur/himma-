# خط الأساس المعماري الحالي — هِمّة

**Updated:** 2026-09-18

## الشكل العام

Browser
→ apps/web (Next.js Arabic RTL)
→ services/api (FastAPI modular domain API)
→ PostgreSQL
→ Redis للتنسيق قصير العمر
→ private object storage للتسجيلات/الأصول الخاصة

أي speech provider إنتاجي ليس جزءًا من الحالة المغلقة الحالية.

## الوحدات

### apps/web
- Next.js 16.3.4 + React 19.2.8 + TypeScript.
- طالب + مشرف.
- لا يملك قواعد الدرجات والتكيف المرجعية.
- يستخدم API كمصدر الحقيقة.

### services/api
- FastAPI/Python.
- auth، students، assessments، learning، adaptation، content، audio review، rewards، reports، audit.
- SQLAlchemy + Alembic.
- PostgreSQL هو transactional truth.

### packages/content
- catalog/versioned additions/validators/canonical release.
- يحول المصادر المعتمدة إلى projection حتمي ثم PostgreSQL.

### Redis
- rate limiting / short-lived coordination.
- ليس academic truth.

### Object storage
- recordings والأصول الخاصة.
- لا public child-recording paths.

## الهجرات

الشجرة الحالية تحتوي 15 migration files تحت services/api/alembic/versions. أي schema change جديد يجب أن يبقى تراكمياً وآمنًا مع migration/rollback أو restore evidence.

## حدود إلزامية

- لا direct DB من الواجهة.
- لا business scoring داخل JSX.
- كل تغيير في الدرجة/المستوى/المراجعة له domain service/audit/test.
- لا runtime patching ليصحح catalog بعد النشر.
- لا child recordings/secrets/db dumps في Git.
- reference/ read-only.
- نفس المصدر يغذي Dashboard/Excel/PDF حيث ينطبق.

## Docker clarification

المشروع لا يعتمد Docker كبيئة تشغيل محلية أو كشرط CI؛ البوابات الحالية تبدأ PostgreSQL/Redis وMinIO مباشرة.  
Railway يستخدم deploy/railway-*.Dockerfile كآلية packaging/build للمنصة المنشورة. هذا استخدام نشر خاص بالمنصة وليس عودة إلى Docker workflow محلي.

## الاختبارات

- Backend/unit/integration/domain.
- PostgreSQL migration roundtrip + drift.
- content validation + idempotent publication.
- frontend type/lint/unit/build.
- Playwright real-browser journeys.
- responsive/RTL/keyboard/axe checks.
- dependency/secret/placeholder/skip guards.
- PostgreSQL + object-store backup/restore in M09.
