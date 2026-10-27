# هِمّة — A10 / W5 — Media Cleanup Ownership

**التاريخ:** 2026-09-16  
**النطاق:** `AUD-MEDIA-003`, `AUD-MEDIA-004`, `AUD-MEDIA-005`  
**القاعدة:** لا حذف أو إعادة استخدام أو كسر URL لمجرد أن الأصل غير مستخدم مباشرة أو أن bytes مكررة.

## مصادر القرار

- `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
- `docs/maintenance/HIMMA_A02_A06_STATIC_INVENTORY_2026-09-10.md`
- الكود الحالي و`apps/web/src` و`apps/web/public`

## AUD-MEDIA-003 — approved unused education images

Master Gap Register يثبت أن هناك 23 صورة تعليمية approved غير مستخدمة حاليًا، وأن الخطر هو اعتبار `unused` مساويًا لـ`orphan`.

**القرار التنفيذي:** هذه الأصول تبقى `APPROVED_RESERVE`. لا تُحذف، ولا تُعاد دلالتها، ولا تُربط بسؤال فقط من أجل التخلص من حالة unused. استعمال أي أصل لاحقًا يحتاج حاجة دلالية مثبتة وعقد محتوى/وسائط صحيح.

**الحالة التنفيذية:** `CLOSED — PRESERVE RESERVE / NO DESTRUCTIVE CHANGE`.

## AUD-MEDIA-004 — duplicate character URLs

الجرد الثابت يثبت خمس مجموعات SHA متطابقة بين المسارات المسطحة القديمة والمسارات المنظمة تحت `characters/boy/`:

- `boy-encourage.png` ↔ `boy/encourage.png`
- `boy-explain.png` ↔ `boy/explain.png`
- `boy-success.png` ↔ `boy/success.png`
- `boy-try-again.png` ↔ `boy/try-again.png`
- `boy-welcome.png` ↔ `boy/welcome.png`

الكود الحالي يشير إلى المسارات المنظمة `characters/boy/...`؛ لذلك تُعامل هذه المسارات باعتبارها **canonical runtime URLs**. النسخ المسطحة القديمة تبقى **compatibility aliases** ولا تُحذف في W5، لأن التطابق الثنائي وعدم وجود direct source ref لا يثبتان غياب روابط خارجية/مخزنة تاريخيًا.

هذا يحسم owner/path الصحيح دون إدخال redirect أو حذف قد يكسر تاريخًا أو رابطًا خارجيًا.

**الحالة التنفيذية:** `CLOSED — CANONICAL URL OWNERSHIP ESTABLISHED / LEGACY ALIASES RETAINED`.

## AUD-MEDIA-005 — 17 public files with zero direct refs

الجرد الثابت يصف 17 ملفًا في `apps/web/public` بلا direct reference من `apps/web/src`، ويذكر صراحة أن ذلك لا يثبت أنها dead؛ قد تكون build defaults أو runtime/dynamic/external paths.

**القرار التنفيذي:** لم يثبت في W5 وجود ملف يحقق شرط الحذف الآمن كاملًا (`source + build/runtime + path/external compatibility proof`). لذلك لا يُحذف أي واحد من الـ17 في هذه الموجة. أي cleanup مستقبلي يحتاج evidence مستقل لكل ملف، وليس bulk deletion.

**الحالة التنفيذية:** `CLOSED — NO FILE QUALIFIED FOR SAFE DELETION`.

## Verification / safety

- لا تغيير في semantic media contracts.
- لا حذف لأي public/approved asset.
- لا تغيير في canonical content release.
- لا تعديل لمسارات runtime المستخدمة حاليًا.
- final W5 exact-SHA Quality Gate يظل مطلوبًا لإغلاق الموجة كاملة.
