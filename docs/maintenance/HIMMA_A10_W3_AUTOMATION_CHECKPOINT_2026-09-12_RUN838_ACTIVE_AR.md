# هِمّة — A10/W3 Automation Checkpoint — Run #838 Active

**التاريخ:** 2026-09-12  
**المستودع:** `7eaur/himma-`  
**فرع التنفيذ:** `audit/comprehensive-repository-review-2026-09-10`  
**الحالة:** `W3 ACTIVE / NOT GREEN — RUN #838 IN PROGRESS — NO MERGE / NO DEPLOY`

## الإغلاق المثبت قبل هذه الدفعة

- Run #837 / ID `34715934635` = **SUCCESS** على exact SHA `5b6bf14e2970999c680dcfe40cf383f7d0992d11`.
- بذلك `AUD-A04-002` مغلق بدليل Playwright تنفيذي يثبت أن فشل rewards/journey/adaptation-history الجزئي يبقى explicit + retryable، ولا يتحول إلى zero/empty/progress مضلل، وأن retry يعيد الحالة الحقيقية.

## ملاحظة ذرية مهمة — AUD-PERF-004

بدأت محاولة نقل الخطوط إلى `next/font/google`، لكن تبين أن الإصلاح الصحيح يحتاج تعديل CSS كاملًا مع إزالة runtime `@import` وليس تعديل `layout.tsx` وحده. لذلك تم **إرجاع التغيير بالكامل قبل فتح batch التالية**:

- commit أولي: `3ea66ed12139ed38846c46adc9e9d04a74276a03`
- revert ذري: `e9cb07ebefb75473d2c2afb57b775f0ee01551aa`

النتيجة التنفيذية: لا يوجد تغيير فعلي في `layout.tsx` مقارنة بما قبل المحاولة، و`AUD-PERF-004` ما يزال **OPEN**. لا تعتبر هذه المحاولة إغلاقًا أو تقدمًا في gap الخطوط.

## Batch الحالية — AUD-A04-003

تم اختيار gap واحدة فقط: canonical Journey UI scenarios.

### التغيير

أضيف الملف:

`apps/web/tests/e2e/student-detail-journey-states.spec.ts`

الاختبارات تثبت أن Student Detail يعرض canonical `level.state` مباشرة ولا يعيد استنتاج completion من `current_level`:

1. Placement skipped:
   - L1/L2 = `skipped`.
   - يظهر `تم تجاوزه وفق نقطة البداية`.
   - لا يظهر `مكتمل` لهما.
2. Manual override pointer:
   - `current_level = 3` لا يصنع historical completion.
   - L1/L2 يبقيان `locked`، L3 = `ready`، ولا توجد أي بطاقة `completed` مصطنعة.
3. Early promotion:
   - L1 canonical `completed` عند 6/10 يبقى مكتملًا كما يقرره Level Completion owner.
   - L2 `active` يبقى قيد التعلم.
4. Completed L3:
   - canonical completed states للمستويات الثلاثة تعرض كـcompleted، وL3 يعرض 10/10.

هذه الدفعة لا تغير academic logic ولا API contract؛ هي executable UI contract فوق canonical Journey projection.

### Code SHA

`08ae3ce4ca0634a448943d7af03dcd8137b6ac8f`

Commit: `test(admin): verify canonical journey UI states`

Helper branch `stage/a10-w3-ci` يشير إلى exact SHA نفسه.

### Quality Gate

- Run #838
- Run ID `34717561661`
- Exact SHA `08ae3ce4ca0634a448943d7af03dcd8137b6ac8f`
- الحالة عند كتابة checkpoint: `IN PROGRESS`.

## قاعدة الاستكمال

لا تبدأ أي gap جديدة بينما Run #838 ما يزال ACTIVE.

المهمة التالية تبدأ بفحص Run #838:
- إذا SUCCESS: أغلق `AUD-A04-003` بواسطة exact-SHA executable evidence ثم اختر gap W3 واحدة فقط.
- إذا FAILURE: افتح jobs وحدد أول failure حقيقي وأصلحه من root cause؛ لا تضعف الاختبارات أو تحول canonical scenario إلى fixture أسهل لإخفاء failure.
- إذا ما يزال ACTIVE: لا تغيّر كود؛ افحص الحالة فقط.

## Remaining W3 بعد نجاح #838

- `AUD-A04-001` remaining AdminUI/presentation ownership.
- `AUD-A04-005` deterministic responsive matrix 320/360/390/430/768/Desktop.
- `AUD-A04-008` filtered audio-review context E2E.
- `AUD-PERF-004` local/build-time fonts؛ runtime Google Fonts import ما يزال موجودًا.
- cross-device/scenario integrity.
- final exact-SHA W3 Green gate.

## القيود

No Docker. No fake ASR. No Temporary Audio Skip. No history deletion. No Speech/Pronunciation Lab merge. No final merge. No Deploy/Railway/Production. No PASS claim without exact-SHA executed evidence. A11 خارج الجدولة الحالية.
