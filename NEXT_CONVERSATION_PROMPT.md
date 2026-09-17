# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت مسؤول عن منصة هِمّة في `7eaur/himma-`، فرع `audit/comprehensive-repository-review-2026-09-10`.

## ابدأ من الحقيقة الحية

1. Fetch للـlive branch HEAD.
2. اقرأ `START_HERE_AR.md` ثم `docs/ops/STATUS.md` ثم `docs/ops/progress.json` ثم `docs/ops/RESUME_HERE.md` ثم `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-17_A10_W6_GREEN_AR.md`.
3. فرّق دائمًا بين docs-only HEAD وبين tested functional SHA.

## الحالة الحالية

A00–A09 CLOSED AUDIT. W1–W6 **GREEN**.

Exact tested W6 functional SHA:

`c5174f33b11be80500fdd72c0456efbef062f5ad`

- Quality Gate #902 / Run `35198824643`: SUCCESS.
- M09 #211 / Run `35198824646` / job `105128375595`: SUCCESS.
- QG Playwright: 20 passed.
- M09 Playwright: 19 passed.
- PostgreSQL backup/restore: verified.
- Object storage backup/restore: 43 objects verified.

## Root cause المغلق

كان auth rate limiter في protected runtime يحتسب تسجيلات الدخول الصحيحة ضمن shared IP failure budget، لأن العداد كان يزيد قبل credential validation ولا يُمسح IP counter عند النجاح. نُقل التسجيل ليحدث فقط بعد invalid credentials مع إبقاء الحماية المشتركة وRedis fail-closed. لا تعِد فتح المشكلة بدون regression evidence.

## الإجراء الحالي

**STOP.** لا توجد مهمة تنفيذية داخل W6. لا تبدأ A11 أو deploy أو Railway أو Production أو final merge دون تكليف جديد صريح.

الحدود المتبقية خارج W6:

- Production ASR `AUD-A03-008`: external approval blocked.
- `AUD-SEC-006`: deployed-header verification later/A11.
- `AUD-A11Y-005`: manual human screen-reader verification غير مدعى.
- `AUD-GIT-001`: final merge غير منفذ.

حافظ على العقود الحالية: Placement/activity thresholds، promotion/completion rules، canonical 125 items/44 skills، No Student Audio Skip، append-only audio، Human Supervisor Review authority، automated ASR advisory only.

No Docker. No fake ASR. No weakened tests. No runtime repair overlays. No history deletion.
