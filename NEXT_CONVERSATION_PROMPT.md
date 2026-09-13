# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت المسؤول الهندسي الكامل عن منصة هِمّة في `7eaur/himma-`.

فرع التنفيذ: `audit/comprehensive-repository-review-2026-09-10`.

قبل أي تعديل اجلب HEAD الحالي وآخر Quality Gate/CI، ثم اقرأ حرفيًا بالترتيب:
1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-13_A10_W4_BADGE_004_CLOSED_AR.md`
2. `docs/maintenance/HIMMA_A10_W4_AUTOMATION_CHECKPOINT_2026-09-13_BADGE_004_CLOSED_AR.md`
3. `docs/ops/STATUS.md`
4. `docs/ops/progress.json`
5. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`

Repository code + migrations + executable tests/CI + canonical contracts هي Source of Truth.

## الحالة الحالية
- A00–A09 CLOSED AUDIT.
- W1 CLOSED GREEN — `ea132c9afbe152d0afa5ae581c058ce3248a0c48`, Run #813 / ID `34467329988`.
- W2 CLOSED GREEN — `77ac72174a9e21163f6341ea8e0fcc172269eac3`, Run #822 / ID `34548388760`.
- W3 CLOSED GREEN — `62e34b151e46b406cf3936201f80010abbe9d8d1`, Run #848 / ID `34729450663`.
- W4 ACTIVE.
- `AUD-BADGE-008` CLOSED GREEN — `57495fb804d4f52f684aded176474155dace07d9`, Run #850 / ID `34731134319`.
- `AUD-BADGE-004` CLOSED GREEN — exact code SHA `fddc8a59190d1f6522f1639d4f8156982fbaf293`, Quality Gate #851 / Run ID `34732091325`; Security/Frontend/Backend/Integration-Playwright SUCCESS.
- `AUD-BADGE-003` is BLOCKED_PENDING_APPROVED_ASSET_FILES: the approved map references `BDG-01..BDG-06` under `assets/rewards/svg`, but the binaries are absent from the current branch. Do not fabricate replacements.
- First independent incomplete candidate: `AUD-BADGE-005`.

## إلزامي
Inspect `AUD-BADGE-005` literally before changing code: read `services/api/level_completion.py`, `services/api/adaptation.py`, `services/api/journey.py` and their executable tests. Verify one canonical completion truth drives both Journey and Rewards for early promotion after 6–9 successful main activities, ordinary 10/10 completion, and manual/override cases. If acceptance is already satisfied, close only with explicit executable evidence; if not, root-fix only this gap and add focused tests, then run an exact-SHA Quality Gate and document it before choosing another W4 gap.

Do not work around `AUD-BADGE-003` by generating substitute badge artwork.

بعد W4 فقط: W5 ثم W6. إذا أصبحت W6 Green توقف. ممنوع A11 أو Deploy/Railway/Production أو final merge.

قيود ثابتة: لا Docker، لا fake ASR، لا Temporary Audio Skip، لا حذف history، لا دمج Speech/Pronunciation Lab، ولا إضعاف tests.
