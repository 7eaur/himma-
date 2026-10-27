# هِمّة — A04/A05 تدقيق لوحة الإدارة، الهاتف، الشارات والمكافآت

**التاريخ:** 2026-09-10  
**الحالة:** `A04 STATIC AUDIT CLOSED / A05 STATIC AUDIT CLOSED — NO MERGE — NO DEPLOY`  
**الفرع:** `audit/comprehensive-repository-review-2026-09-10`  
**مرجع التنفيذ الأصلي:** `integration/canonical-content-2026-09-08@7cb2192b0c31bc85dcf98a470023e9cc6f1598e0`  
**ملاحظة:** Git الحالي على فرع التدقيق هو الحقيقة التنفيذية إذا تقدم عن هذا المرجع.

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
| `/admin` | `AdminUI` | جيد مبدئيًا | VERIFIED STRUCTURE | يستخدم primitives المشتركة. |
| `/admin/students` | `AdminUI` + desktop table/mobile cards | جيد مبدئيًا | VERIFIED STRUCTURE | نموذج جيد يعاد استخدامه. |
| `/admin/students/new` | `AdminUI` | جيد مبدئيًا | VERIFIED STRUCTURE | form/layout مشترك. |
| `/admin/reports` | `AdminUI` + mobile cards | جيد مبدئيًا | VERIFIED STRUCTURE | لا يحتاج نظامًا بصريًا جديدًا. |
| `/admin/skill-reports` | `AdminUI` | جيد مبدئيًا | VERIFIED STRUCTURE | responsive table/mobile-card pattern. |
| `/admin/audio-review` | `AdminUI` | يحتاج E2E هاتف | VERIFIED STRUCTURE | shell موحد، لكن نص إعادة التسجيل يحتاج مراجعة دلالية. |
| `/admin/content-preview` | `AdminUI` shell + preview داخلي | مقبول بنيويًا | VERIFIED STRUCTURE | التخصيص الداخلي مبرر لأنه عارض محتوى. |
| `/admin/settings` | نظام CSS خاص | responsive جزئيًا | GAP | يعيد بناء page/header/tabs/panels/forms/buttons بدل primitives المشتركة. |
| `/admin/account` | `admin.module.css` + inline/global classes | غير موحد | GAP | مسار حي داخل route tree؛ لا يحذف قبل dependency scan وحسم التداخل مع Settings. |
| `/admin/students/[id]` | نظام CSS خاص كبير | يحتاج بوابة 320–768px | GAP P1 | يعيد بناء header/cards/stats/tabs/forms/actions بدل AdminUI. |
| `/admin/login` | صفحة auth مستقلة | يحتاج فحص هاتف | REVIEW | استقلال auth مقبول، مع توحيد tokens/هوية/accessible states فقط. |

### AUD-FE-004 — Settings يشكل Design System إداريًا ثانيًا

`settings/page.tsx` + `settings.module.css` يبنيان page/header/tabs/panels/forms/buttons محلية، بينما توجد primitives مشتركة في `components/admin/AdminUI.tsx`.

**الأثر:** أي تعديل spacing/radius/focus/mobile behavior في AdminUI لا يصل تلقائيًا إلى Settings، فينتج drift دائم.

**المعالجة المخطط لها في A10:** نقل shell/forms/actions/panels إلى AdminUI، والإبقاء فقط على CSS الخاص بتركيب لا يغطيه النظام المشترك.

### AUD-FE-005 — `/admin/account` مسار حي/legacy candidate يحتاج حسم

المسار موجود فعليًا تحت `apps/web/src/app/admin/(dashboard)/account/page.tsx`، لكنه متداخل وظيفيًا وبصريًا مع Settings. لا يجوز وصفه بأنه «محذوف» ولا حذفه الآن. قبل أي إزالة يجب فحص الروابط والـredirects والاختبارات والروابط المحفوظة وتحديد المالك النهائي لوظائف الحساب.

### AUD-FE-001 / AUD-FE-002 — تفاصيل الطالب أولوية إعادة البناء

`students/[id]/page.tsx` لديه منطق وظيفي مهم، لكنه يعيد بناء معظم النظام البصري محليًا: header/identity/status، summary cards، tabs، panels، reward cards، journey/progress، forms/actions، history، messages.

**بوابة الهاتف لاحقًا:** 320 / 360 / 390 / 430 / 768 / desktop مع no horizontal overflow، tabs قابلة للمس، cards لا تكسر الأرقام، actions stack واضح، forms قابلة للكتابة، focus/keyboard/error states، RTL صحيح.

