# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت المسؤول الهندسي الكامل عن منصة هِمّة في `7eaur/himma-`.

فرع التنفيذ: `audit/comprehensive-repository-review-2026-09-10`.

قبل أي تعديل اجلب HEAD الحالي وآخر Quality Gate/CI، ثم اقرأ حرفيًا بالترتيب:
1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-13_A10_W4_BADGE_008_ACTIVE_AR.md`
2. `docs/maintenance/HIMMA_A10_W4_AUTOMATION_CHECKPOINT_2026-09-13_BADGE_008_ACTIVE_AR.md`
3. `docs/ops/STATUS.md`
4. `docs/ops/progress.json`
5. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`

Repository code + migrations + executable tests/CI + canonical contracts هي Source of Truth.

## الحالة الحالية
- A00–A09 CLOSED AUDIT.
- W1 CLOSED GREEN — `ea132c9afbe152d0afa5ae581c058ce3248a0c48`, Run #813 / ID `34467329988`.
- W2 CLOSED GREEN — `77ac72174a9e21163f6341ea8e0fcc172269eac3`, Run #822 / ID `34548388760`.
- W3 CLOSED GREEN — exact SHA `62e34b151e46b406cf3936201f80010abbe9d8d1`, Run #848 / ID `34729450663`; Security/Frontend/Backend/Integration-Playwright SUCCESS.
- W4 ACTIVE.
- Current batch only: `AUD-BADGE-008` canonical Reward Catalog/API.
- Exact code gate SHA: `57495fb804d4f52f684aded176474155dace07d9` (tree `ec345b3be56312e9db8a7dd28e16f2e92ca7a9b0`).
- Implemented versioned catalog `HIMMA_REWARD_CATALOG_1.0.0`, approved `BDG-01..BDG-06` identity, authenticated `GET /reward-catalog`, and contract/history compatibility tests.
- Quality Gate #850 / Run ID `34731134319` is the authoritative exact-SHA gate and is ACTIVE/QUEUED.
- A duplicate predecessor Run #849 / `34731112994` exists from staging-branch creation on the same code tree; it is not a different implementation path.

## إلزامي
افحص #850 أولًا. إذا بقي ACTIVE/QUEUED فلا تبدأ أي كود آخر. إذا FAILURE اقرأ أول failure حقيقي وأصلحه داخل `AUD-BADGE-008` فقط ولا تضعف الاختبارات. إذا SUCCESS بالكامل بما فيه Integration/Playwright، أغلق `AUD-BADGE-008` رسميًا بالـexact evidence، حدّث STATUS/progress/continuity/checkpoint، ثم اختر gap واحدة فقط تالية من W4 وفق dependencies في Master Gap Register.

بعد W4 فقط: W5 ثم W6. إذا أصبحت W6 Green توقف. ممنوع A11 أو Deploy/Railway/Production أو final merge.

قيود ثابتة: لا Docker، لا fake ASR، لا Temporary Audio Skip، لا حذف history، لا دمج Speech/Pronunciation Lab، ولا إضعاف tests.
