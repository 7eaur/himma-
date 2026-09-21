# ابدأ من هنا — منصة هِمّة | الحالة الحالية الموحّدة

**هذه هي نقطة الدخول الرسمية لأي محادثة أو وكيل جديد.**

**آخر تحديث:** 2026-09-21  
**Repository:** `7eaur/himma-`  
**Official branch:** `stage/02-content`  
**Current functional + verified production SHA:** `0bf1390bdbc0a19330c807d82d646424490b5a2b`  
**State:** CLOSED / PRODUCTION_GREEN

## قاعدة الحقيقة

ابدأ دائمًا من الحالة الحية، بهذا الترتيب:

1. live code على `stage/02-content`.
2. PostgreSQL schema + Alembic migrations.
3. executable tests + exact-SHA GitHub Actions.
4. verified Railway runtime.
5. canonical content/audio/product contracts.
6. وثائق CURRENT في `docs/ops/DOCUMENTATION_INDEX.md`.
7. handoffs/checkpoints المؤرخة القديمة = تاريخ فقط.

إذا تغيّر HEAD بعد هذا الملف، اعتمد الأحدث ولا ترجع للخلف.

## ما هي هِمّة؟

هِمّة منصة ويب عربية RTL تعليمية/بحثية لطلبة الصف الثالث ذوي صعوبات القراءة. لها سطح طالب وسطح مشرف.

رحلة الطالب الحالية:
- دخول بالكود.
- اختبار قبلي 30 بندًا.
- تسكين: أقل من 50 → L1، من 50 إلى أقل من 80 → L2، 80 فأعلى → L3.
- تعلم Core + تقوية مستهدفة حسب الحاجة.
- داخل النشاط: >=80 نجاح، 70..<80 إعادة موجهة، <70 تقوية في المستوى نفسه.
- لا خفض تلقائي.
- L1/L2 يمكن ترقيتهما بعد تحقق شروط الإتقان.
- L3 نهائي ويحتاج 10 Core.
- الاختبار البعدي 30 بندًا بعد إكمال المسار وتفعيل المشرف.

## المحتوى القانوني الحالي

Approval version:
`HIMMA-CONTENT-APPROVAL-2026-09-08`

Runtime:
- 125 عنصرًا.
- 30 قبلي.
- 30 بعدي.
- 30 Core.
- 35 Reinforcement.
- 44 مهارة canonical.

Canonical release SHA الحالي:
`e6c749add3652ca8aa896065218673eaac8a07cd0cbca1e92710f35f14f5a904`

Projection SHA:
`e1d14b0b6102f635820aa7f9a9b074e4f7afd68a02006d0a8ee8a3f29f99670e`

## تحديث القراءة والتشكيل — 2026-09-21

تم اعتماد سياسة قراءة جديدة في طبقة الإصدار القانوني نفسها:

- الحروف والمقاطع والكلمات المفردة تحتفظ بالتشكيل المعتمد.
- العبارات والجمل والنصوص الطويلة تزال منها الحركات الاختيارية لتقليل الازدحام البصري.
- الشدّة المهمة تبقى.
- نفس النص المعتمد ينعكس على learner-visible reading stimulus و`expected_reading_text` وسياقات القراءة، فلا يحدث drift بين العرض ومرجع التسجيل.

الملفات الأساسية:
- `services/api/reading_text_policy_2026_09_21.py`
- `services/api/canonical_release.py`
- `services/api/test_reading_text_policy_2026_09_21.py`
- `packages/content/training/himma_reading_training_corpus_v2026_09_21.jsonl`

ملف التدريب يحتوي 92 سجلًا: أهداف القراءة/التسجيل + سياقات القراءة المعتمدة، ويُختبر ضد الإصدار النهائي.

## إدارة المحتوى في لوحة المشرف — 2026-09-21

الفكرة القديمة التي كانت تجعل المشرف يرى واجهة تشبه واجهة الطالب أُلغيت جذريًا.

المسار بقي تقنيًا:
`/admin/content-preview`

لكن وظيفته واسمه في الواجهة أصبحا:
**المحتوى المعتمد**

المعمارية الحالية:
- Admin Content Review مستقل عن Student serializers.
- read-only فقط؛ لا ينشئ جلسات أو محاولات أو تقدمًا.
- يقرأ المحتوى `approved` المنشور في PostgreSQL.
- يعرض السؤال والتعليمة والتلميح والمثير.
- يعرض الخيارات والإجابة/الإجابات الصحيحة.
- في أنشطة الترتيب يعرض الترتيب الأكاديمي الصحيح.
- في مهام القراءة يعرض النص المطلوب من الطالب تسجيله.
- يعرض الصور المرتبطة بالخيارات.
- يعرض ملفات الصوت القابلة للتشغيل.
- يعرض سياقات القراءة/القصص المعتمدة.
- منظم حسب القبلي → مستويات Core/تقوية → البعدي.
- يدعم البحث النصي الكامل والفلاتر.
- يعرض فروع التقوية المرتبطة بالنشاط الأساسي.
- Student APIs ما زالت تمنع تسريب `is_correct` أو answer metadata.

