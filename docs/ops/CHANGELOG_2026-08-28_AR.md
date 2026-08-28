# سجل التغييرات — مراجعة وصيانة 2026-08-28

## قبل المراجعة

آخر Recovery documentation كانت تعتبر UI/Media/Admin/Student recovery جاهزة للإغلاق، مع P07 فقط كمرحلة خارجية معلقة.

## ما تغير في الفهم التنفيذي

### 1. اكتشاف برنامج صيانة أوسع

المراجعة الجديدة أثبتت أن المنتج يحتاج صيانة أكاديمية وUX أعمق قبل التسليم النهائي، لا مجرد استكمال P07.

### 2. CI الحالي

بعد Quality Gate #191 الأخضر تمت 12 commit إضافية. الرأس البرمجي `0f46e7...` فشل في Integration/Playwright في Run #206، مع نجاح Frontend وBackend.

### 3. Frontend foundation

أضيف Tailwind/PostCSS فعليًا لمعالجة خلل استخدام responsive utilities غير المدعومة سابقًا. يلزم validation بصري بعد إصلاح CI.

### 4. Adaptation improvements already coded

- immediate reinforcement for sub-70 activity evidence.
- promotion waits for 10/10 core.
- new session per level transition.
- safer level-scoped low-decision history.
- regression coverage.

### 5. Academic redesign captured

- Placement منفصل عن Learning Adaptation.
- score bands 80 / 70–79 / <70.
- Level Completion Gate.
- L1→L2→L3 journey.
- reinforcement return-to-core verification.
- 20/40/40 placement scoring and skill gates planned.

### 6. Reinforcement content

اعتماد 18 تقوية جديدة:

- L1 +7.
- L2 +6.
- L3 +5.

الإجمالي المستهدف 33.

### 7. Audio

حصر 50 أصلًا موجودًا، وفجوتين فقط: «موز» و«سَا». التقويات الجديدة لا تزيد الفجوات.

### 8. TEMP Audio Skip

وضع تجريبي مؤقت يسمح بتجاوز read-aloud دون ملف/درجة/Reward/Adaptation evidence.

### 9. Product UX audit

الحالة الحالية Functional Recovery Baseline وليست Final Product UI.

أضيفت خطة:

- Student full-screen task stage.
- unified student UI kit.
- contextual character/instructions.
- Admin IA/Action Center.
- Student Profile tabs.
- responsive/accessibility gates.

### 10. ASR

تثبيت Reference-Guided Arabic Reading Analysis كهدف معماري، مع بقاء provider/calibration/privacy خارجيًا.

## ملفات جديدة أضيفت

- `docs/ops/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-08-28_AR.md`
- `docs/handoff/READ_FIRST_2026-08-28_AR.md`
- `docs/ops/CURRENT_STATE_2026-08-28_AR.md`
- `docs/ops/FULL_MAINTENANCE_PLAN_2026-08-28_AR.md`
- `docs/ops/OPEN_ITEMS_2026-08-28_AR.md`
- `docs/ops/DECISIONS_2026-08-28_AR.md`
- `docs/ops/progress_2026-08-28.json`
- `docs/specs/ADAPTATION_REINFORCEMENT_REDESIGN_2026-08-28_AR.md`
- `docs/specs/REINFORCEMENT_CONTENT_ADDITIONS_2026-08-28_AR.md`
- `docs/specs/AUDIO_INVENTORY_AND_GAPS_2026-08-28_AR.md`
- `docs/design/PRODUCT_UX_REBUILD_PLAN_2026-08-28_AR.md`

## أول إجراء بعد هذا التوثيق

M00: إصلاح Run #206 lineage حتى Quality Gate أخضر، ثم تحديث evidence قبل M01.
