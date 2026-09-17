# ابدأ من هنا — مستودع هِمّة

هذه نقطة الدخول التنفيذية الحالية لمنصة **هِمّة**.

## المستودع والحالة

- Repository: `7eaur/himma-`
- Execution branch: `audit/comprehensive-repository-review-2026-09-10`
- Current phase: `A10`
- A00–A09: CLOSED AUDIT.
- W1–W6: **CLOSED GREEN**.
- Stop boundary: **NO A11 / NO DEPLOY / NO MERGE** دون تكليف جديد صريح.

## ترتيب القراءة

1. `NEXT_CONVERSATION_PROMPT.md`
2. `docs/ops/STATUS.md`
3. `docs/ops/progress.json`
4. `docs/ops/RESUME_HERE.md`
5. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-17_A10_W6_GREEN_AR.md`
6. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_STATUS_UPDATE_2026-09-16_AR.md`
7. `docs/specs/SOURCE_OF_TRUTH.md`
8. السجل التاريخي بعد ذلك فقط.

Source of Truth:

`live code → PostgreSQL schema/Alembic → executable tests + exact-SHA CI → canonical contracts → current status/handoff → history`

## W6 — exact tested evidence

Tested functional SHA:

`c5174f33b11be80500fdd72c0456efbef062f5ad`

Commit: `fix(auth): count only failed login attempts`

على هذا SHA نفسه:

- Quality Gate #902 / Run `35198824643`: **SUCCESS**.
- M09 Release Readiness #211 / Run `35198824646`, job `105128375595`: **SUCCESS**.
- Quality Gate backend: `893 passed, 5 warnings`.
- Quality Gate Integration Playwright: `20 passed (3.8m)`.
- M09 declared Playwright product regression: `19 passed (4.4m)`.
- PostgreSQL restore verification: passed.
- Object-store restore: verified for 43 objects.
- Backup artifacts remained ephemeral in CI.

أي commit توثيق لاحق هو docs-only وليس functional evidence. استخدم SHA أعلاه كدليل W6.

## Root cause المغلق

في M09 #210 كانت ثلاثة اختبارات Playwright تحصل على `429` من `POST /auth/login`. كان `enforce_auth_rate_limit()` يزيد عداد IP قبل التحقق من كلمة المرور، بينما النجاح يمسح عداد المعرّف فقط؛ لذلك كانت تسجيلات الدخول الصحيحة من runner مشترك تستهلك ميزانية IP وتمنع تسجيلًا صحيحًا لاحقًا.

الإصلاح أبقى pre-auth blocking وRedis fail-closed، لكنه سجّل عدادات IP/identifier فقط بعد فشل بيانات الاعتماد. ما زال هجوم المعرفات المتناوبة يستهلك ميزانية IP المشتركة. لم تتغير schema أو عقود المنتج أو الاختبارات/التغطية.

## العقود والحدود

- Placement: `<50=L1`, `50..<80=L2`, `80..100=L3`.
- Activity: `>=80 success`, `70..<80 guided retry`, `<70 reinforcement`.
- L1/L2 promotion بعد >=6 Core مع evidence؛ L3 يتطلب 10 Core؛ لا automatic demotion.
- Manual override لا يعني completion/badge؛ أحدث ثلاث evidences فعالة بأوزان 50/30/20.
- Runtime: 125 items و44 skills؛ approval `HIMMA-CONTENT-APPROVAL-2026-09-08`.
- لا Student Audio Skip؛ Human Supervisor Review authority؛ Production ASR `AUD-A03-008` ما زال external-approval blocked.
- `AUD-SEC-006` deployed-header verification و`AUD-A11Y-005` manual human screen-reader و`AUD-GIT-001` final merge لم تُنفذ.

No Docker. No fake ASR. No weakened tests. No runtime repair overlays. No history deletion. لا تبدأ A11/Deploy/Railway/Production/final merge دون تكليف جديد.
