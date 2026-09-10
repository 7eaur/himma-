# هِمّة — A04/A05 تدقيق لوحة الإدارة، الهاتف، الشارات والمكافآت

**التاريخ:** 2026-09-10  
**الحالة:** AUDIT ONLY — لا إصلاح واسع، لا دمج، لا نشر  
**الفرع:** `audit/comprehensive-repository-review-2026-09-10`  
**مرجع التنفيذ:** `integration/canonical-content-2026-09-08@7cb2192b0c31bc85dcf98a470023e9cc6f1598e0`

---

## 1. الهدف

هذا الملف يسجل نتائج مرحلتي A04 وA05 قبل أي موجة تحسين:

- توحيد لوحة الإدارة حول Design System واحد.
- إثبات مرونة صفحات الإدارة على الهاتف، خصوصًا تفاصيل الطالب.
- إثبات نظام المكافآت والشارات من قاعدة البيانات إلى واجهة الطالب والمشرف والأصول البصرية والاختبارات.
- عدم حذف أي صفحة/طبقة أو إعادة كتابة أي نظام قبل فهم سبب وجوده واعتمادياته.

---

## 2. A04 — مصفوفة صفحات الإدارة

| المسار | النظام البصري الحالي | الهاتف | الحالة | الملاحظة |
|---|---|---|---|---|
| `/admin` | `AdminUI` | جيد مبدئيًا | VERIFIED | يستخدم primitives المشتركة. |
| `/admin/students` | `AdminUI` + desktop table/mobile cards | جيد مبدئيًا | VERIFIED | نموذج جيد يعاد استخدامه. |
| `/admin/students/new` | `AdminUI` | جيد مبدئيًا | VERIFIED | form/layout مشترك. |
| `/admin/reports` | `AdminUI` + mobile cards | جيد مبدئيًا | VERIFIED | لا يحتاج نظامًا بصريًا جديدًا. |
| `/admin/skill-reports` | `AdminUI` | جيد مبدئيًا | VERIFIED | responsive table/mobile-card pattern. |
| `/admin/audio-review` | `AdminUI` | يحتاج E2E هاتف | VERIFIED STRUCTURE | shell موحد، لكن نص إعادة التسجيل يحتاج مراجعة دلالية. |
| `/admin/content-preview` | `AdminUI` shell + preview داخلي | مقبول بنيويًا | VERIFIED STRUCTURE | التخصيص الداخلي مبرر لأنه عارض محتوى. |
| `/admin/settings` | نظام CSS خاص | responsive جزئيًا | GAP | يعيد بناء page/header/tabs/panels/forms/buttons بدل primitives المشتركة. |
| `/admin/account` | `admin.module.css` + inline/global classes | غير موحد | GAP | مسار قديم/مكرر وغير موجود في قائمة التنقل الحالية؛ لا يحذف قبل تتبع الروابط والاختبارات. |
| `/admin/students/[id]` | نظام CSS خاص كبير | خطر واضح 320–360px | GAP P1 | يعيد بناء header/cards/stats/tabs/forms/actions/modal بدل AdminUI. |
| `/admin/login` | صفحة auth مستقلة | يحتاج فحص هاتف | REVIEW | استقلال auth مقبول، لكن يجب توحيد tokens/هوية/accessible states لا فرض dashboard shell عليها. |

### AUD-FE-004 — Settings يشكل Design System إداريًا ثانيًا

`settings/page.tsx` + `settings.module.css` يبنيان:
- page/header
- tabs
- panels
- form controls
- buttons
- supervisor cards

بينما نفس primitives موجودة أصلًا في `components/admin/AdminUI.tsx`.

**المشكلة:** ليس مجرد اختلاف شكلي؛ أي تعديل spacing/radius/focus/mobile behavior في AdminUI لن يصل إلى Settings، ما يخلق drift دائمًا.

**المعالجة المخطط لها لاحقًا:** نقل shell/forms/actions/panels إلى AdminUI، والإبقاء فقط على CSS الخاص بالتبويبات أو التركيب الذي لا يغطيه النظام المشترك.

### AUD-FE-005 — `/admin/account` مسار قديم/مكرر يحتاج حسم

المسار الحالي يعرض بيانات الحساب والخروج، لكنه:
- غير موجود في sidebar الحالي.
- يستخدم `admin.module.css` وinline/global classes.
- تتقاطع وظيفته مع `/admin/settings` الذي يدير الحساب/الأمان/المشرفين.

