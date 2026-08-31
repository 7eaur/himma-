# ابدأ من هنا — مستودع هِمّة

هذه نقطة الدخول لأي محادثة أو وكيل جديد يعمل على منصة هِمّة الحالية.

## 1) اقرأ هذا أولًا

المرجع التنفيذي الأحدث والأشمل:

`docs/ops/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-08-31_AR.md`

ثم اقرأ:

- `docs/ops/STATUS.md`
- `docs/ops/progress.json`
- `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md`
- `docs/specs/SOURCE_OF_TRUTH.md`

**لا تبدأ من وثائق أغسطس القديمة وحدها، ولا تعتمد على ذاكرة المحادثة بدل HEAD/CI الحاليين.**

## 2) المستودع الحالي

- Repository: `7eaur/himma-`
- Working branch: `recovery/ui-media-admin-overhaul`
- آخر baseline تنفيذي موثّق أخضر قبل تحديثات التوثيق بتاريخ 2026-08-31:
  `fbf3e4c835e87c142422db9fe35f7dec60fee090`

بعد فتح جلسة جديدة افحص branch HEAD الحالي وحالة GitHub Actions؛ تحديثات الوثائق نفسها تحرّك HEAD.

## 3) الحالة المختصرة

- Runtime catalog: **125 item**.
- Reinforcement: **35**.
- Skills: **44**.
- Student QX/UI baseline: منجز.
- Generated sequence educational assets: 10 ومربوطة بالruntime.
- Reinforcement lifecycle + verification/escalation: منجز baseline.
- Reports/exports/per-skill descriptive evidence: منجز baseline.
- R1 early promotion gates: منجزة ومقفلة بالاختبارات الحالية.
- R2 active-session handoff بعد promotion: مُصلح.
- R3 supervisor-authorized assessment retake/index history: مُصلح baseline.
- M08 real speech production: **غير مكتمل / external-gated**.
- M09 Release/UAT: **أولوية العمل الداخلية التالية**.
- Static audio missing: `موز`, `سَا`.

## 4) قاعدة الاستمرار

قبل أي تعديل:

1. اقرأ handoff الكامل.
2. افحص HEAD الحالي.
3. افحص Main Quality Gate وResponsive Visual Gate لنفس SHA.
4. إذا يوجد failure أصلحه أولًا ولا تتجاوزه.
5. إن كانت البوابات خضراء، أكمل أول gap حقيقي من handoff؛ افتراضيًا M09، بينما M08 يبقى منفصلًا حتى تتوفر provider/calibration/privacy decisions.

## 5) قيود لا تُكسر

- لا تعدّل `stage/04-production-slice` أو `stage/02-content` مباشرة.
- لا force push / reset hard / clean destructive.
- لا تغيّر semantics للمحتوى الأصلي المعتمد بلا مصدر.
- لا تجعل report evidence قاعدة mastery جديدة.
- لا تعتبر temporary audio skip حلًا production.
- لا تعلن PASS دون SHA + CI evidence.
- لا تطلق production أو تدمج الفروع الأساسية دون موافقة صريحة من المستخدم.

## 6) تشغيل المشروع

اقرأ scripts/README/package metadata الحالية قبل التشغيل ولا تفترض أوامر قديمة. استخدم طريقة التشغيل المحلية الموجودة في المستودع، ولا تجعل Docker المحلي شرطًا على المستخدم. CI قد يستخدم service containers بشكل مستقل.

## 7) المواد المرجعية

- `reference/original/`: المصادر الأصلية — لا تُحرّفها.
- `reference/derived/`: نسخ مشتقة للبحث.
- `reference/ui-prototype/`: مرجع تصميم/تفاعل تاريخي، وليس مصدر runtime production.
- `assets/`: الهوية/الشخصيات/الصور/الصوت.
- `apps/`, `services/`, `packages/`: الكود الإنتاجي الحالي؛ اقرأه فعليًا ولا تعتمد على أسماء الملفات فقط.

الحالة المستمرة في `docs/ops/STATUS.md` و`docs/ops/progress.json`، لكن عند التعارض تكون وثيقة handoff الأحدث + الكود والاختبارات + CI الحالي هي المرجع التنفيذي.