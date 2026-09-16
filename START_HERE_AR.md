# ابدأ من هنا — مستودع هِمّة

هذه نقطة الدخول التنفيذية لأي محادثة أو وكيل جديد يعمل على منصة هِمّة.

> لا تعتمد على SHA أو حالة محفوظة قبل Fetch للمستودع الحي. اقرأ الحالة الحالية ثم استخدم الوثائق التاريخية لفهم السبب، لا لاستبدال الحقيقة الحالية.

## 1) المستودع والفروع

- Repository: `7eaur/himma-`
- Default branch: `stage/02-content`
- Current execution branch: `audit/comprehensive-repository-review-2026-09-10`
- Current W4 CI helper: `stage/a10-w4-ci`

فرع الـCI helper هو pointer لتشغيل GitHub Actions فقط؛ لا يُدمج. لا تعدّل base branches مباشرة، ولا force push/reset destructive.

## 2) اقرأ هذه المراجع أولًا

بالترتيب:

1. `NEXT_CONVERSATION_PROMPT.md`
2. `docs/ops/STATUS.md`
3. `docs/ops/progress.json`
4. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-16_A10_W4_MEDIA_002_GATE_FAIL_AR.md`
5. `docs/maintenance/HIMMA_A10_W4_MEDIA_002_GATE_FAIL_2026-09-16_AR.md`
6. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
7. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_STATUS_UPDATE_2026-09-16_AR.md`
8. `docs/ops/HIMMA_W4_OWNER_CLIENT_APPROVAL_2026-09-14.md`
9. `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md`
10. `docs/specs/SOURCE_OF_TRUTH.md`
11. `AGENTS.md` ثم `.agents/rules/` المشار إليها فيه.

الـMaster Continuity Handoff يحتوي خريطة قراءة تفصيلية لملفات A00–A09 وW1/W2/W3/W4 القديمة عندما تحتاج فهم تاريخ قرار أو root cause.

## 3) Source of Truth

عند التعارض، استخدم:

`live code → PostgreSQL schema/Alembic → executable tests/exact-SHA CI → current canonical contracts/approved decisions → STATUS/progress → audit/history docs`

المحادثات والـhandoffs القديمة ليست بديلًا عن الحقيقة الحية.

## 4) الحالة الحالية المختصرة

- A00–A09: audit closed؛ لا تعاد.
- W1: GREEN.
- W2: GREEN.
- W3: GREEN.
- W4: IN PROGRESS؛ كل badge implementation items أُغلقت حتى `AUD-BADGE-002`، و`AUD-MEDIA-002` منفذ لكن Quality Gate #857 فشل في stale Sep-08 projection expectation واحدة؛ لذلك W4 ليست Green بعد.
- W5: لم يبدأ.
- W6: لم يبدأ.

التفاصيل والـSHA/run IDs في `docs/ops/STATUS.md` و`docs/ops/progress.json`.

## 5) المنتج والمسار الأكاديمي

المسار العام:

`دخول الطالب → Pretest → placement → level activities → adaptation/reinforcement → canonical completion/promotion → Posttest`

العقود الأساسية:

- Placement: `<50=L1`, `50..<80=L2`, `80..100=L3`.
- Activity: `>=80 success`, `70..<80 guided retry`, `<70 reinforcement`.
- L1/L2 early promotion بعد >=6 Core عند تحقق mastery/critical evidence الكانونية.
- L3 requires 10 Core.
- لا automatic demotion.
- Manual override لا يعني completion أو badge.
- آخر 3 valid active-session evidence بوزن 50/30/20.

## 6) المحتوى الكانوني

الإصدار الحالي:

`HIMMA-CONTENT-APPROVAL-2026-09-08`

الـruntime الحالي يثبت 125 item:

- 30 Pretest
- 30 Posttest
- 30 Core
- 35 Reinforcement
- 44 skills

المسار المعماري:

`approved/versioned contracts → canonical compile/release → deterministic publication → PostgreSQL runtime → structured APIs → deterministic UI`

لا تستبدل هذا المسار بـruntime patch/overlay أو seeder تاريخي جديد.

## 7) الصوت والمراجعة

الأصول الصوتية الثابتة الحالية موثقة في:

`docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`

القواعد الحالية:

- لا Student Audio Skip.
- latest AudioSubmission هو active، والقديم immutable.
- rerecord append-only ومؤجل حتى يفتح الطالب المهمة صراحة.
- uploaded/pending learning audio محايد أكاديميًا؛ same-level learning/support يمكن أن يستمر.
- human Supervisor Review هي السلطة الأكاديمية الحالية.
- SpeechAnalysis/ASR الآلي advisory فقط.
- Production ASR غير معتمد بعد؛ `AUD-A03-008` external approval boundary مستقل.

## 8) الشارات والمكافآت

Reward Catalog هو owner لهوية الشارات الحالية. الحزمة الرسمية `BDG-01..BDG-06` مدمجة ومعتمدة. Student Home وAdmin Student Detail يعرضان canonical badge assets ولا يُنشأ hardcoded parallel map جديد.

الموافقة الكانونية:

`docs/ops/HIMMA_W4_OWNER_CLIENT_APPROVAL_2026-09-14.md`

## 9) الصور الدلالية الحالية

قرار W4 المعتمد يفرق بين:

- `lexical_stimulus`: تمثيل مباشر لمعنى الكلمة.
- `story_context`: صورة سياقية/مساندة.

الحالتان المقصودتان حاليًا في `L2-CORE-09`:

- R03 `سَمَك` → `VOC-05` → `lexical_stimulus`.
- R05 `نُور` → `VOC-15` → `lexical_stimulus`.

نقطة التوقف الحالية هي توحيد هذا القرار الأحدث مع اختبار Sep-08 القديم ثم إعادة exact-SHA Quality Gate. راجع `NEXT_CONVERSATION_PROMPT.md`.

## 10) البوابات والاختبارات

لا تعلن PASS/CLOSED من وثيقة فقط:

1. Fetch SHA الحالي.
2. شغّل/اعثر على `Himma CI — Quality Gate` لنفس SHA.
3. Backend/Frontend/Security يجب أن تنجح.
4. عندما تكون Integration مطلوبة يجب أن تنجح بما فيها Playwright.
5. أصلح root cause؛ لا تغير السلوك الصحيح لإرضاء stale test.
6. لا skip/xpass/weaken للحراس بدل تصحيح owner-of-truth.

CI الحالي يعمل بدون Docker ويستخدم native PostgreSQL/Redis وpinned MinIO في Integration.

## 11) قيود التنفيذ

- No Docker.
- No Deploy / Railway / Production أثناء A10.
- No final merge.
- No fake ASR.
- No Temporary Audio Skip.
- No history deletion.
- No Speech/Pronunciation Lab merge.
- `deployment/platform-sandbox` reference-only.
- No runtime repair overlays.
- No weakened tests.
- Stop when W6 becomes GREEN؛ A11 يأتي فقط بتكليف صريح لاحق.

## 12) قاعدة الاستئناف

إذا فتحت جلسة جديدة الآن، لا تبدأ بتقرير عام ولا تعيد ما أُنجز. بعد Fetch وقراءة ملفات الاستئناف، نفّذ أول gap غير مغلق من الحالة الحية. عند كتابة هذا الملف هو `AUD-MEDIA-002` بسبب Quality Gate #857 وليس بسبب غياب موافقة أكاديمية.
