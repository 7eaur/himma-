> **على فرع V2 الحالي:** ابدأ من [الخطة التنفيذية الوحيدة والحالة والتسليم](docs/v2/agent-ops/HIMMA_V2_MASTER_STATUS_GAPS_REMAINING_WORK_HANDOFF_20261028_AR.md). وصف V1 أدناه تاريخي، ولا يحدد نشر V2 أو مهامها الحالية.

# ابدأ من هنا — منصة هِمّة

**آخر مزامنة عامة لـV1:** 2026-10-07
**المستودع:** `7eaur/himma-`

هذه نقطة الدخول الرسمية الوحيدة. عند التعارض تُقدّم الحالة الحية للكود وقاعدة البيانات والاختبارات والتشغيل على أي وثيقة تاريخية.

## الحالة الآن

- الفرع الرسمي المنشور: `stage/02-content`.
- نسخة الإنتاج المؤكدة: `4ecb27590f7c19cbe7823804b9919d91000415ef`.
- فرع الأرشيف: `archive/production-baseline-20260921`.
- فرع العمل: `improvement/himma-unified-v2-20260921`.
- الإنتاج لم يتغير أثناء أعمال التوحيد والتنظيف.
- Railway `friendly-dream / production`: الويب والـBackend وPostgreSQL وRedis في حالة `SUCCESS`.
- تقرير الاستلام الموحد للمحادثة الجديدة: `docs/handoff/HIMMA_CURRENT_PROJECT_HANDOFF_AR.md`.

## دليل فرع التحسين

آخر بوابة كاملة مثبتة قبل الإصلاحات الحالية:

- Himma CI — Quality Gate #1062.
- Run: `35660961118`.
- Evidence SHA: `186307b35cab1ad214b61f2eea601bc66240d4f8`.
- Security: ناجح.
- Frontend type-check/lint/unit/build: ناجح.
- Backend: 906 اختبارًا ناجحًا، 5 تحذيرات.
- Integration Playwright: 23 اختبارًا ناجحًا.

أي descendant توثيقي لاحق يحتاج بوابة جديدة قبل الدمج، لكنه لا يغيّر نسخة الإنتاج تلقائيًا.

فرع التحسين البعيد وصل إلى `a35afb3a370070b7f81f6b9ab61750d35582bac5` ضمن PR #8 Draft. نجحت Security وFrontend وBackend في QG Run `37669828279`؛ فشل Integration لأن توقعًا واحدًا في `vertical-slice.spec.ts` قبل سبب تعليق واحدًا فقط، بينما أعاد API سبب التعليق الصحيح الآخر. صُحح التوقع محليًا لقبول سببي التعليق المحددين دون تخفيف تحقق الشاشة، ويلزم exact-head gate جديد بعد الرفع.

## عقد المنتج المختصر

- منصة عربية RTL لطلبة الصف الثالث ذوي صعوبات القراءة، بسطح طالب وسطح مشرف.
- المسار: كود دخول → قبلي 30 بندًا → تسكين L1/L2/L3 → Core وتقوية مستهدفة → بعدي 30 بندًا.
- التسكين: أقل من 50 إلى L1، ومن 50 إلى أقل من 80 إلى L2، و80 فأعلى إلى L3.
- النشاط: 80 فأعلى نجاح، 70 إلى أقل من 80 إعادة موجهة، وأقل من 70 تقوية من المستوى نفسه.
- لا خفض تلقائي ولا تقوية عشوائية أو عابرة للمستويات.
- التسجيلات الصوتية المعلقة محايدة أكاديميًا، والمرجع الحالي هو مراجعة المشرف البشرية.
- لا Student Audio Skip ولا Temporary Audio Skip ولا Fake ASR.

## المحتوى القانوني

- Approval: `HIMMA-CONTENT-APPROVAL-2026-09-08`.
- 125 عنصر Runtime: 30 قبلي + 30 بعدي + 30 Core + 35 Reinforcement.
- 44 مهارة canonical.
- 54 معرّف صوت ثابت و108 ملفات WAV/MP3.
- Admin Content Review مستقل وقرائي فقط ولا يكتب تقدم الطالب.

## مصادر الحقيقة الحالية

اقرأ بهذا الترتيب فقط:

1. `START_HERE_AR.md`
2. `docs/handoff/HIMMA_CURRENT_PROJECT_HANDOFF_AR.md`
3. `docs/ops/STATUS.md`
4. `docs/ops/progress.json`
5. `docs/specs/SOURCE_OF_TRUTH.md`
6. `docs/specs/SYSTEM_SPEC.md`
7. `docs/specs/ARCHITECTURE_BASELINE.md`
8. `docs/ops/DECISIONS.md`
9. `docs/ops/EVIDENCE_INDEX.md`
10. `docs/ops/RELEASE_DEPLOYMENT_CURRENT_AR.md`
11. `docs/ops/OPEN_ITEMS.md`
12. `docs/ops/DOCUMENTATION_INDEX.md`

كل handoff أو checkpoint أو audit مؤرخ وغير مدرج في الفهرس الحالي هو تاريخ محفوظ فقط، ولا يُستخدم لتغيير السلوك الحالي.

## العمل المفتوح

1. إغلاق بوابة الرأس الحالي وتسجيل دليلها النهائي.
2. أرشفة تنظيمية للتوثيقات المؤرخة دون حذف تاريخ Git.
3. حسم CA-04 أكاديميًا، وتأجيل CA-10 حتى وجود backup/restore معتمد.
4. حسم Worker وبقية seed/repair scripts والأصول المرشحة بدفعات مستقلة.
5. مراجعة بصرية وسيناريوهات فعلية ثم تجهيز Release Candidate قبل أي دمج أو نشر.

النسخ الاحتياطي الإنتاجي مؤجل بقرار المالك، لذلك تُمنع migrations أو عمليات حذف بيانات مدمرة خلال هذه المرحلة.


## مسار تطوير V2 (توثيق حديث مستقل — 2026-10-18)

**فرع V2:** `v2/01-learning-foundation-20261007`. **ابدأ في مهام V2 من `docs/v2/README.md`**، ثم اقرأ `docs/v2/20_VERIFIED_CONTENT_BASELINE_AND_GAPS_AR.md` و`docs/v2/DECISIONS_AR.md` و`docs/v2/09_IMPLEMENTATION_ROADMAP_AR.md` و`docs/v2/21_EXECUTION_PROGRESS_AR.md`.

بنك V2 مؤلف ومدقق بنيويًا: **19 درسًا، 12 دعمًا، 300 بند**. **ليس مستوردًا أو منشورًا**، ولا يزال اعتماد الوسائط والتحكيم التربوي وRuntime مطلوبًا. الحالة المنشورة لـV1 المذكورة أعلاه **حقيقة موثقة قديمة يجب إعادة التحقق منها حيًا عند P01**، لا إثباتًا بأن V2 منشورة. لا تخلط مراحل V2 في `docs/v2` بحالة تشغيل V1 في `docs/ops`.