**لا يُحذف الآن.** يجب أولًا فحص:
1. أي Link داخلي أو redirect إليه.
2. اختبارات E2E أو روابط محفوظة.
3. هل Settings هو المالك النهائي فعلًا لكل وظائفه.

إذا ثبت عدم وجود اعتماد مشروع، يصبح `ARCHIVE/REMOVE CANDIDATE` بعد redirect آمن أو migration UX إن لزم.

### AUD-FE-001 / AUD-FE-002 — تفاصيل الطالب أولوية إعادة البناء

`students/[id]/page.tsx` لديه منطق وظيفي مهم لا يجب كسره، لكنه يعيد بناء معظم النظام البصري محليًا.

المكوّنات المحلية تشمل:
- header/identity/status button
- summary cards
- tabs
- panels
- info/reward cards
- journey/progress
- forms/actions
- history rows
- message states

CSS يعتمد أيضًا على grid بقيم مثل `minmax(320px, 1fr)` مع تغطية هاتف محدودة.

**بوابة الهاتف لهذه الصفحة قبل الاعتماد:**
- 320px
- 360px
- 390px
- 430px
- 768px
- desktop

ويجب التحقق فعليًا من:
- عدم horizontal overflow.
- tabs قابلة للاستخدام باللمس ولا تقطع النصوص.
- summary cards لا تضغط رمز الدخول/الأرقام.
- status/actions تتكدس بشكل مفهوم.
- حقول تعديل الاسم/الرمز/المستوى والسبب قابلة للكتابة دون overflow.
- focus/keyboard/error states.
- النص العربي والـRTL لا ينكسران.

**اتجاه الحل الجذري لاحقًا:** إعادة تكوين الصفحة من `AdminPage`, `AdminPageHeader`, `AdminPanel`, `AdminStatGrid`, `AdminAction` ومكونات shared جديدة فقط إذا كان هناك pattern حقيقي غير موجود، بدل نسخ CSS جديد.

### AUD-FE-006 — نص إعادة التسجيل في لوحة المراجعة يحتاج مزامنة مع العقد الحالي

العقد التنفيذي الحالي: `rerecord_required` مهمة مؤجلة وصريحة يفتحها الطالب عندما يختار ذلك، ولا تسحبه فورًا من مساره.

بعض نصوص Admin Audio Review ما زالت تُفهم كأن المحاولة «تعاد فتحها» مباشرة بعد رفض التسجيل.

**المطلوب لاحقًا:** توحيد صياغة Admin/Student على:
- التسجيل غير صالح → ينشأ طلب إعادة تسجيل.
- الطالب يستطيع متابعة المسار المسموح.
- يعيد التسجيل عندما يفتح المهمة صراحة.
- التسجيل السابق محفوظ تاريخيًا.

---

## 3. A05 — حالة نظام النجوم والشارات فعليًا

### 3.1 قاعدة البيانات — موجودة وليست ناقصة

يوجد Model دائم `RewardEvent` وجدول `reward_events` في migration `0006_adaptation_engine.py`.

الحقول تشمل:
- `student_id`
- `attempt_id` nullable
- `reward_type` (`stars` / `badge`)
- `reward_key`
- `stars`
- `label`
- `details`
- `created_at`

يوجد قيد فريد:
`UNIQUE(student_id, reward_key)`

**النتيجة:** الأساس البنيوي للمكافآت persistent ويدعم idempotency على مستوى DB.

### 3.2 منطق المنح — موجود

`adaptation.ensure_rewards()`:
- يمنح نجومًا فقط لمحاولة مكتملة ولها evidence صالح عبر `_attempt_signal`.
- لا يمنح فجوة media-only أو صوتًا unresolved كمكافأة أكاديمية.
- يستخدم مفتاحًا ثابتًا `activity:{attempt_id}:stars`.
- يحسب 3/2/1 نجمة بحسب retry/hint behavior.
- ينشئ badge event بمفتاح `level:{level}:core-complete`.
- `_add_reward_once` + unique constraint يمنعان التكرار.

كما توجد APIs:
- `GET /rewards` للطالب.
- `GET /researcher/students/{student_id}/rewards` للمشرف.

**إذن النظام ليس مفقودًا من Backend.** الفجوات الأساسية حاليًا في contract/visual integration/coverage.

---

## 4. فجوات الشارات المثبتة

