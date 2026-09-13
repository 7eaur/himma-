# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت المسؤول الهندسي الكامل عن منصة هِمّة في `7eaur/himma-`.

فرع التنفيذ: `audit/comprehensive-repository-review-2026-09-10`.

قبل أي تعديل اجلب HEAD الحالي وآخر Quality Gate/CI، ثم اقرأ حرفيًا بالترتيب:
1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-13_A10_W4_BADGE_007_ACTIVE_AR.md`
2. `docs/maintenance/HIMMA_A10_W4_AUTOMATION_CHECKPOINT_2026-09-13_BADGE_007_ACTIVE_AR.md`
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
- `AUD-BADGE-004` CLOSED GREEN — `fddc8a59190d1f6522f1639d4f8156982fbaf293`, Run #851 / ID `34732091325`.
- `AUD-BADGE-005` CLOSED GREEN by existing executable canonical completion evidence on the #851-verified baseline; no duplicate code patch was needed.
- `AUD-BADGE-003` BLOCKED_PENDING_APPROVED_ASSET_FILES. Approved `BDG-01..BDG-06` SVG binaries under `assets/rewards/svg` are absent; do not fabricate replacements.
- Current batch only: `AUD-BADGE-007`.
- Exact code SHA: `970416d707639a3cab2f0dfa930b9f78990afe20`.
- Student Home now distinguishes reward failure/malformed data from legitimate successful zero, and focused frontend tests cover HTTP 500 / empty / populated responses.
- Quality Gate #853 / Run ID `34733663693` ACTIVE on the exact SHA.

## إلزامي
Inspect #853 first. If ACTIVE/QUEUED, do not start code or another W4 gap. If FAILURE, inspect the first true failure and root-fix `AUD-BADGE-007` only without weakening tests. If SUCCESS including Integration/Playwright, close `AUD-BADGE-007`, update STATUS/progress/continuity/checkpoint/NEXT with exact SHA and Run ID, then select exactly one next independent W4 gap from the Master Gap Register.

Do not work around `AUD-BADGE-003` by generating substitute badge artwork.

بعد W4 فقط: W5 ثم W6. إذا أصبحت W6 Green توقف. ممنوع A11 أو Deploy/Railway/Production أو final merge.

قيود ثابتة: لا Docker، لا fake ASR، لا Temporary Audio Skip، لا حذف history، لا دمج Speech/Pronunciation Lab، ولا إضعاف tests.
