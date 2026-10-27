# هِمّة — A04 Deep Audit: Admin UI / Student Details / Mobile

**التاريخ:** 2026-09-10  
**الحالة:** `AUDIT COMPLETE / FINDINGS VERIFIED / NO PRODUCTION FIX APPLIED`  
**الفرع:** `audit/comprehensive-repository-review-2026-09-10`  
**HEAD عند بدء الإغلاق التفصيلي:** `659449da99f77dc9e6e92a0dc97c595d625e8173`

---

## 1. نطاق A04

أُغلق هذا التدقيق على مستوى المصدر والعقود الحالية للوحة المشرف مع ترك التنفيذ الجذري إلى A10. شمل:

- shell/navigation للوحة المشرف.
- Design System الفعلي `components/admin/AdminUI`.
- `/admin/students` و`/admin/students/new` كنماذج مرجعية صحيحة نسبيًا.
- `/admin/students/[id]` بكل تبويباته وعمليات الإدارة والتكيف.
- `/admin/settings` و`/admin/account`.
- عقود Backend المقابلة في `protected.py` و`adaptation.py`.
- تغطية Playwright الحالية للهاتف/التابلت/الديسكتوب والوصولية.

لم تُشغّل Test Suite جديدة أثناء هذه الجولة؛ نتائج الاختبارات المذكورة هنا هي **تغطية موجودة في الشجرة** وليست دعوى PASS جديدة.

---

## 2. ما ثبت أنه صحيح ويجب الحفاظ عليه

1. يوجد Design System إداري مشترك حقيقي في `AdminUI.tsx`/`AdminUI.module.css` يوفّر `AdminPage`, `AdminPageHeader`, `AdminPanel`, `AdminAction`, `AdminResponsiveTable`, `AdminMobileCard`, `AdminStatGrid` وغيرها.
2. `/admin/students` و`/admin/students/new` يستخدمان هذا النظام فعليًا، وقائمة الطلاب تطبق desktop-table/mobile-cards بدل ضغط الجدول على الهاتف.
3. shell الإداري يملك breakpoint للهاتف وقائمة جانبية/حوارًا للهاتف، ويدعم RTL.
4. Student Details يأخذ بيانات الطالب الأساسية من API canonical `/researcher/students/{id}`، ويأخذ history/rewards من APIs الرسمية لا من بيانات mock.
5. `history.at(-1)` متوافق حاليًا مع Backend لأن history يرجع `AdaptationDecision` بترتيب id تصاعدي.
6. يوجد اختبار Admin responsive حقيقي عند 390 و768 ويستطيع دخول Student Details إذا وجد طالبًا، ويوجد smoke matrix عام 360/390/768/1024/1440 لواجهات الدخول العامة.
7. `/admin/account` تم فحصه فعليًا قبل أي قرار حذف؛ لم يعد مجرد افتراض من اسم الملف.

---

## 3. سجل فجوات A04