### AUD-BADGE-001 — واجهة الطالب تجلب الشارات ثم لا تعرضها

`student/page.tsx` يجلب `/api/rewards` ويخزن جميع RewardEvent، لكنه يحسب فقط:
`totalStars = sum(reward.stars)`

ولا يوجد render للشارات المكتسبة في الصفحة الحالية.

النتيجة: الطالب قد يمتلك BadgeEvent في قاعدة البيانات وAPI، بينما واجهته الرئيسية لا تعرض الشارة نفسها.

**الشدة:** P1 لأن الشارات جزء من تجربة التحفيز المرئية، وليست مجرد metadata خلفية.

### AUD-BADGE-002 — لوحة المشرف تعرض اسم الشارة كنص فقط

صفحة تفاصيل الطالب:
- تحسب `badges = rewards.filter(type === "badge")`.
- تعرض العدد.
- تعرض `badge.label` داخل chip نصي.

هذا أفضل من عدم العرض، لكنه لا يستخدم الأصل البصري المعتمد للشارة، ولا يوجد asset id في الـAPI يجعل الربط صريحًا.

### AUD-BADGE-003 — حزمة الشارات المعتمدة غير مدمجة في `public`

الحزمة المرفقة `Himma_Characters_Badges_UI_Kit_v1.0` تحتوي:
- BDG-01 نجمة واحدة
- BDG-02 نجمتان
- BDG-03 ثلاث نجوم
- BDG-04 مستكشف الحروف
- BDG-05 بطل الكلمات
- BDG-06 نجم الفهم
- وثلاثة رموز مستويات
- وصيغ SVG/PNG/WebP

لكن `apps/web/public` الحالي يحتوي `audio`, `brand`, `characters` وبعض أصول Next الافتراضية، ولا يوجد حاليًا directory معتمد `rewards` أو `levels` لهذه الحزمة.

**النتيجة:** Backend reward events غير موصول فعليًا بالحزمة البصرية الرسمية.

### AUD-BADGE-004 — عدم تطابق اسم شارة المستوى الثالث

Backend الحالي:
- L1 = `مستكشف الحروف`
- L2 = `بطل الكلمات`
- L3 = `قارئ متميز`

الحزمة المعتمدة:
- BDG-04 = `مستكشف الحروف`
- BDG-05 = `بطل الكلمات`
- BDG-06 = `نجم الفهم`

L3 غير متطابق: `قارئ متميز` مقابل `نجم الفهم`.

**هذه فجوة Source of Truth.** لا نعدل الاسم عشوائيًا الآن؛ في موجة التحسين يجب إنشاء reward catalog canonical واحد يربط:
`reward_key -> asset_id -> label -> level -> type`
بحيث لا يحتفظ Backend وUI والحزمة بثلاث حقائق منفصلة.

### AUD-BADGE-005 — شرط منح الشارة لا يطابق تعريف اكتمال L1/L2 الحالي

`journey.py` يعترف صراحة بأن المستوى 1 أو 2 يمكن أن يصبح `completed` عبر **early promotion** بعد بوابات V4، حتى لو اكتملت 6–9 أنشطة Core فقط.

لكن `ensure_rewards()` يمنح badge فقط عندما:
`_completed_core_count(...) >= 10`

النتيجة المحتملة المؤكدة منطقيًا من الكود:
- طالب متفوق يترقى مبكرًا من L1 أو L2.
- رحلة الطالب تعرض المستوى `completed`.
- لن يحصل على شارة ذلك المستوى لأن شرط الشارة ما زال legacy `10 core`.

هذا تعارض semantics حقيقي بين Journey وRewards.

**اتجاه الحل الجذري المخطط:** الشارة يجب أن تعتمد على نفس مفهوم `level completion` الرسمي المستخدم في Journey/transition evidence، وليس عدادًا موازيًا خاصًا بها. يلزم تثبيت العقد النهائي قبل التنفيذ: هل الشارة لـ«إكمال المستوى وفق سياسة V4» أم لـ«إكمال العشرة أنشطة تحديدًا»؟ أسماء الشارات وحزمة المستويات تشير إلى أنها milestone مستوى، لذلك الخيار الأول هو المرشح الأقوى، لكن لا يطبق قبل تثبيت القرار في Source of Truth/ADR.

### AUD-BADGE-006 — تغطية الاختبارات الحالية لا تغلق E2E للشارات

