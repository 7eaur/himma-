# هِمّة — Master Continuity Handoff — A05

**التاريخ:** 2026-09-10  
**الحالة:** `AUDIT CONTINUATION — A05`  
**المستودع:** `7eaur/himma-`  
**الفرع:** `audit/comprehensive-repository-review-2026-09-10`  
**HEAD الموثق قبل إنشاء هذا handoff:** `1f15e468b28453258609e139023fce1d7cdaeae3`

---

## الحقيقة التنفيذية

Git الحالي هو الحقيقة التنفيذية. لا Merge ولا Deploy ولا Docker ولا Production fixes أثناء A05. لا يبدأ A10 قبل اكتمال A00–A09 وسجل الفجوات الجامع.

## المراحل المغلقة مؤخرًا

- A03: مكتمل audit-only. التقرير: `docs/maintenance/HIMMA_A03_AUDIO_SPEECH_REVIEW_ADAPTATION_AUDIT_2026-09-10_AR.md`.
- A04: مكتمل audit-only. التقرير: `docs/maintenance/HIMMA_A04_ADMIN_MOBILE_DEEP_AUDIT_2026-09-10_AR.md`.
- السجل الجامع محدث في `docs/maintenance/HIMMA_COMPREHENSIVE_REPOSITORY_AUDIT_2026-09-10_AR.md`.

## ثوابت لا تُرجع للخلف

- canonical content = 125 عنصرًا.
- pending/uploaded audio محايد أكاديميًا.
- pending لا يمنع same-level navigation/support؛ يحجز فقط irreversible promotion/L3 completion.
- rerecord مهمة مؤجلة صريحة ويجب أن تنشئ AudioSubmission جديدًا وتحفظ القديم.
- graded فقط يدخل academic evidence.
- latest submission هو active audio state.
- لا Production ASR Provider معتمد؛ لا mock أو ادعاء اكتمال ASR.
- لا حذف للتاريخ الأكاديمي أو reward/audio history.

## نقطة الاستكمال الحالية — A05 Rewards / Badges

ابدأ من `docs/maintenance/HIMMA_A04_A05_ADMIN_BADGES_AUDIT_2026-09-10_AR.md` ثم عمّق ولا تعيد الجرد من الصفر.

المثبت مبدئيًا:
- RewardEvent persistent وidempotent على `UNIQUE(student_id, reward_key)`.
- stars/badge award logic وStudent/Admin APIs موجودة.
- Student UI لا يعرض badge assets.
- Admin Student Detail يعرض badge label/chip فقط.
- حزمة الشارات الرسمية غير مدمجة في public/reward display contract.
- L3 label في Backend `قارئ متميز` بينما BDG-06 في الحزمة `نجم الفهم`.
- early-promotion completion في Journey لا يطابق شرط badge legacy `10 core`.
- Badge E2E الكامل غير مغلق.

## المطلوب لإغلاق A05

1. تتبع `RewardEvent`, migration, `_stars_for_attempt`, `_core_flow_complete`, `ensure_rewards` وكل consumer/API.
2. مقارنة مفهوم level completion في Journey/transition مع badge award semantics، وتحديد owner واحد للحقيقة دون تطبيق إصلاح بعد.
3. جرد reward rendering في Student/Admin وعدم الخلط بين stars وbadges.
4. تثبيت أسماء ومعرفات الأصول المعتمدة من الحزمة وعدم إعادة رسمها أو تسميتها اعتباطيًا.
5. فحص tests الحالية للنجوم/idempotency/media-gap/audio/early-promotion/badges وتوثيق missing E2E بدقة.
6. تسجيل findings بصيغة Master Gap Register-compatible.
7. عند الإغلاق: تحديث السجل الجامع، إنشاء تقرير A05 تفصيلي إذا لزم، ثم handoff إلى A06 Images/Media ومتابعة التدقيق دون توقف.

**لا تُشغّل أو تدّعي Test PASS جديدًا إلا إذا تم تشغيله فعليًا.**