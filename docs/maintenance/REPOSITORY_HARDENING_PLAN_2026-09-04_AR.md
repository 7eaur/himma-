# خطة التوحيد والتقوية الشاملة — منصة هِمّة

**التاريخ:** 2026-09-04  
**الحالة:** ACTIVE — وثيقة تنفيذ حيّة  
**المستودع:** `7eaur/himma-`  
**الفرع:** `recovery/ui-media-admin-overhaul`

## 1. الهدف

الوصول إلى مستودع رسمي واحد يمكن الاعتماد عليه دون الرجوع إلى Sandbox لمعرفة «النسخة الأفضل»، مع:

- Runtime أكاديمي واحد واضح.
- Design System واحد للطالب.
- Admin System موحد.
- لا DOM/content patches.
- لا visual override layers.
- لا منطق أكاديمي دائم داخل ملفات Temporary.
- فجوات الوسائط معلنة ولا تخفى ببدائل.
- CI يختبر عقود السلوك لا نصوص copy هشة.
- توثيق حي يطابق الكود الفعلي.

## 2. ما أُنجز فعليًا في جولة 2026-09-04

### A. توحيد تصميم مهام الطالب

تم:

- جعل `session.module.css` القالب المشترك للاختبار والتعلم.
- إزالة `student-experience.css`.
- إزالة `activity-polish.css`.
- تحويل Coach/CTA من absolute layout إلى Grid طبيعي.
- توحيد Desktop/Tablet/Mobile داخل نفس القالب.
- الحفاظ على touch targets وreduced motion.
- إزالة `studentPath.module.css` غير المستخدم.

المرجع:

`docs/architecture/STUDENT_TASK_DESIGN_SYSTEM_AR.md`

### B. إزالة DOM/Portal patch للتخطي الصوتي

تم:

- حذف `TemporaryAudioSkipControl.tsx` الذي كان يعتمد `MutationObserver/querySelector/Portal`.
- إضافة `DevelopmentAudioSkipAction` كعنصر صريح داخل Recording Panel.
- تمرير `sessionId/itemId/stepId` مباشرة.
- منع التخطي من إنشاء تسجيل/درجة/Mastery.
- إزالة التخطي المؤقت من Layout الاختبار.

### C. تحسين عقد النشاط والاختبارات

تمت إضافة عقود صريحة مثل:

- `aria-pressed` للخيارات القابلة للتحديد.
- `activity-option`.
- `activity-image-options`.
- `activity-text-options`.
- `activity-sequence-*`.
- `activity-memory-preview`.
- `activity-reading-text`.
- `declared-media-gap`.

الهدف: لا يفترض E2E شكل DOM غير معلن.

### D. إزالة feedback inference من DOM

تم:

- حذف `MutationObserver` الذي كان يقرأ `innerText` ويبحث عن عبارات مثل «حاول مرة أخرى».
- إلغاء Popup reward المستنتج من النص/DOM.
- إبقاء micro audio cue فقط على عقود صريحة: زر الاستماع و`aria-pressed`.
- حذف CSS الخاص بالـPopup القديم.

### E. فصل منطق التقييم الدائم عن Temporary audio bypass

تم إنشاء:

`services/api/assessment_completion.py`

ليحتوي عقد:

- pre/post completion.
- section scoring.
- audio review preflight.
- provisional placement.
- posttest no-backward-rewrite behavior.

وأعيد `temporary_audio_skip.py` إلى وظيفة تطويرية فقط.

**ملاحظة تقنية:** ما زال `assessment.py` يحتوي endpoint legacy لـ`finish` للتوافق، بينما `assessment_completion_router` مسجل قبله ويملك العقد الحالي. إزالة الـlegacy duplicate بالكامل خطوة Hardening لاحقة بعد إثبات جميع الاختبارات؛ لا يحذف عميانيًا قبل ذلك.

### F. تنظيف ملفات خطرة/ميتة

تم حذف:

- `scratch.py`: سكربت قديم بمسار Windows ثابت كان يعدل/يلحق CSS وملفات محلية، وليس Runtime أو build tool معتمدًا.
- `studentPath.module.css`: ملف Legacy غير مستخدم.

### G. تصحيح سجل الصوت

تم تصحيح الاعتقاد القديم أن الفجوات = 2 فقط.

الفجوات المعروفة الآن = **4**:

1. `موز` — L1-CORE-06.
2. `سَا` — L2-CORE-06.
3. قصة ليان/المزرعة — L1-CORE-09.
4. قصة نادر/الشاطئ — L1-REIN-11.

المرجع:

`docs/specs/AUDIO_INVENTORY_AND_GAPS_2026-08-28_AR.md`

## 3. P0 — لا اعتماد نهائي قبل إغلاقها

### P0-01 — Quality Gate على SHA موحد

الحالة: **PENDING VERIFY**.

يجب تشغيل والتحقق من:

- Backend tests.
- Frontend typecheck/lint/unit/build.
- Integration E2E.
- M04 responsive visual gate.
- M09/full journey/release gate حسب workflow الحالي.

لا PASS بدون SHA + Run IDs + jobs.