| ID | Severity | Status | Evidence / Symptom | Root Cause | Correct Owner of Truth | Root Fix لاحقًا | Required Tests | Release Risk | Wave |
|---|---:|---|---|---|---|---|---|---|---|
| AUD-A04-001 | P1 | VERIFIED | Student Details وSettings يعيدان بناء page/header/panel/form/action styles محليًا، و`/admin/account` يحتفظ بطبقة legacy ثالثة؛ تغييرات AdminUI لا تنتشر لهذه الأسطح. | توسع صفحات تاريخية دون فرض owner بصري واحد. | `components/admin/AdminUI` + global design tokens | إعادة تكوين Student Details/Settings من primitives المشتركة، وإبقاء CSS محلي فقط للpatterns الخاصة فعلاً. | visual parity + keyboard + mobile matrix | drift دائم وUX غير متسق | A10-W3 |
| AUD-A04-002 | P1 | VERIFIED | تحميل Student Details يحول فشل history أو rewards إلى `[]` إذا بقي student endpoint ناجحًا؛ الواجهة بعدها تعرض “لا يوجد سجل” و0 نجوم/0 شارات كأنها حقيقة. `refreshAdaptiveEvidence()` أيضًا يتجاهل non-OK بصمت. | client-side composition بدون partial-failure contract. | Student Detail view-model/API aggregation contract | إما endpoint تفصيلي موحد أو state صريح لكل مصدر (`loaded/empty/error`)؛ لا تحويل فشل إلى empty evidence. | history 500 + rewards 200، rewards 500 + history 200، retry/refresh | تضليل المشرف في evidence/المكافآت | A10-W3 |
| AUD-A04-003 | P1 | VERIFIED | تبويب Journey يعرّف `completed = level < student.current_level`. manual override يسمح للمشرف بتغيير المستوى إلى 1/2/3، ويمكن أن يغلق جلسة core جارية وينشئ جلسة للمستوى الجديد دون اشتراط إثبات اكتمال كل مستوى أدنى. قفزة 1→3 قد تجعل UI تعرض L1 وL2 “مكتمل” اعتمادًا على رقم المستوى فقط. | UI اشتق completion من current pointer بدل longitudinal completion evidence. | Journey/completion service الرسمي نفسه الذي تستخدمه transition/posttest/rewards | API يخرج per-level completion state من evidence canonical؛ UI لا يخمن completion من `current_level`. | override 1→3، downgrade، early promotion، incomplete prior level | دقة أكاديمية/تقارير P1 | A10-W1/W3 |
| AUD-A04-004 | P2 | VERIFIED | `/admin/account` موجود ويعرض profile/logout عبر `/api/me`، غير موجود في shell nav، يستخدم `admin.module.css` + inline/global styles، ويتداخل مع `/admin/settings`. `/api/me` يعيد `full_name = username` للمشرف، فتظهر حقول تبدو منفصلة وهي نفس القيمة. | سطح حساب قديم بقي بعد إنشاء Settings الأحدث. | `/admin/settings` كمرشح owner لوظائف الحساب، بعد dependency proof | dependency scan نهائي ثم redirect/إزالة آمنة إن لم يوجد عقد مستقل. لا حذف أثناء audit. | route redirect/backlinks/auth regression | legacy UX/maintenance | A10-W3 |
| AUD-A04-005 | P1 | VERIFIED | Student Details لا يملك بوابة viewport كاملة. `admin-responsive.spec.ts` يختبر 390 و768 فقط، ودخول detail مشروط بوجود طالب ويمكن أن يمر الاختبار دون فتح الصفحة. `responsive-smoke` يغطي 360/390/768/1024/1440 لكن لا يدخل Admin، وP03 screenshots تغطي صفحات Admin عند 390/768/1440 مع استبعاد Student Details. لا تغطية مثبتة لـ320/360/430/Desktop لتفاصيل الطالب. | responsive evidence موزع على smoke عام وصور تاريخية بدل gate خاص بأكثر صفحة إدارية كثافة. | Admin E2E/mobile gate | test data deterministic + direct detail route + 320/360/390/430/768/1440 + overflow/tabs/forms/actions/modal checks. | matrix كاملة مع no-overflow وtouch targets | كسر الهاتف قد يمر CI | A10-W3/A08 |
| AUD-A04-006 | P2 | VERIFIED | mobile menu يعرّف dialog/aria-modal ويغلق بالنقر، لكن المصدر لا يطبق focus trap أو initial focus أو Escape handler أو استرجاع focus/scroll lock صريح. اختبار الوصولية الحالي يثبت ظهور الحوار وحجم target فقط. | modal shell visual قبل إكمال keyboard lifecycle contract. | Admin shell accessibility | dialog focus lifecycle موحد مع Escape + focus return + background interaction guard. | keyboard-only open/tab/escape/return-focus | WCAG/keyboard usability | A10-W3/A07 |
| AUD-A04-007 | P2 | VERIFIED | Settings tabs هي `<nav>` مع buttons وتبديل بصري فقط؛ لا tablist/tab/aria-selected contract. الصفحة تستخدم CSS وتوكنز hardcoded خاصة رغم وجود AdminUI/global tokens. | Settings صُمم كسطح مستقل. | AdminUI + accessible tabs pattern | shared tabs primitive عند ثبوت تكراره أو ARIA disclosure/navigation semantics واضحة دون اختراع DS ثانٍ. | keyboard focus/selection/screen-reader state | accessibility/consistency | A10-W3 |
| AUD-A04-008 | P2 | VERIFIED | تبويب “التسجيلات” في Student Details لا يعرض recording state للطالب؛ يربط إلى `/admin/audio-review` العامة دون student filter/deep-link. النص يتجنب رقمًا وهميًا وهذا صحيح، لكن supervisor يفقد context عند الانتقال. | لا يوجد student-specific recording view contract في صفحة التفاصيل. | review queue/query contract | deep-link/filter آمن بالطالب أو summary حقيقي من review API، بدون counters مشتقة/وهمية. | student with pending/graded/rerecord + back navigation | workflow friction/خطأ اختيار طالب | A10-W3 |