في الاختبارات التي تمت مراجعتها:
- يوجد إثبات قوي لمنح النجوم مرة واحدة.
- يوجد إثبات أن media-gap/unresolved-audio لا يكسب مكافأة.
- يوجد idempotency في DB والمنطق.

لكن لم يُثبت بعد في المراجعة الحالية Test يغطي الرحلة كاملة:
1. إكمال/ترقية مستوى.
2. إنشاء الشارة الصحيحة مرة واحدة.
3. asset_id/label الصحيح.
4. ظهورها للطالب.
5. ظهورها للمشرف.
6. بقاءها صحيحة بعد refresh/seed/runtime restart.

لذلك Badge E2E يبقى Gate مفتوحًا.

---

## 5. التصميم الجذري المقترح لنظام المكافآت — لا ينفذ قبل نهاية التدقيق

بدل إضافة if/else جديد داخل الواجهة:

### Reward Catalog واحد
مثال عقد مقترح:

```text
BDG-01 -> stars:1 -> asset hem-bdg-01-star-one.svg
BDG-02 -> stars:2 -> asset hem-bdg-02-stars-two.svg
BDG-03 -> stars:3 -> asset hem-bdg-03-stars-three.svg
BDG-04 -> level:1 -> مستكشف الحروف
BDG-05 -> level:2 -> بطل الكلمات
BDG-06 -> level:3 -> نجم الفهم
```

ويصبح RewardEvent يسجل هوية reward مستقرة (`reward_key` أو catalog id)، بينما API يخرج display contract موحدًا يتضمن على الأقل:
- `key`
- `type`
- `stars`
- `label`
- `asset_id` أو `asset_url`
- `level_id` عند الحاجة
- `created_at`

### مصدر واحد لاكتمال المستوى
لا يجب أن يمتلك:
- Journey تعريفًا للاكتمال،
- Rewards تعريفًا ثانيًا،
- Posttest eligibility تعريفًا ثالثًا.

يجب استخراج service/policy واحد يجيب: `is_level_completed(student, level, evidence)`، وتستهلكه Journey + Rewards + posttest gate حيث يلزم.

---

## 6. أصول موجودة يجب حمايتها أثناء التحسين

1. `RewardEvent` التاريخي لا يحذف.
2. `reward_key` uniqueness لا يكسر.
3. النجوم المكتسبة سابقًا لا تعاد حسابها بطريقة تغيّر التاريخ دون migration صريحة.
4. rejected/pending audio لا يصبح reward evidence.
5. high-performing early-promotion behavior لا يعاد إلى legacy 10-core لمجرد إصلاح الشارة.
6. AdminUI الموجود يعاد استخدامه بدل إنشاء Design System ثالث.
7. حزمة badges/levels تستخدم بأسمائها ومعرفاتها المعتمدة؛ لا تعاد رسمها أو إعادة تسميتها اعتباطيًا.

---

## 7. بوابات قبول A04/A05 لاحقًا

### Admin UI
- جميع صفحات dashboard تستخدم shell/tokens/primitives موحدة أو توثق سبب استثناء واضح.
- Student Details يمر 320/360/390/430/768/desktop دون overflow.
- Settings لا يحتفظ بنظام buttons/panels/forms موازٍ.
- orphan `/admin/account` يحسم بعد dependency scan.
- keyboard/focus/error/loading/mobile states مختبرة.

### Rewards/Badges
- Reward catalog canonical.
- أسماء BDG-04/05/06 مطابقة للأصول المعتمدة.
- قواعد completion موحدة مع Journey.
- Student UI يعرض الشارات بصريًا.
- Admin UI يعرض الشارة بمظهر موحد.
- badge assets موجودة في bundle النهائي ومختبرة 404-free.
- لا duplication عند تكرار الطلبات.
- test لـearly promotion badge semantics.
- Backend + frontend unit + integration + E2E خضراء.

---

## 8. الحالة بعد هذه الجولة

- A04: **فهم هيكل لوحة الإدارة اكتمل مبدئيًا، مع فجوات موثقة في Student Details / Settings / Account.**
- A05 Backend persistence/API: **VERIFIED**.
- A05 Visual integration: **GAP**.
- A05 completion semantics: **GAP P1**.
- A05 end-to-end verification: **OPEN**.

المرحلة التالية: A02 dependency map للـSeeds/Repair/Projection، ثم A06 جرد الأصول الفعلي، مع إبقاء الإصلاحات الواسعة مؤجلة حتى اكتمال سجل الفجوات.
