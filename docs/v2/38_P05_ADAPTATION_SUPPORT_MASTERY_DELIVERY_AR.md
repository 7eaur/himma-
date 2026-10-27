# هِمّة V2 — تسليم P05: التكيف والدعم والأدلة والانتقال

**التاريخ:** 2026-10-23
**الحالة:** ready_for_review — لا بدء P06، لا تفعيل محتوى، ولا نشر
**مرجع التنفيذ:** اعتمد المالك P04 بعبارة «تم»، ثم نُفذت P05 داخل نفس FastAPI/Next/SQLAlchemy وLessonSession.
**Implementation SHA:** 16da82441de62dd3b6b2f77b7886c0a357bff8d4

## 1. النتيجة

أصبحت نتيجة التحقق المستقل في V2 تتحول إلى قرار تعليمي خادمي، مثبت بالإصدار وقابل للتفسير:

- النجاح المستقر يفتح الدرس التالي ويحدث StudentJourney حتى posttest_ready بعد آخر درس.
- خطأ منفرد لا يرسل الطالب مباشرة إلى التقوية؛ يفتح تحققًا إضافيًا من بندين بديلين للـfocus نفسه.
- تكرر الفجوة نفسها يفتح تدريب دعم مركزًا ثم تحققًا من بندين فقط.
- فشل التحقق الإضافي يحول الإسناد نفسه إلى دعم؛ وفشل تحقق الدعم يصعّد مرة واحدة إلى supervisor_hold بدل loop.
- القراءة والكتابة المعلقتان لا تعدان نجاحًا أو رسوبًا.
- mapping غير المعتمد يفشل مغلقًا إلى المشرف؛ لا اختيار تخميني.
- GET لحالة الطالب read-only؛ القرار ينشأ عند أمر الإجابة فقط.
- دعم مستوى سابق لا يغير مستوى الرحلة ولا يخفض الطالب.
- direct URL لا يفتح درسًا غير current_lesson_id.

السياسة تحمل النسخة himma-v2-adaptation/1-candidate. التنفيذ مختبر، لكن الاعتماد التربوي النهائي ومعايرة سياسة الإطلاق لم يحدثا بعد.

## 2. القرار حسب الدليل

| الدليل | القرار | حالة الطالب |
|---|---|---|
| كل IC صحيح ومراجع | next_lesson | اكتمال الدرس وفتح التالي |
| خطأ واحد له mapping | additional_check | بندا تحقق بديلان، بلا دعم فوري |
| تكرر focus نفسه | targeted_support | تدريب focus ثم بندا تحقق |
| قراءة/كتابة pending | waiting_review | حفظ محايد |
| mapping غير معتمد | supervisor_hold | حفظ التقدم وتدخل المشرف |
| نجاح التحقق أو الدعم | next_lesson | فتح التالي |
| فشل التحقق الإضافي | targeted_support | الإسناد نفسه |
| فشل تحقق الدعم | supervisor_hold | تصعيد محدود |

لا تستخدم السياسة نسب V1 أو ثوابتها 10/6، ولا تعتبر hint أو GP دليل إتقان.

## 3. المعالجة الهندسية

- سياسة خالصة في services/api/v2_adaptation_policy.py.
- mapping صريح وفشل غموض مغلق في v2_content/adaptation_mapping.py مع حارس compiler لكل 75 IC؛ hold معلن واحد هو L1-03-IC-A04.
- command/query runtime في v2_adaptation_runtime.py؛ GET الطالب read-only، وتفسير قرار للمشرف.
- توسعة المشغل نفسه للمراحل additional_check/support_practice/support_check؛ لا Player موازٍ.
- قفل الرحلة للـ19 درسًا، وفصل skipped بسبب التسكين عن done.
- جداول support_assignments وskill_evidence وadaptation_decisions_v2 وربط response بالدعم عبر migration 0018.
- قيد إسناد نشط واحد وسقف تحقق واحد يمنعان التكرار والحلقة.

## 4. المحافظة على V1 وهوية هِمّة