**اتجاه الحل الجذري:** إعادة تكوين الصفحة من AdminUI primitives ومكونات shared فقط عند وجود pattern حقيقي غير مغطى.

### AUD-FE-006 — نص إعادة التسجيل في لوحة المراجعة يحتاج مزامنة

العقد الحالي: `rerecord_required` مهمة مؤجلة وصريحة، لا تسحب الطالب فورًا من المسار. يجب توحيد Admin/Student copy على أن التسجيل غير الصالح يفتح طلب إعادة تسجيل، والطالب يعيده عندما يفتح المهمة، مع حفظ التسجيل السابق تاريخيًا.

### إغلاق A04

A04 مغلق كـ **static/source audit**. إعادة التصميم والاختبار البصري الفعلي مؤجلان إلى A10/A08 حسب نوع البوابة؛ لم يتم الادعاء هنا بمرور browser screenshots أو mobile E2E.

---

## 3. A05 — النظام الفعلي للمكافآت والشارات

### 3.1 قاعدة البيانات — موجودة ودائمة

يوجد Model `RewardEvent` وجدول `reward_events` في migration `0006_adaptation_engine.py` بالحقول:

- `student_id`
- `attempt_id` nullable
- `reward_type` (`stars` / `badge`)
- `reward_key`
- `stars`
- `label`
- `details`
- `created_at`

وقيد `UNIQUE(student_id, reward_key)`، لذلك idempotency الأساسية موجودة على مستوى DB.

### 3.2 منطق المنح الحالي

`adaptation.ensure_rewards()`:

- يمنح نجومًا لمحاولة Learning مكتملة ولها evidence صالح عبر `_attempt_signal`.
- يستبعد media-gap والصوت unresolved من reward evidence.
- يستخدم `activity:{attempt_id}:stars`.
- يمنح 3/2/1 نجمة حسب retry/hint.
- يمنح badge بمفتاح `level:{level}:core-complete` عندما `_completed_core_count >= 10`.
- يستخدم `_add_reward_once` مع unique constraint لمنع التكرار.
- يستدعى داخل `evaluate_student()`، وكذلك من `GET /rewards` و`GET /researcher/students/{student_id}/rewards`.

الـBackend إذن ليس مفقودًا؛ الخلل في ownership/semantics/display contract/visual integration والبوابات النهائية.

---

## 4. فجوات A05 المثبتة

### AUD-BADGE-001 — واجهة الطالب تجلب الشارات ثم لا تعرضها

`apps/web/src/app/student/page.tsx` يجلب `/api/rewards` ويحسب `totalStars`، لكنه لا يملك render فعليًا لمجموعة badges. الطالب قد يملك BadgeEvent دائمًا ولا يراه في واجهته.

**Severity:** P1.

### AUD-BADGE-002 — لوحة المشرف تعرض الشارة كنص فقط

`apps/web/src/app/admin/(dashboard)/students/[id]/page.tsx` يحسب badge count ويعرض `badge.label` داخل chip، دون الأصل البصري المعتمد.

### AUD-BADGE-003 — حزمة الشارات المعتمدة غير مدمجة في `public`

الفحص الحالي لـ`apps/web/public` وجد `audio`, `brand`, `characters` وأصول Next الافتراضية، ولا يوجد reward/levels bundle معتمد.

حزمة `Himma_Characters_Badges_UI_Kit_v1.0` نفسها تثبت الأصول التالية:

- BDG-01 نجمة واحدة — `hem-bdg-01-star-one.svg`
- BDG-02 نجمتان — `hem-bdg-02-stars-two.svg`
- BDG-03 ثلاث نجوم — `hem-bdg-03-stars-three.svg`
- BDG-04 مستكشف الحروف — `hem-bdg-04-letter-explorer.svg`
- BDG-05 بطل الكلمات — `hem-bdg-05-word-hero.svg`
- BDG-06 نجم الفهم — `hem-bdg-06-comprehension-star.svg`

وتوصي الحزمة باستخدام SVG للشارات في شاشة النتيجة ومسار التقدم.

### AUD-BADGE-004 — عدم تطابق شارة L3

Backend الحالي في `BADGE_BY_LEVEL`:

- L1 `مستكشف الحروف`
- L2 `بطل الكلمات`
- L3 `قارئ متميز`