---

## 4. مصفوفة Responsive المثبتة من الاختبارات الحالية

### `admin-responsive.spec.ts`
- 390×844: shell + key Admin routes.
- 768×1024: shell + key Admin routes.
- Student Details: **شرطي**؛ لا يفتح إلا إذا وجد رابط طالب صالح.
- assertions الأساسية: auth، menu/notification visibility، no horizontal overflow، screenshot.

### `responsive-smoke.spec.ts`
- 360×800، 390×844، 768×1024، 1024×768، 1440×900.
- يغطي landing + student login + supervisor login فقط؛ لا يغطي workspace الإداري.

### `p03-screenshots.spec.ts`
- Admin screenshots عند 390/768/1440.
- يغطي dashboard/students/new/audio-review/reports/settings.
- **لا يغطي Student Details**.

### `accessibility-integration.spec.ts`
- dashboard 1440: RTL + focus outline + no overflow.
- menu 390: touch target + dialog visible + nav target height.
- 720: 200% zoom-equivalent no-overflow.
- لا يختبر focus trap/Escape/return-focus داخل mobile dialog.

**النتيجة:** وجود اختبارات Responsive حقيقي، لكنه لا يغلق بوابة Student Details المطلوبة.

---

## 5. قرار ملكية Admin UI

المالك الصحيح المقترح للتنفيذ لاحقًا ليس `settings.module.css` ولا `student-detail.module.css` ولا `admin.module.css` كلٌ على حدة. المالك هو:

`global tokens → AdminUI primitives → page-specific composition`

يسمح CSS محلي فقط عندما يثبت وجود pattern خاص بالصفحة لا يناسب primitive مشتركًا. الهدف ليس جعل كل صفحة متطابقة بصريًا، بل منع ثلاثة عقود مستقلة للspacing/buttons/panels/forms/mobile behavior.

---

## 6. قرار Student Details

لا تعاد كتابة منطقها الوظيفي من الصفر. الصفحة تحتوي عمليات صحيحة ومهمة: status، access code، posttest access، manual override، rewards/history. الإصلاح الجذري لاحقًا يجب أن يفصل:

1. **View data contract**: profile + per-level journey + adaptation + rewards + recording review summary بحالات loading/error مستقلة وصريحة.
2. **Shared admin presentation**: Header/Stats/Panels/Actions/Forms/Tabs.
3. **Academic truth**: لا تستنتج “مكتمل” من `current_level` وحده.
4. **Responsive gate**: 320/360/390/430/768/Desktop مباشرة على detail route وبـfixture deterministic.

---

## 7. `/admin/account` — حكم A04

الحكم الآن: `LEGACY DUPLICATE / ARCHIVE-CANDIDATE`, وليس `DELETE NOW`.

المثبت:
- المسار موجود.
- غير موجود في navigation الحالي.
- وظيفته أضيق من Settings ومتداخلة معها.
- يستخدم طبقة styles قديمة.
- profile “full name” للمشرف يأتي من username نفسه في `/api/me`.

قبل الإزالة في A10 يجب إكمال dependency scan للروابط/redirects/bookmarks/tests، ثم redirect آمن إلى Settings إذا لم توجد وظيفة فريدة.

---

## 8. بوابة إغلاق A04

A04 مغلق كـ**تدقيق وفهم قبل الإصلاح**. لم تُطبق تغييرات Production ولم يتم Merge أو Deploy.

ينتقل سجل التدقيق الآن إلى **A05 — Rewards / Badges end-to-end**. الفجوات الأولية الموجودة في `HIMMA_A04_A05_ADMIN_BADGES_AUDIT_2026-09-10_AR.md` تصبح نقطة البداية، ويجب تعميقها عبر owner-of-truth واحد للمكافآت، semantics اكتمال المستوى، assets الرسمية، Student/Admin rendering، والاختبارات.