# حالة مشروع هِمّة الحالية

**Current snapshot:** 2026-09-21  
**Official branch:** `stage/02-content`  
**Current verified SHA:** `0bf1390bdbc0a19330c807d82d646424490b5a2b`

## المنتج

هِمّة منصة ويب عربية RTL تعليمية/بحثية بسطحين: طالب ومشرف. النظام يعمل بBackend حقيقي، PostgreSQL/Alembic، Auth، content runtime، مسار تعلم متكيف، تسجيل ومراجعة بشرية للصوت، تقارير، CI release gates، وRailway production.

## المحتوى

- 125 runtime items / 44 skills.
- 30 Pretest / 30 Posttest / 30 Core / 35 Reinforcement.
- canonical release SHA: `e6c749add3652ca8aa896065218673eaac8a07cd0cbca1e92710f35f14f5a904`.
- الجمل والنصوص الطويلة مخففة التشكيل؛ المفردات والحروف تبقى بتشكيلها المعتمد.
- Training corpus الرسمي: 92 records.

## إدارة المحتوى

صفحة الإدارة على `/admin/content-preview` لم تعد Student Preview. أصبحت **المحتوى المعتمد**:
- read-only admin projection من approved DB rows.
- الأسئلة والتعليمات والتلميحات.
- الخيارات والإجابة الصحيحة.
- صور الخيارات.
- تشغيل الصوت.
- هدف التسجيل الصوتي.
- الترتيب الصحيح.
- البحث والفلاتر.
- فروع التقوية المرتبطة بالـCore.
- لا progress writes.
- لا تسريب answer metadata إلى Student APIs.

## الصوت

Human Supervisor Review هو المرجع الأكاديمي الحالي. لا Audio Skip ولا Fake ASR. Production ASR مستقل ومؤجل.

## الهندسة والإطلاق

- QG #976: GREEN.
- M04 #387: GREEN.
- M09 #252: GREEN.
- Backend exact-head: 902 passed.
- Frontend unit: 40 passed.
- Playwright: 23 passed.
- Railway API/Web على exact SHA الحالي: SUCCESS.
- /ready: 200.
- PostgreSQL restore: PASS.
- object store restore: 35 objects.

## المفتوح

فقط البنود الخارجية/المالك الموجودة في `docs/ops/OPEN_ITEMS.md`.
