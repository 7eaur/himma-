# هِمّة — A10/W3 Automation Checkpoint — Run #837 Active

**التاريخ:** 2026-09-12  
**المستودع:** `7eaur/himma-`  
**فرع التنفيذ:** `audit/comprehensive-repository-review-2026-09-10`  
**الحالة:** `W3 ACTIVE / NOT GREEN — RUN #837 IN PROGRESS — NO MERGE / NO DEPLOY`

## الإغلاق المثبت قبل هذه الدفعة

- Run #836 / ID `34714516971` = **SUCCESS** على exact SHA `818930aef34fd26a5cc059e316b0f7224844e542`.
- بذلك `AUD-A04-006` مغلق بدليل Playwright تنفيذي يغطي mobile Admin dialog: focus entry، Tab/Shift+Tab trap، Escape close، trigger focus restoration، `aria-expanded`، وbody scroll lock/unlock.

## Batch الحالية — AUD-A04-002

تم اختيار gap واحدة فقط: partial-source failure/retry regressions في Student Detail.

### التغيير

أضيف الملف:

`apps/web/tests/e2e/student-detail-partial-source-errors.spec.ts`

الاختبارات تستخدم مشرفًا وطالبًا حقيقيين، وتحقن فشلًا مؤقتًا لمصدر ثانوي واحد في كل سيناريو ثم تسمح للمحاولة التالية بالمرور. العقود المثبتة:

1. Rewards failure:
   - النجوم تظهر `—` أثناء عدم توفر المصدر ولا تتحول إلى صفر مضلل.
   - يظهر `تعذر تحميل المكافآت` مع `إعادة المحاولة`.
   - retry يستعيد المصدر الحقيقي، ثم يظهر الصفر الحقيقي لطالب جديد.
2. Journey failure:
   - يظهر خطأ `تعذر تحميل المسار الأكاديمي`.
   - لا يُعرض progressbar مشتق أو مزيف أثناء غياب canonical Journey.
   - retry يستعيد canonical Journey ثم يظهر progressbar الحقيقي.
3. Adaptation history failure:
   - يظهر `تعذر تحميل سجل التكيف`.
   - لا تظهر حالة empty الناجحة أثناء الخطأ.
   - retry يستعيد المصدر، ثم تظهر حالة `لا يوجد قرار تكيف محفوظ بعد.` الحقيقية لطالب جديد.

لم يتغير implementation أو API contract أو academic state؛ الدفعة تضيف executable regression فقط للسلوك الموجود.

### Code SHA

`5b6bf14e2970999c680dcfe40cf383f7d0992d11`

Commit: `test(admin): verify student detail partial-source retries`

Helper branch `stage/a10-w3-ci` يشير إلى exact SHA نفسه.

### Quality Gate

- Run #837
- Run ID `34715934635`
- Exact SHA `5b6bf14e2970999c680dcfe40cf383f7d0992d11`
- الحالة عند كتابة checkpoint: `IN PROGRESS`.

## قاعدة الاستكمال

لا تبدأ أي gap جديدة بينما Run #837 ما يزال ACTIVE.

المهمة التالية تبدأ بفحص Run #837:
- إذا SUCCESS: أغلق `AUD-A04-002` بواسطة exact-SHA executable evidence ثم اختر gap W3 واحدة فقط.
- إذا FAILURE: افتح jobs وحدد أول failure حقيقي وأصلحه من root cause؛ لا تضعف الاختبارات ولا تحوّل failure إلى expected success.
- إذا ما يزال ACTIVE: لا تغيّر كود؛ افحص الحالة فقط.

## Remaining W3 بعد نجاح #837

- `AUD-A04-001` remaining AdminUI/presentation ownership.
- `AUD-A04-003` canonical Journey scenarios.
- `AUD-A04-005` deterministic responsive matrix 320/360/390/430/768/Desktop.
- `AUD-A04-008` filtered audio-review context E2E.
- `AUD-PERF-004` local/build-time fonts؛ runtime Google Fonts import ما يزال موجودًا.
- cross-device/scenario integrity.
- final exact-SHA W3 Green gate.

## القيود

No Docker. No fake ASR. No Temporary Audio Skip. No history deletion. No Speech/Pronunciation Lab merge. No final merge. No Deploy/Railway/Production. No PASS claim without exact-SHA executed evidence. A11 خارج الجدولة الحالية.