الحزمة المعتمدة:

- BDG-04 `مستكشف الحروف`
- BDG-05 `بطل الكلمات`
- BDG-06 `نجم الفهم`

إذن L3 له حقيقتان مختلفتان. لا يغير الاسم عشوائيًا أثناء التدقيق؛ الحل هو Reward Catalog canonical واحد.

### AUD-BADGE-005 — Journey completion وBadge completion لهما مصدران مختلفان

هذا ليس احتمالًا نظريًا فقط. التسلسل الحالي حتمي عند early promotion:

1. `evaluate_student()` يستدعي `ensure_rewards()` **قبل** تنفيذ transition.
2. L1/L2 يسمحان بالترقية عند `>=6` Core إذا تحققت بقية بوابات V4.
3. `ensure_rewards()` لا يمنح شارة المستوى إلا عند `>=10` Core.
4. `adaptation_runtime` بعد ذلك يغلق جلسة المستوى ويسجل transition evidence.
5. `journey.py` يعتبر L1/L2 `completed` من persisted early-promotion evidence حتى لو كانت 6–9 Core.
6. أي استدعاء لاحق لـ`ensure_rewards()` يبقى مشروطًا بـ10 Core، لذلك لا تتحول حقيقة اكتمال المستوى إلى badge.

وتؤكد `test_m09_full_single_candidate_journey.py` أن L1/L2 يترقيان فعليًا في المسار الكامل مع `6 <= completed < 10`، لكنها لا تتحقق من الشارة.

**Severity:** P1.  
**Correct owner of truth:** خدمة/عقد واحد لحالة اكتمال المستوى، يستهلكه Journey + Rewards + gates ذات الصلة، مع الحفاظ على early-promotion المعتمد.

### AUD-BADGE-006 — E2E للشارات غير مغلق

الاختبارات الحالية تثبت أجزاء مهمة فقط:

- `test_adaptation_runtime.py` يثبت نجومًا once/idempotent، واستبعاد media-gap/unresolved audio.
- `test_adaptation.py` وscenario matrix يثبتان بوابات early promotion/L3.
- `test_m09_full_single_candidate_journey.py` يثبت رحلة L1→L2→L3 مع early promotion.
- `apps/web/src/app/student/page.test.tsx` يمرر rewards كـ`[]` في سيناريوهاته ولا يختبر badge rendering.

لا يوجد عقد واحد يثبت:
`promotion/completion -> badge once -> correct catalog identity/asset -> Student visible -> Admin visible -> refresh/persistence`.

**Status:** OPEN GATE، ينفذ في A08 بعد إصلاح A10.

### AUD-BADGE-007 — فشل Rewards API يظهر للطالب كأنه صفر مكافآت

في Student Home، فشل `/api/rewards` لا يتحول إلى حالة `unavailable/error` مستقلة؛ القائمة تبقى فارغة ويظهر `totalStars = 0`. هذا يخلط «لا توجد مكافآت» مع «تعذر تحميل سجل المكافآت» ويعرض حقيقة غير مؤكدة للطالب.

**Severity:** P2 مع أثر ثقة/UX واضح.  
**Root fix:** state صريح `loading / loaded / unavailable` للمكافآت، وعدم تمثيل fetch failure كرصيد صفر.

### AUD-BADGE-008 — API لا يحمل هوية بصرية/كتالوجية مستقرة

Reward payload الحالي يخرج الهوية الحدثية (`key/type/stars/label/details`) لكنه لا يخرج `catalog_id/asset_id/asset_url/catalog_version`. لذلك لا تستطيع الواجهات ربط الحدث بالأصل المعتمد دون إنشاء mapping محلي جديد، ما يعيد نفس split-brain الحالي.

**Severity:** P1 contract gap.  
**Root fix:** Reward Catalog canonical واحد مع stable IDs، والـAPI يعيد presentation metadata من هذا المصدر مع الحفاظ على `RewardEvent.label/details` التاريخية وعدم إعادة كتابة الماضي صامتًا.

### AUD-BADGE-009 — FK النجوم إلى Attempt لديه مخاطرة حذف تاريخي يجب حمايتها

Model/migration يعرّف `RewardEvent.attempt_id -> attempts.id ON DELETE CASCADE`. لم يثبت في هذه الجولة وجود مسار production طبيعي يحذف Attempts، كما أن retake contract الحالي يصرح بحفظ المحاولات السابقة وعدم حذفها؛ لذلك هذه **ليست مطالبة بوجود فقد بيانات حالي**.

