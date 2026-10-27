# HIMMA MASTER HANDOFF — 2026-09-21

هذا الملف هو **التسليم الحالي الكامل** لمنصة هِمّة للمحادثة التالية. لا تعتمد عليه بدل الحالة الحية إذا تغير المستودع؛ أول خطوة دائمًا هي Fetch للـHEAD الرسمي.

## 1. الاستلام السريع

Repository:
`7eaur/himma-`

Official branch:
`stage/02-content`

HEAD المؤكد عند إنشاء هذا الملف:
`0bf1390bdbc0a19330c807d82d646424490b5a2b`

Commit:
`refine(admin): expose reinforcement branches and full-text search`

Current state:
**CLOSED / PRODUCTION_GREEN**

نفس SHA نجح في QG/M04/M09 ونُشر على Railway للـAPI والويب.

## 2. Source of Truth

الترتيب الإلزامي:
1. live repository code.
2. PostgreSQL migrations/schema.
3. executable tests / exact-SHA CI.
4. verified Railway runtime.
5. canonical content/audio/product contracts.
6. current authoritative docs.
7. historical docs/handoffs.

لا تستخدم هذا الملف لتجاوز دليل أحدث.

## 3. ما يجب قراءته لفهم هِمّة كاملًا

### A — الحالة الحالية أولًا
1. `START_HERE_AR.md`
2. `docs/ops/STATUS.md`
3. `docs/ops/progress.json`
4. `docs/ops/PROJECT_STATE.md`
5. `docs/ops/ROADMAP.md`

### B — قواعد الحقيقة والمعمارية والمنتج
6. `docs/specs/SOURCE_OF_TRUTH.md`
7. `docs/specs/SYSTEM_SPEC.md`
8. `docs/specs/ARCHITECTURE_BASELINE.md`
9. `.agents/rules/00-himma-core.md`
10. `.agents/rules/10-delivery-protocol.md`
11. `.agents/rules/20-security-quality.md`
12. `docs/ops/DECISIONS.md`

### C — الصوت والإطلاق والأدلة
13. `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_CURRENT_AR.md`
14. `docs/ops/EVIDENCE_INDEX.md`
15. `docs/ops/RELEASE_DEPLOYMENT_CURRENT_AR.md`
16. `docs/ops/OPEN_ITEMS.md`
17. `docs/maintenance/HIMMA_BRANCH_INVENTORY_2026-09-18_AR.md`

### D — آخر تغييرات المحتوى
18. `services/api/canonical_release.py`
19. `services/api/reading_text_policy_2026_09_21.py`
20. `services/api/test_reading_text_policy_2026_09_21.py`
21. `packages/content/training/himma_reading_training_corpus_v2026_09_21.jsonl`
22. `services/api/content_approval_contract_2026_09_08.py`
23. `services/api/canonical_content_compiler.py`

### E — آخر إعادة بناء لصفحة المحتوى الإداري
24. `services/api/content_preview.py`
25. `apps/web/src/app/admin/(dashboard)/content-preview/page.tsx`
26. `apps/web/src/app/admin/(dashboard)/layout.tsx`
27. `services/api/test_content_surface_parity.py`
28. `services/api/content_runtime.py`
29. `services/api/content_student_view.py`

بعد ذلك استخدم `docs/ops/DOCUMENTATION_INDEX.md` لتحديد أي وثيقة أخرى Current أو Historical.

## 4. المنتج الحالي

هِمّة منصة ويب عربية RTL بسطحين:
- الطالب.
- المشرف.

الطالب يدخل بكود. المشرف ينشئ الطلاب، يتابع المسار، يراجع التسجيلات، يرى المحتوى المعتمد، التقارير والإعدادات.

لا يوجد تطبيق موبايل أصلي ضمن النطاق الحالي.

## 5. رحلة الطالب

- Pretest: 30.
- Placement: <50 L1 / 50..<80 L2 / >=80 L3.
- Core learning + targeted reinforcement.
- Activity thresholds: >=80 pass / 70..<80 retry / <70 reinforcement.
- Continuous adaptation uses valid evidence.
- no automatic demotion.
- L1/L2 promotion only after approved mastery rules.
- L3 terminal after 10 Core.
- Posttest: 30 after learning completion + supervisor enable.

## 6. المحتوى الحالي

Canonical version:
`HIMMA-CONTENT-APPROVAL-2026-09-08`

Runtime:
- 125 items.
- 30 pretest.
- 30 posttest.
- 30 core.
- 35 reinforcement.
- 44 skills.

Canonical SHA:
`e6c749add3652ca8aa896065218673eaac8a07cd0cbca1e92710f35f14f5a904`

Projection SHA:
`e1d14b0b6102f635820aa7f9a9b074e4f7afd68a02006d0a8ee8a3f29f99670e`

## 7. آخر تعديل أكاديمي/عرض قراءة

