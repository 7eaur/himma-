# هِمّة V2 — تقرير تسليم إصلاحات P06 الجذرية وفحص القبول

**التاريخ:** 2026-10-24  
**الفرع:** `v2/01-learning-foundation-20261007`  
**آخر كود عند إنشاء التقرير:** `e9d2b540a6ca9abd24acb157d03977795e25a4fd`  
**حالة P06:** `ready_for_review — fixes implemented; final verification pending`  
**حالة P07:** `not_started` — محظور الانتقال قبل قول المالك «تم».

## 1. لماذا أُعيد فتح التنفيذ؟

التقرير المستقل `43_P06_INDEPENDENT_SUPERVISION_ACCEPTANCE_REVIEW_AR.md` وثق عيبين مانعين `P0` وثلاث فجوات `P1`. لم تُنقل المنصة أو يُنشأ مشروع موازٍ. جميع التغييرات داخل نفس فرع V2 ونفس Web/API/PostgreSQL والتخزين الصوتي الخاص.

## 2. الإصلاحات المنفذة

| القضية | الإجراء | الدليل |
|---|---|---|
| SUP-P06-01 | طابور V2 يعرض اسم الطالب/سؤاله ومراجع التصحيح وإجابة الكتابة؛ بث التسجيل من `/v2/assessments/admin/responses/{id}/audio` بعد `get_current_user` والتحقق من ارتباط التسجيل بالطالب. يمنع اعتماد النتيجة عند غياب الدليل أو فقد الملف من S3. UI نموذج ملاحظة حقيقي بدل `prompt`. | `services/api/v2_assessment_runtime.py`، `apps/web/src/app/admin/(dashboard)/v2-assessments/page.tsx`، `services/api/test_v2_assessment_runtime.py` |
| SUP-P06-02 | استدعاء خدمة V1/V2 المشتركة `mark_official_completed_attempt` تحت قفل Student؛ إلغاء صفة official عن السابق؛ إنشاء فهرس جزئي فريد رسمي لكل (student,kind) بترحيل `0020`، إصلاح أعلام التاريخ المكررة فقط دون حذف المحاولات/درجاتها. | `services/api/assessment_retake.py`، `db/models.py`، Alembic `0020_v2_official_attempt_guard.py` |
| SUP-P06-03 | قائمة مؤهلة للتسكين باسم الطالب ونتيجة كل مجموعة مهارات ومبرر واضح ومستوى 1–3. API يشترط 30 إجابة مكتملة بلا pending ويرفض القرار المكرر. | `/admin/placement-queue`، UI AdminShell |
| SUP-P06-04 | يخزن استيراد المحتوى `bank_snapshot` بإصدار وبصمة DB ويربط به سؤال/مرجع/وسائط أي جلسة؛ الإصدار التاريخي السابق بلا snapshot لا يقرأ إصدارًا جديدًا بغير تطابق كامل للـchecksum (fail-closed). | `v2_content/importer.py`، `_session_release` في تقييم V2 |
| SUP-P06-05 | يحد الطابور وصفحة التسكين إلى 100 عنصر لكل استعلام ويستخدم pagination وتجميع دليل الصوت وإصدار البنك ونتائج المهارات، ويحسب المتوسطات في SQL بالتجميع بدل جمع كل الجلسات في Python. Auth researcher مطلوب لكل مسار. | `review_queue`، `placement_queue`، `reports_summary` |

**إصلاح إضافي:** استعادة المحاولة لا تتجاهل سجل V1؛ محاولة V2 ليست محاولة رقم 1 جديدة إن كان الطالب أكمل V1، ولا تفتح posttest دون رحلة V2. حماية ضد حساب نتائج ناقصة.

## 3. سلسلة الأكواد

1. `556246da8c3c54d72c947a7323a1cd8d280f389e` — backend evidence/official/migration.
2. `7df06cf66b5af0b39097e1e1b7c920604d763262` — workspace للمشرف.
3. `b0b84977eff8f63014ff45a92b9b98aa27628b5c` — immutable candidate snapshot.
4. `0208e7c365b8e9fbf2c56cb16f6b26c770c0088f` — اختبارات P06.
5. `16df3fcbb0fc9820cef264e1d64c32597fcb04c4` — إصلاح lint مكتشف من CI.
6. `88e858026f12e6ce798fb51861a73cc0925de93c` — تداخل تاريخ V1/V2.
7. `7d618cc55329b810035e59ae8704e6d8c76422f5` — batching / pagination.
8. `0144ea1baf3bad0e899001bd60afbbf208a71b4e` — S3 verification قبل الاعتماد.
9. `e9d2b540a6ca9abd24acb157d03977795e25a4fd` — integrity gate للـ30 بندًا.

## 4. الفحوص والحالة عند كتابة التقرير

- CI الأول `556246da...`: `frontend / backend / security SUCCESS` بعد فحص وظائف P0 الأصلية؛ Integration كان قيد التشغيل. لا ينطبق النجاح المبكر تلقائيًا على SHA الأخير.
- إصلاح ESLint بعد فشل إصدار الواجهة السابق موثق في `16df3fc...`، وحزمة frontend على هذا الإصدار نجحت.
- بوابات M04 المتعددة على إصلاحات متقدمة أعادت `SUCCESS`؛ نتيجة SHA الأخير وM09/CI النهائية **مطلوبة**.
- اختبارات مضافة: authorization للدليل والإدارة، وجود التسجيل والتحقق منه قبل grade، إصلاح تاريخ الرسمي ومتوسطات التقارير، snapshot عند تبدل بنك الأسئلة، عدم تجاوز V1، منع المراجعة مع غياب دليل.
- Railway Preview: نفس المشروع `968ce1df-b94f-4de8-a365-88e5073d3d11` / Web+API+Postgres+Redis+Bucket. النشر التجريبي التلقائي لا يعني موافقة إصدار نهائي. آخر deployed SHA لـWeb قد يختلف عن API لأن watchPatterns مستقلة.

## 5. الشروط المتبقية قبل قبول P06

1. إثبات CI + M04 + M09 ناجحة على SHA وظيفي واحد أخير، مع هجرة PostgreSQL وحماية official Index.
2. Browser manual/Playwright على واجهات مراجعة الصوت والكتابة والتسكين، وسلامة Range، واستجابة الهاتف وRTL وkeyboard.
3. فحص Live Trial: الدخول الحقيقي للمشرف، عرض الدليل وسماع ملف موجود، منع ملف مفقود، ومطابقة Web/API deployed SHA المقصود.
4. اختبار end-to-end كامل لمسار طالب اصطناعي دون كشف مفتاح الإجابة، وعدم تراجع V1 (P09 سيعمم لاحقًا).
5. الميديا النهائية، المراجعة السمعية/التربوية والاعتماد الأكاديمي **غير محسومة** ولا تغير P06 لموافقة نهائية. الفيديو المشترك `TEST_ONLY` ليس 19 فيديو حقيقيًا.
6. سياسة تكوين **multi-cohort/claim** إن أُضيف مشرفون متعددون لاحقًا، ودورة مراجعة rerecord/history المتقدمة ضمن P08؛ لا تجاوز لها داخل P06.

## 6. قرار التنفيذ

تم تحويل العوائق المذكورة من «لا إصلاح» إلى **«إصلاحات مرفوعة وجاهزة للتحقق»**. لا تُختم `P06=approved` إلا بعد دليل اختبارات وQA نهائي وقول المالك «تم». `P07=not_started`، ولا نشر إنتاج معتمد.