لكنها مخاطرة schema/history: أي cleanup/reset/delete لاحق لمحاولة يمكن أن يمحو star RewardEvent المرتبط بها تلقائيًا.

**Severity:** P2 CARRY-TO-A10/A07.  
**Required action:** قبل أي cleanup أو FK تغيير، inventory لمسارات حذف Attempt، ثم اختيار سياسة history صريحة (restrict/retain snapshot/soft-delete) دون كسر السجل الأكاديمي.

---

## 5. التصميم الجذري المطلوب لاحقًا — لا ينفذ أثناء A05

### Reward Catalog واحد

العقد المرشح:

```text
BDG-01 -> stars:1 -> hem-bdg-01-star-one.svg
BDG-02 -> stars:2 -> hem-bdg-02-stars-two.svg
BDG-03 -> stars:3 -> hem-bdg-03-stars-three.svg
BDG-04 -> level:1 -> مستكشف الحروف -> hem-bdg-04-letter-explorer.svg
BDG-05 -> level:2 -> بطل الكلمات -> hem-bdg-05-word-hero.svg
BDG-06 -> level:3 -> نجم الفهم -> hem-bdg-06-comprehension-star.svg
```

ويخرج API على الأقل: `key`, `catalog_id`, `type`, `stars`, `label`, `asset_id/asset_url`, `level_id`, `created_at`، مع versioning إذا كان الكتالوج قابلًا للتطور.

### مصدر واحد لاكتمال المستوى

لا يجوز أن يحتفظ Journey بتعريف، وRewards بتعريف ثانٍ، وPosttest/واجهات بتعريف ثالث. المطلوب state/contract واحد مبني على transition/session evidence الرسمي، مع المحافظة على early-promotion لـL1/L2 وعلى 10/10 لـL3.

---

## 6. أصول يجب حمايتها أثناء A10

1. `RewardEvent` التاريخي لا يحذف.
2. `reward_key` uniqueness لا يكسر.
3. النجوم المكتسبة سابقًا لا يعاد حسابها بما يغير التاريخ دون migration موثقة.
4. pending/rejected/unresolved audio لا يصبح reward evidence.
5. early-promotion لا يعاد إلى legacy 10-core لمجرد إصلاح الشارة.
6. AdminUI يعاد استخدامه بدل Design System ثالث.
7. أصول BDG الرسمية تستخدم بمعرفاتها؛ لا يعاد رسمها/تسميتها اعتباطيًا.
8. أي تغيير في FK/history يخضع لاختبار migration + history preservation.

---

## 7. بوابات القبول المؤجلة

### Admin UI
- dashboard shell/tokens/primitives موحدة أو استثناء موثق.
- Student Details يمر 320/360/390/430/768/desktop دون overflow.
- Settings لا يحتفظ بنظام buttons/panels/forms موازٍ.
- `/admin/account` يحسم بعد dependency scan.
- keyboard/focus/error/loading/mobile states مختبرة.

### Rewards/Badges
- Reward Catalog canonical.
- BDG-04/05/06 تطابق الأصول المعتمدة.
- completion semantics موحدة مع Journey.
- Student/Admin يعرضان الشارات بصريًا.
- assets موجودة و404-free.
- API failure لا يمثل كرصيد صفر.
- no duplication على repeat/refresh.
- early-promotion badge regression test.
- Backend + frontend + integration + browser E2E خضراء فعليًا.

---

## 8. إغلاق مرحلة A05

A05 مغلق الآن كـ **static/source audit**، وليس كإصلاح أو release gate:

- Persistence/API/idempotency basics: **VERIFIED**.
- Audio/media neutrality في rewards: **VERIFIED BY SOURCE + EXISTING TESTS**.
- Visual integration: **GAP P1**.
- L1/L2 completion semantics: **GAP P1**.
- Catalog/API presentation identity: **GAP P1**.
- Student reward failure-state: **GAP P2**.
- Historical FK risk: **CARRY P2**.
- Full Badge E2E: **OPEN FOR A08**.

**نقطة الاستكمال التالية:** `A06 — Images / Media`، بدءًا من تقرير الاستخدام الكانوني الموجود والجرد الفعلي للأصول/التكرارات/unused references. لا حذف ولا استبدال أثناء التدقيق؛ فقط إثبات الدلالة والاعتماديات ثم نقل القرارات إلى Master Gap Register.
