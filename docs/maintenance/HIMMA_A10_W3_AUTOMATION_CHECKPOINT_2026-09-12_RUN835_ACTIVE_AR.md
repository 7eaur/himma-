# هِمّة — A10/W3 Automation Checkpoint — Run #835 Active

**التاريخ:** 2026-09-12  
**المستودع:** `7eaur/himma-`  
**فرع التنفيذ:** `audit/comprehensive-repository-review-2026-09-10`  
**الحالة:** `W3 ACTIVE / NOT GREEN — RUN #835 IN PROGRESS — NO MERGE / NO DEPLOY`

## نقطة البدء

- Documentation HEAD عند البدء: `a67d31ebff1d68f323a95e62dde8a6b15d9c7a1b`.
- آخر gate مغلق: Run #834 / ID `34710221396` على SHA `c180146b10467199e6833bacb77873eddcea2143` = SUCCESS.
- لم يوجد batch أو CI أحدث نشط قبل بدء هذه الدفعة.

## Batch الحالية — AUD-A11Y-003

تم اختيار gap واحدة فقط: executable verification لدلالات progressbar في Student Detail.

### التغيير

الملف:
`apps/web/tests/e2e/accessibility-integration.spec.ts`

أضيف اختبار Playwright حقيقي يقوم بـ:
- تسجيل دخول المشرف.
- إنشاء طالب فعلي من واجهة الإدارة.
- فتح Student Detail ثم تبويب `المسار والتقدم`.
- الوصول إلى progressbar عبر role وaccessible name.
- التحقق من `aria-valuemin=0`.
- التحقق أن `aria-valuemax` رقم موجب.
- التحقق أن `aria-valuenow` رقم ضمن `[0,max]`.
- التحقق أن `aria-valuetext` يطابق القيمة المرئية `${now} من ${max}`.

لم يتم تغيير JSX أو العقد الأكاديمي؛ المصدر كان يحتوي semantics صحيحة، وكانت الفجوة هي غياب executable evidence.

### Code SHA

`50a02d250adc1f45a0e1f2577b40dd59ce18c0c1`

Commit: `test(a11y): verify student progressbar semantics`

تم تحريك helper branch `stage/a10-w3-ci` إلى exact SHA نفسه.

### Quality Gate

- Run #835
- Run ID `34712992018`
- Exact SHA `50a02d250adc1f45a0e1f2577b40dd59ce18c0c1`
- الحالة عند كتابة checkpoint: `IN PROGRESS`.

## قاعدة الاستكمال

لا تبدأ أي gap جديدة بينما Run #835 ما يزال ACTIVE.

المهمة التالية تبدأ بفحص Run #835:
- إذا SUCCESS: أغلق `AUD-A11Y-003` بواسطة exact-SHA executable evidence ثم اختر gap W3 واحدة فقط.
- إذا FAILURE: افتح jobs وحدد أول failure حقيقي وأصلحه من root cause؛ لا تضعف الاختبار.
- إذا ما يزال ACTIVE: لا تغيّر كود؛ افحص الحالة فقط.

## Remaining W3 بعد هذه الدفعة

لا تعتبر `AUD-A11Y-003` مغلقة حتى ينجح #835. بقية المفتوح:
- `AUD-A04-001` remaining AdminUI/presentation ownership.
- `AUD-A04-002` partial-source error/retry regressions.
- `AUD-A04-003` canonical Journey scenarios.
- `AUD-A04-005` responsive matrix 320/360/390/430/768/Desktop.
- `AUD-A04-006` final keyboard/dialog regression.
- `AUD-A04-008` filtered audio-review context E2E.
- `AUD-PERF-004` local/build-time fonts.
- cross-device/scenario integrity.
- final exact-SHA W3 Green gate.

## القيود

No Docker. No fake ASR. No Temporary Audio Skip. No history deletion. No Speech/Pronunciation Lab merge. No final merge. No Deploy/Railway/Production. No PASS claim without exact-SHA executed evidence.