أهم الملفات:
- `services/api/content_preview.py`
- `apps/web/src/app/admin/(dashboard)/content-preview/page.tsx`
- `services/api/test_content_surface_parity.py`

## الصوت

- Human Supervisor Review هو المرجع الأكاديمي الحالي.
- 54 static audio IDs / 108 binaries (54 WAV + 54 MP3).
- التسجيل pending لا يتحول تلقائيًا إلى نجاح/فشل.
- الطالب يكمل بقية الأسئلة غير المجابة.
- الإنهاء النهائي ينتظر المراجعات المطلوبة.
- rerecord مهمة صريحة مع حفظ التاريخ.
- لا Student Audio Skip.
- لا Temporary Audio Skip.
- لا Fake ASR.
- Production ASR provider ما زال خارجيًا/مؤجلًا.

## أحدث دليل CI على نفس الـSHA الحالي

Exact SHA:
`0bf1390bdbc0a19330c807d82d646424490b5a2b`

- Himma CI — Quality Gate #976 / Run `35541791265`: SUCCESS.
  - Security: SUCCESS.
  - Frontend: TypeScript + ESLint + build SUCCESS.
  - Frontend unit tests: 40 passed.
  - Backend: 902 passed, 5 warnings.
  - Integration Playwright: 23 passed (3.7m).
- M04 Responsive Visual Gate #387 / Run `35541791302`: SUCCESS.
  - responsive smoke: 2 passed.
  - screenshots artifact ID: `10615031736`.
  - artifact digest: `sha256:843fd55e673cdb93d51cfcd0c109d5f15beab7aa07bca926296a9b9338da7930`.
- M09 Release Readiness #252 / Run `35541791274`: SUCCESS.
  - Backend regression: 902 passed, 5 warnings.
  - Browser regression: 23 passed (3.5m).
  - PostgreSQL restore: PASS.
  - restored skills: 44.
  - restored content_items: 125.
  - object store restore: 35 objects.
  - readiness checks: green.

## Production الحالي — Railway

Project: `friendly-dream`  
Environment: `production`  
Branch: `stage/02-content`

نفس SHA الحالي منشور:
`0bf1390bdbc0a19330c807d82d646424490b5a2b`

- Backend service deployment: `f160b611-c157-4a53-9d37-cfae289cfb07` — SUCCESS.
- himma-web deployment: `7f6fec27-3f38-4e21-afd6-c9b62729b168` — SUCCESS.
- PostgreSQL: SUCCESS.
- Redis: SUCCESS.
- himma-audio bucket: present.
- Alembic predeploy: PASS.
- canonical publication: 125 items.
- canonical SHA: `e6c749add3652ca8aa896065218673eaac8a07cd0cbca1e92710f35f14f5a904`.
- `/ready`: HTTP 200.

## ما تبقى

لا توجد دفعة implementation مخفية مفتوحة في التسليم الحالي.

البنود المفتوحة فقط:
- Production ASR/provider/calibration/privacy/governance.
- قرار الاحتفاظ النهائي بتسجيلات/بيانات الأطفال قبل دراسة فعلية.
- تفاصيل البروتوكول البحثي النهائي إن لم يعتمدها المالك.
- manual human screen-reader acceptance.
- custom domain/branding النهائي إن طُلب.

## ترتيب القراءة للمحادثة الجديدة

بعد هذا الملف اقرأ:

1. `docs/handoff/HIMMA_MASTER_HANDOFF_2026-09-21_AR.md`
2. `docs/ops/STATUS.md`
3. `docs/ops/progress.json`
4. `docs/specs/SOURCE_OF_TRUTH.md`
5. `docs/specs/SYSTEM_SPEC.md`
6. `docs/specs/ARCHITECTURE_BASELINE.md`
7. `.agents/rules/00-himma-core.md`
8. `.agents/rules/10-delivery-protocol.md`
9. `.agents/rules/20-security-quality.md`
10. `docs/ops/DECISIONS.md`
11. `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_CURRENT_AR.md`
12. `docs/ops/EVIDENCE_INDEX.md`
13. `docs/ops/RELEASE_DEPLOYMENT_CURRENT_AR.md`
14. `docs/ops/OPEN_ITEMS.md`
15. `docs/maintenance/HIMMA_BRANCH_INVENTORY_2026-09-18_AR.md`
16. `docs/ops/DOCUMENTATION_INDEX.md`

ولفهم آخر تغييرات المحتوى والإدارة مباشرة اقرأ:
- `services/api/reading_text_policy_2026_09_21.py`
- `packages/content/training/himma_reading_training_corpus_v2026_09_21.jsonl`
- `services/api/content_preview.py`
- `apps/web/src/app/admin/(dashboard)/content-preview/page.tsx`
- `services/api/test_content_surface_parity.py`

## بروتوكول الاستلام

1. Fetch للـlive `stage/02-content`.
2. لا تفترض أن SHA هذا ما زال HEAD إذا ظهر أحدث.
3. شغّل/راجع exact-SHA CI عند أي تغيير وظيفي.
4. راجع Railway عند أي مهمة Production.
5. لا تعِد فتح recovery/UX/content reconciliation المغلق بدون regression evidence.
6. أكمل من أول تكليف جديد للمالك فوق هذه الحالة.