### P0-02 — E2E semantics

تم إصلاح exact copy assertion في Dashboard إلى عقد دلالي.

يجب التأكد من `vertical-slice.spec.ts` بعد التغييرات الحالية، خصوصًا:

- memory preview يحتاج `التالي` قبل recall.
- sequence/image choices تستخدم test IDs الحالية.
- completion يجب الاعتماد فيه على `data-phase=done` لا copy قديمة.

إذا فشل الـCI لهذا السبب، يصلح الاختبار ليحاكي UI الحقيقي ولا يعدل المنتج لإرضاء اختبار stale.

### P0-03 — External audio gates

الحالة: **EXTERNAL-GATED**.

لا يمكن للكود إغلاق الأصول الأربعة المطلوبة. لا substitutions ولا fake assets.

M08 يبقى PENDING في النطاق الذي يعتمد عليها.

## 4. P1 — Hardening معماري

### P1-01 — إزالة legacy duplicate finish route

الوضع الحالي:

- `assessment_completion.py` = العقد الدائم الصحيح.
- `assessment.py` ما زال يحتوي `/session/{id}/finish` legacy.

المطلوب بعد CI:

- نقل أي test/import أخير للعقد الجديد.
- حذف implementation القديم أو تحويله إلى استدعاء مباشر لخدمة completion واحدة دون duplicate route order dependency.
- إضافة test يثبت وجود route فعلي واحد للمسار النهائي.

### P1-02 — Runtime/seed simplification

الوضع الحالي صحيح وظيفيًا لكنه يحتوي عدة seed مراحل تاريخية.

المطلوب ليس حذف التاريخ، بل فصل:

- migrations/history؛
- approved source؛
- current projection؛
- orchestration.

الهدف النهائي:

```text
approved versioned content
  -> one current projection orchestration
  -> DB snapshot
  -> readiness contract
```

أي seed تاريخي يبقى migration/history ولا يكون مصدرًا ثانيًا للحقيقة.

### P1-03 — Media manifest contract

ينبغي تحويل سجل الصوت من Markdown فقط إلى Manifest machine-readable يربط:

- asset_id.
- semantic_text.
- canonical item.
- usage.
- master/web files.
- status approved/pending.
- checksum عند توفر الملفات.

ثم يقرأ validator هذا manifest ويمنع إعلان content ready إذا كان المسار المطلوب يحتاج asset مفقودًا.

### P1-04 — Admin visual reconciliation

الـAdmin الحالي وظيفي وResponsive، لكن يجب عمل مراجعة تصميمية نهائية على:

- Dashboard hierarchy.
- Students list/detail.
- Audio Review.
- Reports.
- Skill Reports.
- Notifications.
- Settings.

القاعدة: التحسين يدخل في `AdminUI`/shared tokens، لا Page-specific patch CSS.

## 5. P2 — جودة وصيانة

### P2-01 — Dead CSS audit

بعد استقرار CI:

- استخراج selectors غير المستخدمة في `session.module.css` و`globals.css`.
- إزالة أي class لم يعد له consumer.
- لا تستخدم purge آليًا دون مراجعة لأن CSS Modules/conditional rendering قد لا يظهران في بحث نصي بسيط.

### P2-02 — Visual regression coverage

مصفوفة ثابتة للشاشات الحرجة:

- Landing.
- Student Login/Home.
- Assessment text/image/listen/record/sequence.
- Memory.
- Reinforcement.
- Completion/waiting review.
- Admin Dashboard.
- Students.
- Audio Review.
- Reports.

Desktop + Tablet + Mobile.

### P2-03 — Documentation hygiene

- Active docs تبقى قليلة وواضحة.
- Sandbox handoffs تحفظ في archive إن احتجناها.
- لا يكون ملف handoff قديم أعلى سلطة من كود/contract أحدث.

## 6. قواعد تمنع عودة الترقيع

أي PR/commit جديد يخص الطالب يجب رفضه إذا:

- أضاف `*-polish.css` بدل تعديل المصدر.
- استخدم DOM parser لاستخراج محتوى السؤال.
- استخدم MutationObserver لحل حالة application state.
- استخدم selector على CSS Module hashed name من ملف خارجي.
- أخفى media gap بصوت/نص بديل.
- أعاد `path_sequence` دون قرار أكاديمي جديد.
- غير قواعد promotion/scoring كأثر جانبي لتعديل UI.

## 7. Definition of Repository Ready

لا يسمى الفرع Ready/Closed إلا إذا اجتمعت:

1. Runtime counts 125/35/30/65/30 صحيحة.
2. readiness يمر على DB current projection.
3. Backend/Frontend/Integration أخضر على نفس SHA.
4. M04 أخضر وصور من نفس SHA.
5. رحلة الطالب الأساسية مختبرة.
6. Admin critical paths مختبرة.
7. كل media gap معلن، لا مخفي.
8. أي External Gap مذكور صراحة في قرار الإصدار.
9. Sandbox لم يعد يحتوي تحسينًا معروفًا مطلوبًا لم تتم مصالحته.
10. لا Patch architecture معروفة في critical student flow.
