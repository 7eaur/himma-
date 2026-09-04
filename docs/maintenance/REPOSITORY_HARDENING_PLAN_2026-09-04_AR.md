# خطة التوحيد والتقوية الشاملة — منصة هِمّة

**التاريخ:** 2026-09-04  
**الحالة:** ACTIVE — التنفيذ المعماري مغلق، والتحقق النهائي جارٍ على SHA موحد  
**المستودع الرسمي:** `7eaur/himma-`  
**الفرع:** `recovery/ui-media-admin-overhaul`

## 1. الهدف

الوصول إلى مستودع رسمي واحد يمكن الاعتماد عليه دون الرجوع إلى Sandbox لمعرفة «النسخة الأفضل»، وفق المسار التالي:

```text
Approved versioned source
  -> deterministic projection/seed
  -> PostgreSQL runtime snapshot
  -> structured API
  -> deterministic renderer
```

مع القواعد التالية:

- Runtime أكاديمي واحد واضح.
- Design System واحد لمهام الطالب.
- Admin System مشترك بلا page-specific patch architecture.
- لا DOM/content parser أو MutationObserver لحل حالة التطبيق.
- لا `*-polish.css` كطبقة ترقيع فوق التصميم الأساسي.
- لا اعتماد على ترتيب تسجيل FastAPI routers لحسم duplicate routes.
- لا منطق أكاديمي دائم داخل ملفات Temporary.
- فجوات الوسائط معلنة كأصول ومتعددة الاستخدامات ولا تخفى ببدائل.
- CI يختبر عقود السلوك لا نصوص copy هشة.

## 2. ما أُنجز فعليًا

### A. Design System موحد لمهام الطالب — DONE

تم:

- جعل `apps/web/src/app/student/session/[id]/session.module.css` القالب المشترك للاختبار والتعلم والتقوية.
- إزالة `student-experience.css` و`activity-polish.css`.
- تحويل Coach/CTA من absolute layout إلى Grid طبيعي.
- دمج Desktop/Tablet/Mobile داخل القالب نفسه.
- الحفاظ على touch targets و`prefers-reduced-motion`.
- إزالة `studentPath.module.css` غير المستخدم.
- عدم إعادة مكونات Sandbox القديمة التي كانت تعدل DOM بعد render.

المرجع: `docs/architecture/STUDENT_TASK_DESIGN_SYSTEM_AR.md`.

### B. إزالة ترقيع DOM/Portal للتخطي الصوتي — DONE

تم:

- حذف `TemporaryAudioSkipControl` القائم على `MutationObserver/querySelector/Portal`.
- جعل Development Audio Skip عنصرًا صريحًا داخل Recording Panel.
- تمرير `sessionId/itemId/stepId` مباشرة.
- إبقاء التخطي محايدًا أكاديميًا: لا تسجيل وهمي، لا درجة، لا Reward، لا Mastery.
- Trial/Production يفشلان مغلقين إذا كان bypass مفعّلًا.

### C. إزالة UI state inference من DOM — DONE

تم:

- إزالة قراءة `innerText` والبحث عن عبارات نجاح/إعادة.
- إزالة reward popup المستنتج من DOM.
- إبقاء micro audio cues على عقود صريحة فقط مثل زر الاستماع و`aria-pressed`.
- نتائج الإنجاز والانتظار تعرضها الشاشة نفسها كحالة صريحة.

### D. عقود Student UI/E2E — DONE

العقود الحالية تشمل:

- `activity-option`
- `activity-image-options`
- `activity-text-options`
- `activity-sequence-image-options`
- `activity-memory-preview`
- `activity-reading-text`
- `declared-media-gap`
- `aria-pressed`
- `data-phase`

كما تم تحديث Vertical Slice بحيث:

- الذاكرة تعرض الصور أولًا ثم ينقر الطالب/الاختبار `التالي` قبل الاسترجاع.
- sequence/image tasks تستخدم العقود الحالية.
- completion يتحقق من `data-phase=done` بدل copy قديمة.
- وصول `path_sequence` المتقاعد إلى Runtime يعد فشلًا صريحًا.

### E. Assessment completion — DONE

تم فصل العقد الدائم إلى:

`services/api/assessment_completion.py`

وهو المالك الوحيد لـ:

`POST /assessment/session/{session_id}/finish`

وتم حذف endpoint القديم المكرر من `assessment.py` وإضافة اختبار يثبت وجود مالك واحد فقط.

