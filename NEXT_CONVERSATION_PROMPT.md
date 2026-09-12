# NEXT CONVERSATION PROMPT — منصة هِمّة

أنت المسؤول الهندسي الكامل عن منصة هِمّة في `7eaur/himma-`.

فرع التنفيذ: `audit/comprehensive-repository-review-2026-09-10`.

قبل أي تعديل اجلب HEAD الحالي وآخر Quality Gate/CI، ثم اقرأ حرفيًا بالترتيب:
1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-13_A10_W3_RUN845_ACTIVE_AR.md`
2. `docs/maintenance/HIMMA_A10_W3_AUTOMATION_CHECKPOINT_2026-09-13_RUN845_ACTIVE_AR.md`
3. `docs/maintenance/HIMMA_A10_W3_EXECUTION_CHECKPOINT_2026-09-12_AR.md`
4. `docs/ops/STATUS.md`
5. `docs/ops/progress.json`
6. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`

Repository code + migrations + executable tests/CI + canonical contracts هي Source of Truth.

## الحالة الحالية
- A00–A09 CLOSED AUDIT.
- W1 CLOSED GREEN — `ea132c9afbe152d0afa5ae581c058ce3248a0c48`, Run #813 / ID `34467329988`.
- W2 CLOSED GREEN — `77ac72174a9e21163f6341ea8e0fcc172269eac3`, Run #822 / ID `34548388760`.
- W3 ACTIVE / NOT GREEN.
- `AUD-A04-008` CLOSED GREEN — `562b4eb3ef831cf7b8b51bd7d5e33145917cb382`, Run #842 / ID `34723513642`.
- Current batch only: `AUD-PERF-004`.
- #843 / ID `34724452979` FAILED on `e10dfe7bba8ea47ebc3fc6fca92c015d80ffe115`: direct ESM loading of `@tailwindcss/postcss` caused Turbopack native Tailwind/LightningCSS bundling errors.
- #844 / ID `34724716140` FAILED on `10620651b96947dd1b2f8d215dbf9acce78e929d`: Security + Backend passed; Frontend typecheck/ESLint/30 unit tests passed, then `next build` failed because Turbopack required `./postcss-strip-google-fonts.cjs` relative to its generated `.next/build/chunks` module and could not find it. Integration was skipped.
- Root-cause correction exact code SHA: `33263107047447ae758ca2092209100ab541efdd`. The local pure-JS PostCSS plugin is resolved with an absolute path derived from `import.meta.url`; Tailwind remains declarative and `font-loading.spec.ts` remains unchanged.
- Quality Gate #845 / Run ID `34725817618` is ACTIVE/QUEUED on exact SHA `33263107047447ae758ca2092209100ab541efdd`.

## إلزامي
افحص #845 أولًا. إذا بقي ACTIVE/QUEUED فلا تبدأ أي كود آخر. إذا FAILURE اقرأ job logs وأصلح أول failure حقيقي فقط داخل `AUD-PERF-004` ولا تضعف `font-loading.spec.ts`. إذا SUCCESS بالكامل بما فيه Integration/Playwright، أغلق `AUD-PERF-004` رسميًا ثم حدّث Master Gap Register وSTATUS/progress/continuity/checkpoint وحدد gap واحدة فقط تالية من W3.

بعد W3 فقط: W4 ثم W5 ثم W6. ممنوع A11 أو Deploy/Railway/Production أو final merge.

قيود ثابتة: لا Docker، لا fake ASR، لا Temporary Audio Skip، لا حذف history، لا دمج Speech/Pronunciation Lab، ولا إضعاف tests.