المالك اعتمد في 2026-09-21:
- الحروف/المقاطع/الكلمات المفردة تبقى بتشكيلها.
- العبارات والجمل والنصوص الطويلة تخفف من الحركات الاختيارية.
- تبقى الشدة المهمة.
- التنفيذ في final canonical release boundary، وليس JSX patch.

Training corpus:
`packages/content/training/himma_reading_training_corpus_v2026_09_21.jsonl`

عدد السجلات:
92.

اختبار regression يثبت تطابق corpus مع final release targets.

## 8. آخر تعديل جذري في لوحة المشرف

المطلوب من المالك كان حذف فكرة “معاينة واجهة الطالب” بالكامل.

القرار المنفذ:
- أبقينا route `/admin/content-preview` لحماية الروابط.
- ألغينا وظيفته القديمة بالكامل.
- الاسم الظاهر: **المحتوى المعتمد**.
- Backend لم يعد يعيد student serializer.
- Admin projection مستقل يقرأ approved PostgreSQL content.
- read-only ولا ينشئ sessions/attempts/responses/progress.

المشرف يرى:
- السؤال.
- التعليمة.
- التلميح.
- stimulus.
- كل الخيارات.
- correct answer(s).
- correct order للترتيب.
- recording target لمهام القراءة.
- option images.
- prompt/story audio مع player.
- reading/audio context intro.
- media gaps.
- filters.
- full-text search.
- Core → approved reinforcement candidates links.

Student serializers ما زالت تمنع answer metadata.

## 9. Commit chain لأحدث العمل

- `7dce39b1...` — simplify diacritics in sentence reading targets.
- `43dd1547...` — align training corpus with retained shadda.
- `df00c34c...` — replace student preview with approved content review.
- `96b0aeee...` — lint-safe React effects.
- `5dacb8eb...` — testable admin filter defaults.
- `0bf1390b...` — reinforcement branch links + full-text search.

اعتمد live HEAD إذا ظهر أحدث.

## 10. CI الحالي

Exact SHA:
`0bf1390bdbc0a19330c807d82d646424490b5a2b`

QG #976 / Run `35541791265`:
- SUCCESS.
- Backend: 902 passed, 5 warnings.
- Frontend unit: 40 passed.
- Integration Playwright: 23 passed (3.7m).
- Security: SUCCESS.

M04 #387 / Run `35541791302`:
- SUCCESS.
- responsive smoke: 2 passed.
- artifact: `10615031736`.
- digest: `sha256:843fd55e673cdb93d51cfcd0c109d5f15beab7aa07bca926296a9b9338da7930`.

M09 #252 / Run `35541791274`:
- SUCCESS.
- Backend: 902 passed, 5 warnings.
- Browser: 23 passed (3.5m).
- PostgreSQL restore PASS.
- skills 44 / content_items 125.
- object restore 35.

## 11. Production

Railway:
- project `friendly-dream`.
- environment `production`.

Exact deployed SHA:
`0bf1390bdbc0a19330c807d82d646424490b5a2b`

Deployments:
- API `f160b611-c157-4a53-9d37-cfae289cfb07` SUCCESS.
- Web `7f6fec27-3f38-4e21-afd6-c9b62729b168` SUCCESS.

Also:
- PostgreSQL SUCCESS.
- Redis SUCCESS.
- himma-audio bucket present.
- Alembic predeploy PASS.
- canonical publication 125.
- /ready 200.

## 12. Audio contract

- Human Supervisor Review = authority.
- 54 IDs, 54 WAV + 54 MP3.
- pending audio academically neutral.
- remaining unanswered questions continue.
- finalization waits required reviews.
- rerecord explicit/history-preserving.
- no Student Audio Skip.
- no Temporary Audio Skip.
- no fake ASR.
- production ASR deferred/external.

## 13. ما هو مغلق

- recovery القديمة.
- canonical reconciliation السابقة.
- student/admin core journeys.
- adaptation/reinforcement.
- human audio review.
- UX rebuild.
- reading-text policy update.
- training corpus export.
- admin approved-content review rebuild.
- exact-SHA gates.
- Railway deployment.

لا تعِد أي منها بدون regression evidence جديد.

## 14. ما تبقى

فقط:
- Production ASR provider/calibration/privacy/governance.
- child recording/data retention policy.
- final research protocol parameters if unresolved.
- manual human screen-reader acceptance.
- optional custom domain/branding.

## 15. قاعدة التنفيذ للمحادثة الجديدة

- لا تعتمد على الذاكرة بدل المستودع.
- لا ترقيع؛ أصلح Root Cause.
- لا تغيّر قواعد أكاديمية بصمت.
- لا fake ASR.
- لا Docker كاعتماد محلي للمشروع.
- لا تضع answers في Student payload.
- لا تخلط Admin Review بStudent UI مرة أخرى.
- كل PASS مهم يحتاج exact SHA evidence.
- عند أي functional change: tests → exact CI → Railway verification إذا production affected.