`temporary_audio_skip.py` عاد لوظيفته التطويرية فقط ولا يملك placement/scoring الدائم.

### F. Activities route ownership — DONE

تم إلغاء نمط:

`V4 routes + include legacy router + الاعتماد على registration order`

وأصبح `activities_v4.py` المالك الوحيد للمسارات العامة:

- `GET /activities/status`
- `POST /activities/start`
- `GET /activities/session/{session_id}/progress`
- `GET /activities/session/{session_id}/next`
- `POST /activities/session/{session_id}/attempt/{item_id}/submit`

`activities.py` يستخدم حاليًا كمكتبة service/helpers مثبتة ولا يتم Mount للـrouter الخاص به. ويوجد اختبار يمنع duplicate route ownership مستقبلًا.

### G. Source واحد للقصص السمعية — DONE

المصدر المعتمد:

`packages/content/src/l1_auditory_comprehension_v1.json`

ويحتوي:

- `L1-CORE-09` — قصة ليان في المزرعة.
- `L1-REIN-11` — قصة نادر في الشاطئ.

تم إلغاء `patch_db_runtime()` بالكامل. المسار الحالي:

```text
l1_auditory_comprehension_v1.json
  -> seed_l1_auditory_story_replacement.py
  -> normalized DB rows
  -> seed_db_runtime_contract.py
  -> db_runtime snapshot
```

لا يوجد تعديل لاحق للـRuntime بعد إسقاطه.

### H. تصحيح Skill/Adaptive Mapping للاستبدال السمعي — DONE

كانت فجوة حقيقية: `L1-REIN-11` أصبح قصة سمعية بينما خريطة التقوية ما زالت تربطه بمهارة اتجاه القراءة القديمة.

تمت المصالحة كالتالي:

- Skill الحالي: `auditory_literal_comprehension`.
- الاسم: `الفهم السمعي المباشر`.
- الأسرة: `auditory_comprehension`.
- المرشح المباشر: `L1-REIN-11`.
- `L1-CORE-09` و`L1-REIN-11` يشيران إلى Skill نفسه.
- Skill row التاريخي نفسه أعيد توصيفه دون حذف FK/history ودون إنشاء مهارة رقم 45.
- `visual_motor_direction` لا يظهر في الخريطة الحالية.
- Reinforcement Map أصبح `HIMMA-REINFORCEMENT-MAP-1.2` ويظل 44 مهارة.
- اختبار Runtime يثبت عدم بقاء `path_sequence` كـcanonical interaction حالي.

### I. فجوات الصوت — EXTERNAL-GATED ومكتملة التوثيق

عدد الأصول الصوتية المطلوبة المفقودة = **4**:

1. `موز` — `L1-CORE-06/R01`.
2. `سَا` — أصل واحد يستخدم في:
   - `L2-CORE-06/R04`
   - `L2-REIN-08/R04`
3. قصة ليان/المزرعة — أصل واحد يعاد استخدامه عبر جولات `L1-CORE-09` الخمس.
4. قصة نادر/الشاطئ — أصل واحد يعاد استخدامه عبر جولات `L1-REIN-11` الخمس.

المصدر machine-readable:

`packages/content/src/audio_asset_requirements_v1.json`

الإصدار: `HIMMA-AUDIO-REQUIREMENTS-1.1`.

السياسة:

- لا substitution.
- لا placeholder يعد approved.
- `موزة` ليست بديلًا عن `موز`.
- نص القصة لا يحل محل الصوت في واجهة الطالب.
- أصل واحد يمكن أن يخدم عدة usages ويجب ربطها جميعًا عند الاستلام.

M08 يبقى **EXTERNAL-GATED** حتى تصل الملفات الأربعة المعتمدة.

### J. Admin reconciliation — DONE دلاليًا

تمت مقارنة الكود الفعلي في الرسمي مع آخر Sandbox المرجعي في:

- `AdminUI.tsx`
- `AdminUI.module.css`
- `AdminNotifications.tsx`
- `AdminNotifications.module.css`

النتيجة: السلوك والتصميم المشترك متصالحان دلاليًا؛ اختلافات SHA المتبقية كانت تنسيق/أسطر وليست ميزة ناقصة. لم يتم إنشاء commit شكلي لمجرد مطابقة SHA.

### K. تنظيف Legacy/خطر — DONE للـcritical flow

تم حذف:

