# الحالة الحالية لمنصة هِمّة — 2026-08-28

## 1. Git

الفرع: `recovery/ui-media-admin-overhaul`.

Implementation head قبل commits التوثيق الجديدة:

`0f46e7e9421e7617f72fd03de3199df955084cd0`

بعده أضيفت ملفات توثيق الصيانة فقط على نفس الفرع؛ أي منفذ يجب أن يقرأ HEAD الحالي الفعلي قبل العمل.

## 2. CI

Quality Gate #206 / Run ID `33139416128` على `0f46e7e...`:

- Frontend: SUCCESS.
- Backend: SUCCESS.
- Integration/Playwright: FAILURE.

لا تعتبر الفرع أخضر حاليًا اعتمادًا على Run #191 القديم.

Quality Gate #191 كان آخر مرجع أخضر مثبت عند `7c559948f3f75c19f244b7e8942ab6ee3148c614` قبل 12 commit لاحقة.

## 3. التغييرات اللاحقة المهمة

المقارنة من `7c559...` إلى `0f46e7...` أظهرت تغييرات في:

- `apps/web/postcss.config.mjs` — جديد.
- `apps/web/src/app/tailwind.css` — جديد.
- `apps/web/src/app/layout.tsx` — تحميل styling الجديد.
- `services/api/adaptation.py` — تغييرات كبيرة.
- `services/api/adaptation_runtime.py` — تغييرات كبيرة.
- `services/api/temporary_audio_skip.py` — تغييرات كبيرة.
- `services/api/test_adaptation_recovery_regressions.py` — جديد/موسع.

هذه التغييرات لا تُحذف لمجرد أن Playwright فشل.

## 4. ما يعمل كقاعدة

- auth/session/roles.
- PostgreSQL/Alembic.
- MinIO + Redis infrastructure.
- student codes.
- pre/post test lifecycle.
- approved content runtime.
- images/audio routing.
- recording/manual review.
- admin settings/supervisors.
- dashboard/students/reports baseline.
- adaptation/rewards foundation.

## 5. ما ليس نهائيًا

- Placement scoring لا يزال يحتاج مراجعة 20/40/40 + skill gates.
- adaptation يحتاج تثبيت state machine النهائي.
- reinforcement mapping يحتاج Skill Family + 18 additions.
- Automatic Demotion قرار غير محسوم نهائيًا.
- Admin UX غير جاهز للتسليم.
- student activities UI تحتاج full-screen rebuild.
- responsive/accessibility غير مثبتين كقبول نهائي.
- reports الحالية ليست reports البحثية النهائية.
- ASR الحقيقي غير مكتمل/غير معتمد.

## 6. الصوت

- 50 أصلًا ثابتًا موجودًا.
- ينقص «موز» و«سَا» فقط.
- TEMP audio skip مفعل للتجربة عند `HIMMA_TEMP_AUDIO_SKIP=true`.

## 7. التقوية

- 15 أصلية محفوظة.
- 18 إضافة جديدة معتمدة ضمن الصيانة.
- الإجمالي المستهدف 33.
- أهم فجوة أكاديمية مؤكدة: تقوية الشدة في L2.

## 8. Product UI

المنصة الحالية Functional Recovery Baseline، وليست Final Product UI.

أبرز المشاكل:

- عدم اتساق styling التاريخي؛ أضيف Tailwind مؤخرًا ويجب التحقق من أثره.
- student task/activity layout غير مستغل للشاشة بالكامل.
- الشخصية صغيرة في بعض الأنشطة.
- instructions غير contextual بما يكفي.
- Admin dashboard/IA ضعيفان.
- Student Profile admin مكدس ويحتاج tabs.
- loading/empty/error states غير ناضجة.
- mobile/tablet coverage غير كافٍ.

## 9. أول مهمة

افتح Run #206، شخّص Playwright، أصلحه، ثم أعد Quality Gate حتى يصبح كاملًا SUCCESS. بعد ذلك ابدأ M01 من `FULL_MAINTENANCE_PLAN_2026-08-28_AR.md`.
