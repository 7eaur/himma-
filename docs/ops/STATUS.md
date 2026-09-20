# STATUS — Himma Platform

**Last synchronized:** 2026-09-21  
**Repository:** 7eaur/himma-  
**Official branch:** stage/02-content  
**Current functional / gate / production SHA:** `0bf1390bdbc0a19330c807d82d646424490b5a2b`  
**State:** CLOSED / PRODUCTION_GREEN

## Current truth

الفرع الرسمي يحتوي آخر تحديثات المحتوى والقراءة وصفحة إدارة المحتوى. لا تستخدم أي handoff قديم يقول إن Content Preview ما زال محاكاة لواجهة الطالب أو إن التشكيل القديم ما زال معتمدًا.

## Closed in the latest batch

- اعتماد سياسة تخفيف التشكيل للجمل والنصوص مع إبقاء الحروف/المقاطع/الكلمات المفردة بتشكيلها، والحفاظ على الشدّة المهمة.
- Corpus تدريب مطابق للإصدار النهائي: 92 سجلًا.
- إلغاء مفهوم Student-like Content Preview للمشرف.
- بناء Admin Content Review read-only من PostgreSQL approved content.
- عرض السؤال/التعليمة/التلميح/الخيارات/الإجابة الصحيحة/الصور/الأصوات/هدف التسجيل.
- دعم الترتيب الصحيح في sequence tasks.
- بحث نصي كامل وفلاتر.
- إظهار فروع التقوية المرتبطة بالـCore.
- إبقاء Student payloads answer-safe.
- لا كتابة على تقدم الطلاب من صفحة المحتوى.

## Exact official evidence

SHA: `0bf1390bdbc0a19330c807d82d646424490b5a2b`

- QG #976 / Run `35541791265`: SUCCESS.
  - Frontend unit: 40 passed.
  - Backend: 902 passed, 5 warnings.
  - Integration Playwright: 23 passed (3.7m).
  - Security: SUCCESS.
- M04 #387 / Run `35541791302`: SUCCESS.
  - responsive smoke: 2 passed.
  - artifact: `10615031736`.
  - digest: `sha256:843fd55e673cdb93d51cfcd0c109d5f15beab7aa07bca926296a9b9338da7930`.
- M09 #252 / Run `35541791274`: SUCCESS.
  - Backend: 902 passed, 5 warnings.
  - Browser: 23 passed (3.5m).
  - PostgreSQL restore PASS.
  - 44 skills / 125 content_items restored.
  - object store restore: 35.

## Canonical content

- Version: `HIMMA-CONTENT-APPROVAL-2026-09-08`.
- Runtime: 125 items / 44 skills.
- Canonical release SHA: `e6c749add3652ca8aa896065218673eaac8a07cd0cbca1e92710f35f14f5a904`.
- Projection SHA: `e1d14b0b6102f635820aa7f9a9b074e4f7afd68a02006d0a8ee8a3f29f99670e`.
- Training corpus: `packages/content/training/himma_reading_training_corpus_v2026_09_21.jsonl` — 92 records.

## Production

Railway `friendly-dream / production`:
- himma-api `f160b611-c157-4a53-9d37-cfae289cfb07`: SUCCESS.
- himma-web `7f6fec27-3f38-4e21-afd6-c9b62729b168`: SUCCESS.
- deployed commit = exact current SHA.
- Postgres / Redis = SUCCESS.
- himma-audio bucket = present.
- canonical publication = 125.
- /ready = 200.

## Remaining boundaries

Only external/owner items remain:
- Production ASR/provider/calibration/privacy/governance.
- child data/audio retention decision.
- final study protocol parameters if not approved.
- manual human screen-reader acceptance.
- optional custom domain/entity branding.

## Current action

لا توجد مرحلة تنفيذ عامة مفتوحة. استلم أي تكليف جديد من المالك فوق هذه الحالة. نقطة الدخول:
`START_HERE_AR.md`