- `scratch.py` القديم ذي مسار Windows الثابت وكتابة CSS المباشرة.
- `studentPath.module.css` غير المستخدم.
- طبقات polish السابقة.
- DOM enhancer/temporary injection components المرتبطة بالمسار الحرج.

البحث الحالي لا يجد `polish.css` أو `TemporaryAudioSkipControl` أو `AssessmentExperienceEnhancer` أو `MutationObserver` في الرسمي.

## 3. التحقق النهائي

### P0-01 — Quality Gate على SHA واحد

الحالة: **VERIFYING**.

يجب تثبيت النتائج على SHA النهائي نفسه لـ:

- Backend tests.
- Frontend typecheck/lint/unit/build.
- Integration job حسب شروط workflow.
- M04 responsive visual gate + artifact screenshots.
- M09 release readiness.

لا يكتب PASS هنا أو في تقرير التسليم دون Run IDs وjobs/conclusions.

### P0-02 — External Media Gate

الحالة: **EXTERNAL-GATED**.

هذه ليست مشكلة كود قابلة للاختلاق. المطلوب الملفات الصوتية الأربعة المذكورة أعلاه، ثم:

1. إضافتها إلى حزمة الصوت المعتمدة.
2. تحديث manifest/checksum.
3. ربط جميع usages.
4. تشغيل seed/projection.
5. التحقق من عدم بقاء gap المقابل.
6. إعادة M08 والبوابات المرتبطة.

## 4. P2 — تحسينات صيانة مستقبلية غير حاجبة للفرع الحالي

### P2-01 — استخراج Activity service module

`activities.py` لم يعد Mounted لكنه ما زال يحمل تاريخ Stage-2 ودوال route-decorated تستخدم كخدمات من `activities_v4.py`.

التنظيف المستقبلي الأفضل:

- استخراج scoring/state helpers إلى `activity_service.py` بلا `APIRouter`.
- نقل tests إلى الخدمة الجديدة.
- إبقاء `activities_v4.py` طبقة HTTP رفيعة.
- حذف module legacy فقط بعد إثبات عدم وجود imports خارجية.

هذا لا يسبب duplicate Runtime routes حاليًا، لذلك هو P2 لا P0.

### P2-02 — Dead CSS audit إضافي

بعد استقرار Screenshots:

- مراجعة selectors غير المستخدمة في `session.module.css` و`globals.css`.
- إزالة class فقط بدليل consumer/search/build.
- لا purge آلي أعمى.

### P2-03 — Visual regression expansion

المصفوفة المستهدفة:

- Landing.
- Student Login/Home.
- Assessment text/image/listen/record/sequence.
- Memory preview + recall.
- Reinforcement.
- Completion/waiting review.
- Admin Dashboard.
- Students.
- Audio Review.
- Reports.

Desktop + Tablet + Mobile.

## 5. قواعد تمنع عودة الترقيع

يرفض أي تغيير جديد إذا:

- أضاف `*-polish.css` بدل تعديل القالب المصدر.
- استخدم DOM parser لاستخراج محتوى السؤال.
- استخدم MutationObserver لحل application state.
- استخدم selector خارجي على CSS Module hashed class.
- أخفى media gap بصوت/نص بديل.
- أعاد `path_sequence` دون قرار أكاديمي جديد.
- أعاد duplicate API route يعتمد على registration order.
- وضع scoring/placement دائمًا داخل Temporary/Dev module.
- غيّر promotion/scoring كأثر جانبي لتعديل UI.

## 6. Definition of Repository Ready

يسمى **Repository Code Ready** فقط إذا اجتمعت:

1. Runtime counts `125 / 35 / 30 / 65 / 30` صحيحة.
2. المهارات الحالية 44 وخريطة التقوية متوافقة مع المحتوى الحالي.
3. `path_sequence` المتقاعد غير موجود في canonical Runtime.
4. DB Runtime يبنى من المصادر versioned بلا post-projection patch.
5. Assessment/Activities critical URLs لها owner واحد.
6. Backend/Frontend/Integration أخضر على SHA واحد.
7. M04 أخضر وصور من نفس SHA.
8. M09 أخضر من نفس SHA.
9. كل media gap معلن ولا يوجد substitute مخفي.
10. Sandbox لم يعد يحتوي تحسينًا معروفًا مطلوبًا غير مصالح في الرسمي.
11. لا Patch architecture معروفة في critical student flow.

حتى بعد تحقق ذلك، **M08/Full Media Release يبقى External-Gated** إلى أن تصل الأصول الصوتية الأربعة وتتم إعادة البوابات المعنية.