- حُفظ منع demotion، pending المحايد، التاريخ القابل للتدقيق، الدعم المحدد، سقف المحاولة ودور المشرف.
- لم تُحذف صفحات V1 للتقوية أو المكافآت أو المراجعة أو التقارير، ولم يُنشأ تطبيق أو DB أو محرك تعلم موازٍ.
- بقيت FastAPI/PostgreSQL/Alembic وStudentJourney وLessonSession وInteractionPlayer وBFF/Auth نفسها.
- لم تتغير الشعارات أو الشخصيات أو الألوان أو الخطوط أو الأصوات التعليمية.
- لا RETIRE_APPROVED ولا حذف بيانات طلاب أو تسجيلات.
- تبقى مكافآت V1 محفوظة، لكن P05 لا تمنح مكافأة V2 من سياسة candidate قبل اعتماد الحدث المستقر؛ يمنع ذلك مكافأة GP أو pending أو refresh.

## 5. الاختبارات والأدلة

| البوابة | النتيجة |
|---|---|
| P02–P05 المستهدفة | PASS: 35 |
| انحدار التكيف/الصوت/الرحلة/التقوية/V2 محليًا | PASS: 627؛ تحذير TestClient deprecation واحد |
| اختبارات P05 الجديدة | PASS: 9 |
| Frontend Jest | PASS: 13 suites / 61 tests |
| TypeScript / ESLint / Next build | PASS |
| npm audit production | PASS: صفر ثغرات |
| PostgreSQL upgrade/downgrade/upgrade + drift | PASS في Quality Gate |
| CI Quality Gate | success — run 39995806118 |
| M04 Responsive Visual Gate | success — run 39995805915 |
| M09 Release Readiness Gate | success — run 39995806009 |

كل البوابات مرتبطة بالـimplementation SHA نفسه: 16da82441de62dd3b6b2f77b7886c0a357bff8d4. شمل Quality الأمن والواجهة وBackend/PostgreSQL وIntegration/Playwright، وشمل M09 انحدار Backend وBrowser والنسخ والاستعادة.

ظهر محليًا عطل في ملف SQLite المشترك بعد تشغيل منقطع؛ أعيدت الحزمة على قاعدة مؤقتة معزولة فنجحت 627/627. لا يُخفى هذا كنجاح suite محلية كاملة، وPostgreSQL في CI هو دليل migration/runtime الحاكم.

## 6. حالة معايير P01-E

| المعيار | الحالة الدقيقة |
|---|---|
| P-E01 policy/version بلا عتبات V1 | PARTIAL: مختبر، والاعتماد التربوي غير منفذ |
| P-E02 GP والخطأ الواحد | IMPLEMENTED_TESTED |
| P-E03 mapping أو hold صريح | IMPLEMENTED_TESTED |
| P-E04 focus/تحققان/عودة | IMPLEMENTED_TESTED |
| P-E05 دعم سابق بلا demotion | IMPLEMENTED_TESTED خادميًا؛ E2E الكامل P09 |
| P-E06 pending وReviewTask | PARTIAL: pending محايد؛ القرار/rerecord في P08 |
| P-E07 GET/idempotency | IMPLEMENTED_TESTED؛ race الموسع P09 |
| P-E08 hold والتنبيه | PARTIAL: hold وتفسير admin؛ التنبيه والحل P06/P08 |
| P-E09 reward/report | PARTIAL إلى P07/P09 |
| P-E10 visual/axe | PARTIAL: M04 و390/1440؛ المصفوفة الكاملة P09/P10 |

## 7. الحدود والمتبقي

- P06: القبلي/البعدي، التسكين الفعلي، CurrentAction الشامل، إنهاء المستويات وواجهة المشرف الأساسية.
- P07: جاهزية ربط الميديا وجرد النواقص واختبار تبديل ملفات الاختبار؛ التقارير الأساسية ضمن P06، وتكامل المكافآت النهائي ضمن P09.
- P08: ReviewTask للقراءة/الكتابة، القرار البشري، rerecord/rewrite والتنبيه.
- P09: رحلة E2E كاملة، race/offline والمقاسات وaxe وparity.
- P10: الأصول النهائية وQA الصوتي/البصري/التربوي.
- لا يعني نجاح التنفيذ اعتماد المحتوى أو سياسة تربوية نهائية أو جاهزية نشر.

## 8. قرار المراجعة

P05=ready_for_review بعد إغلاق البوابات exact-SHA. نتوقف هنا؛ لا تبدأ P06 قبل قول المالك «تم».

**تحديث 2026-10-23:** اعتمد المالك P05 بعبارة «تم» وبدأت P06 وفق التسلسل. لا يغير ذلك حدود السياسة المرشحة أو الحاجة إلى اعتماد تربوي نهائي.
