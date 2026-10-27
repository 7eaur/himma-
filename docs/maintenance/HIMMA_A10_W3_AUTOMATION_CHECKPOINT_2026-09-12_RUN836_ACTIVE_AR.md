# هِمّة — A10/W3 Automation Checkpoint — Run #836 Active

**التاريخ:** 2026-09-12  
**المستودع:** `7eaur/himma-`  
**فرع التنفيذ:** `audit/comprehensive-repository-review-2026-09-10`  
**الحالة:** `W3 ACTIVE / NOT GREEN — RUN #836 IN PROGRESS — NO MERGE / NO DEPLOY`

## ما أُغلق قبل هذه الدفعة

- Run #835 / ID `34712992018` = **SUCCESS** على exact SHA `50a02d250adc1f45a0e1f2577b40dd59ce18c0c1`.
- بذلك `AUD-A11Y-003` مغلق بدليل تنفيذي: Playwright تحقق من progressbar role/name و`aria-valuemin/max/now/valuetext` وتطابق القيمة المرئية.

## Batch الحالية — AUD-A04-006

تم اختيار gap واحدة فقط: final keyboard/dialog regression لقائمة المشرف على الجوال.

### التغيير

أضيف الملف:

`apps/web/tests/e2e/admin-dialog-keyboard.spec.ts`

الاختبار يستخدم جلسة مشرف حقيقية ويثبت على viewport 390×844 أن:

- زر `فتح القائمة` يملك حالة `aria-expanded` الصحيحة.
- فتح القائمة ينقل التركيز إلى أول عنصر قابل للتركيز داخل dialog.
- body scroll يصبح locked أثناء modal.
- `Shift+Tab` من أول عنصر يلتف إلى آخر عنصر داخل dialog.
- `Tab` من آخر عنصر يلتف إلى أول عنصر.
- `Escape` يغلق dialog.
- التركيز يعود إلى trigger بعد الإغلاق.
- `aria-expanded` يعود إلى false وscroll lock يزول.

لم يتم تغيير implementation؛ `useAccessibleDialog` كان يملك lifecycle الصحيح، والفجوة الحالية هي executable final regression.

### Code SHA

`818930aef34fd26a5cc059e316b0f7224844e542`

Commit: `test(a11y): verify admin dialog keyboard lifecycle`

تم تحريك helper branch `stage/a10-w3-ci` إلى exact SHA نفسه.

### Quality Gate

- Run #836
- Run ID `34714516971`
- Exact SHA `818930aef34fd26a5cc059e316b0f7224844e542`
- الحالة عند كتابة checkpoint: `IN PROGRESS`.

## قاعدة الاستكمال

لا تبدأ أي gap جديدة بينما Run #836 ما يزال ACTIVE.

المهمة التالية تبدأ بفحص Run #836:
- إذا SUCCESS: أغلق `AUD-A04-006` بواسطة exact-SHA executable evidence ثم اختر gap W3 واحدة فقط.
- إذا FAILURE: افتح jobs وحدد أول failure حقيقي وأصلحه من root cause؛ لا تضعف الاختبار.
- إذا ما يزال ACTIVE: لا تغيّر كود؛ افحص الحالة فقط.

## Remaining W3 بعد هذه الدفعة

- `AUD-A04-001` remaining AdminUI/presentation ownership.
- `AUD-A04-002` partial-source failure/retry regressions.
- `AUD-A04-003` canonical Journey scenarios.
- `AUD-A04-005` responsive matrix 320/360/390/430/768/Desktop.
- `AUD-A04-008` filtered audio-review context E2E.
- `AUD-PERF-004` local/build-time fonts؛ runtime Google Fonts import ما يزال موجودًا.
- cross-device/scenario integrity.
- final exact-SHA W3 Green gate.

## القيود

No Docker. No fake ASR. No Temporary Audio Skip. No history deletion. No Speech/Pronunciation Lab merge. No final merge. No Deploy/Railway/Production. No PASS claim without exact-SHA executed evidence.
