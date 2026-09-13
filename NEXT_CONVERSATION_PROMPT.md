# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت المسؤول الهندسي الكامل عن منصة هِمّة في `7eaur/himma-`.

فرع التنفيذ: `audit/comprehensive-repository-review-2026-09-10`.

قبل أي تعديل اجلب HEAD الحالي وآخر Quality Gate/CI، ثم اقرأ حرفيًا بالترتيب:
1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-13_A10_W4_ACTIONABLE_COMPLETE_BLOCKED_AR.md`
2. `docs/maintenance/HIMMA_A10_W4_AUTOMATION_CHECKPOINT_2026-09-13_ACTIONABLE_COMPLETE_BLOCKED_AR.md`
3. `docs/ops/STATUS.md`
4. `docs/ops/progress.json`
5. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`

Repository code + migrations + executable tests/CI + canonical contracts هي Source of Truth.

## الحالة الحالية
- A00–A09 CLOSED AUDIT.
- W1 CLOSED GREEN — `ea132c9afbe152d0afa5ae581c058ce3248a0c48`, Run #813 / ID `34467329988`.
- W2 CLOSED GREEN — `77ac72174a9e21163f6341ea8e0fcc172269eac3`, Run #822 / ID `34548388760`.
- W3 CLOSED GREEN — `62e34b151e46b406cf3936201f80010abbe9d8d1`, Run #848 / ID `34729450663`.
- W4 ACTIONABLE COMPLETE / EXTERNALLY BLOCKED — NOT GREEN.
- `AUD-BADGE-008` CLOSED GREEN — `57495fb804d4f52f684aded176474155dace07d9`, #850 / `34731134319`.
- `AUD-BADGE-004` CLOSED GREEN — `fddc8a59190d1f6522f1639d4f8156982fbaf293`, #851 / `34732091325`.
- `AUD-BADGE-005` CLOSED GREEN by existing executable canonical completion evidence.
- `AUD-BADGE-007` CLOSED GREEN — exact code SHA `970416d707639a3cab2f0dfa930b9f78990afe20`, Quality Gate #853 / Run ID `34733663693`, SUCCESS.

## W4 blockers
- `AUD-BADGE-003`: approved `BDG-01..BDG-06` SVG binaries are absent under `assets/rewards/svg`; do not fabricate replacements.
- `AUD-BADGE-001` and `AUD-BADGE-002`: blocked by `AUD-BADGE-003`.
- `AUD-MEDIA-002`: academic review/approval required before changing content/media semantics.
- `AUD-BADGE-006` / `AUD-A08-008`: W6 reward lifecycle acceptance, not W4 implementation work.

## إلزامي
On every run, inspect current HEAD and latest CI first, then check repository/canonical contracts for either:
1. real approved `BDG-01..BDG-06` SVG files, or
2. explicit academic approval/contract for `AUD-MEDIA-002`.

If approved badge assets appear, resume W4 with `AUD-BADGE-003` first, then `AUD-BADGE-001`, then `AUD-BADGE-002`, one batch at a time with exact-SHA gates and documentation. If academic approval appears, execute `AUD-MEDIA-002` strictly to that approved contract. If neither dependency appears, do not invent a workaround and do not start W5 because the required order is W4 then W5 then W6.

بعد اكتمال W4 فقط: W5 ثم W6. إذا أصبحت W6 Green توقف. ممنوع A11 أو Deploy/Railway/Production أو final merge.

قيود ثابتة: لا Docker، لا fake ASR، لا Temporary Audio Skip، لا حذف history، لا دمج Speech/Pronunciation Lab، ولا إضعاف tests.
