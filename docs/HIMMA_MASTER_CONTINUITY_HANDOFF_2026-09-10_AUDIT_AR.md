# منصة هِمّة — MASTER CONTINUITY HANDOFF المحدث للمراجعة الشاملة

**التاريخ:** 2026-09-10  
**الغرض:** تسليم محادثة جديدة السياق التنفيذي الكامل للمشروع، بما في ذلك ما نُفذ قبل المراجعة الشاملة، وما اكتُشف أثناءها، ونقطة الاستكمال الدقيقة، دون إعادة التحليل من الصفر.  
**الحالة:** `AUDIT IN PROGRESS — NO MERGE — NO DEPLOY`  
**المستودع الرسمي:** `7eaur/himma-`  
**فرع الحقيقة التنفيذية قبل المراجعة:** `integration/canonical-content-2026-09-08`  
**HEAD التنفيذي قبل بدء المراجعة:** `7cb2192b0c31bc85dcf98a470023e9cc6f1598e0`  
**فرع المراجعة الحالي:** `audit/comprehensive-repository-review-2026-09-10`  
**HEAD فرع المراجعة قبل إنشاء هذا الملف:** `b870da62618b232b03908dcef5d48eb192a8626a`

> هذا الملف هو المرجع الأول لأي محادثة لاحقة. لا تبدأ من الصفر. اقرأ هذا الملف كاملًا أولًا، ثم الملفات المشار إليها بالترتيب، ثم افحص Git الحالي. إذا كان Git أحدث من الأرقام المذكورة هنا فـGit الحالي هو الحقيقة التنفيذية، مع المحافظة على قرارات المنتج والعقود الأكاديمية الأحدث وعدم الرجوع إلى سلوك قديم لمجرد أنه موجود في ملف تاريخي.

---

# 1) التكليف الحالي من المستخدم — لا تختصره إلى «إصلاح أخطاء»

المستخدم طلب **مراجعة شاملة ودقيقة للمستودع والمنصة قبل الإغلاقات النهائية**، ثم صيانة وتحسين وتوحيد الفروع والنشر. المطلوب ليس تنظيفًا سطحيًا ولا إزالة ملفات تحمل أسماء Repair/Recovery/Overlay لمجرد أسمائها.

القواعد الأساسية:

1. افحص المنصة كاملة: Backend، Frontend، DB، Seeds/Migrations، المحتوى، الصوت، التكيف، الشارات، الوسائط، التصميم، الهاتف، الأمن، الأداء، accessibility، الاختبارات، الفروع، وتجهيز النشر.
2. أي «ترقيع» أو طبقة تاريخية لا تحذف مباشرة. افهم: لماذا أضيفت؟ ما المشكلة التي كانت تحلها؟ هل ما زال شيء يعتمد عليها؟ ثم عالج السبب جذريًا في المالك الصحيح للحقيقة.
3. لا تضف Repair/Overlay Runtime جديدًا فوق طبقات قديمة.
4. لوحة الإدارة يجب أن تصبح موحدة بصريًا حول Design System واحد، بدون تكرار CSS/components غير مبرر.
5. صفحة تفاصيل الطالب في الإدارة يجب أن تكون مرنة فعليًا على الهاتف.
6. نظام الشارات/النجوم يجب أن يكون كاملًا من DB → logic → API → Student UI → Admin UI → assets → tests، وليس مجرد Events في الخلفية.
7. افحص الصور كلها: استخدم الأصول غير المستخدمة عندما يكون معناها مطابقًا بدل تكرار صورة مستخدمة، لكن لا تستبدل لمجرد تقليل التكرار إذا كان التطابق الدلالي غير صحيح.
8. بعد اكتمال التدقيق، راجع **جميع فروع المستودع** قبل الدمج. لا Merge أعمى.
9. **استبعد فرع نموذج الصوت الاصطناعي/التجريبي المؤقت من الدمج** حتى اعتماد مستقل.
10. بعد جمع الفجوات، نفذ الصيانة على مراحل، ثم اختبارات نهائية كاملة، ثم انشر النسخة النهائية على **Railway** بدل نسخة التطوير الحالية.
11. لا Docker.
12. لا Merge ولا Deploy قبل اكتمال المراجعة والصيانة والبوابات النهائية.

---

# 2) ما هي منصة هِمّة؟

هِمّة منصة تعليمية عربية موجهة لطلاب الصف الثالث ممن لديهم صعوبات في القراءة. المسار العام:

`دخول الطالب بكود → اختبار قبلي → تصحيح/تحليل → تصنيف مستوى → أنشطة أساسية → تقوية موجهة حسب الضعف → متابعة تكيفية → اختبار بعدي → تقارير المشرف`

المحتوى الأكاديمي الكانوني الحالي بعد اعتماد 2026-09-08:

- الاختبار القبلي: **30 سؤالًا**.
- الأنشطة الأساسية: **30 نشاطًا** = 10 لكل مستوى.
- التقوية: **35 نشاطًا**: L1=12، L2=11، L3=12.
- الاختبار البعدي: **30 سؤالًا**.
- الإجمالي: **125 عنصرًا**.
- الكتالوج يستهدف **44 مهارة**.

التصنيف الأساسي:

- أقل من 50% → المستوى الأول.
- 50% إلى أقل من 80% → المستوى الثاني.
- 80% إلى 100% → المستوى الثالث.

السياسة التكيفية الموجودة حاليًا والتي لا تُغير دون قرار مستقل:

- >=80 نجاح.
- 70–<80 Guided Retry.
- <70 Reinforcement.
- الترقية المبكرة في L1/L2 مبنية على أدلة V4، وليس شرط 10/10 دائمًا.
- المستوى الثالث يمر بجميع 10 Core.
- لا Auto-Demotion عشوائي.

---

# 3) ترتيب مصادر الحقيقة

عند التعارض:

1. **Git الحالي على الفرع التنفيذي الأحدث** هو الحقيقة الهندسية التنفيذية إذا كان أحدث من handoff قديم.
2. اعتماد المحتوى 2026-09-08 وعقوده الكانونية هو الحقيقة الأكاديمية الأحدث.
3. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-10_AUDIT_AR.md` — هذا الملف للاستمرارية الحالية.
4. `docs/maintenance/HIMMA_COMPREHENSIVE_REPOSITORY_AUDIT_2026-09-10_AR.md` — سجل المراجعة الشاملة.
5. تقارير A02/A04/A05/A06 الموجودة في `docs/maintenance/`.
6. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-09_AR.md` — التاريخ التفصيلي قبل المراجعة الحالية.
7. `docs/maintenance/CANONICAL_CONTENT_EXECUTION_CHECKPOINT_2026-09-09_AR.md`.
8. `docs/maintenance/CANONICAL_CONTENT_PORT_2026-09-08_AR.md`.
9. `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`.
10. `docs/specs/SOURCE_OF_TRUTH.md` + `docs/ops/STATUS.md` + `progress.json` + `DECISIONS.md` + `OPEN_ITEMS.md`.
11. الملفات المرجعية المرفقة بالمشروع، ومنها:
   - `05_توثيق_فكرة_المشروع_ومتطلبات_العميل_للمبرمج.docx`
   - `06_دليل_الهوية_البصرية_لمنصة_همة.pdf`
   - `00_حالة_المشروع_ومؤشر_الاعتماد_v1.2.pdf`
   - `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md`
   - `himma_comprehensive_audit_2026-08-16.docx`
   - `Himma_Characters_Badges_UI_Kit_v1.0.zip`
   - `Himma_Educational_Images_Kit_v1.0.zip`
   - `Himma_Web_Logo_Kit_v1.0.zip`
   - `himma-audio-production-skill.zip`
   - `Himma_Unified_Repository_v1.1_FINAL.zip`

لا تجعل ملفًا أقدم يعكس اعتمادًا أحدث.

---

# 4) قواعد العمل الهندسية الثابتة

- لا Docker.
- لا Merge/Deploy أثناء التدقيق.
- لا نقل أعمى من Sandbox أو فرع آخر.
- لا إصلاح محتوى بإضافة Seed/Repair جديد فوق القديم.
- Runtime الطالب يقرأ Structured DB Runtime، وليس parsing من source_text أثناء الطلب.
- ربط الوسائط Semantic وصريح، لا تخمين بالترتيب.
- لا حذف History لإجابات الطلاب أو AudioSubmissions القديمة بغرض التنظيف.
- أي إصلاح جذري يرافقه Regression Test.
- لا تدّع Green قبل تشغيل البوابة فعليًا.
- عند فحص ملف legacy: صنفه أولًا Runtime / production dependency / migration-history / test-only / standalone / dead-candidate.
- لا تنظف الفروع قبل compare كامل وفهم unique commits.

---

# 5) ما نُفذ قبل المراجعة الشاملة — الحالة الهندسية المهمة

## 5.1 المحتوى الكانوني

تم الانتقال من طبقات Seed/Projection تاريخية إلى مسار Canonical Compiler/Publisher/Release فعلي. الملفات الأساسية الحالية تشمل:

- `services/api/content_approval_contract_2026_09_08.py`
- `services/api/canonical_content_compiler.py`
- `services/api/canonical_content_publisher.py`
- `services/api/canonical_media_guard.py`
- `services/api/canonical_release.py`
- `services/api/content_runtime.py`
- `services/api/content_student_view.py`
- `services/api/seed_all.py`
- `services/api/verify_canonical_seed_idempotency.py`

إصلاحات مهمة نُفذت قبل المراجعة:

- توحيد محتوى 8 سبتمبر داخل canonical contract بدل Runtime overlay.
- إصلاح visible stimuli التي بقيت معتمدة من النسخ السابقة ولم يغيرها اعتماد 8 سبتمبر.
- إصلاح POST-Q14 ليصبح target الحالي **نخلة** وتسلسل الإجابة `ن، خ، ل، ة` داخل المصدر الكانوني.
- إضافة Media mapping الناقص لـ`L3-REIN-10`، بما فيها الأصول المولدة SEQ-007/008/009/010.
- توسيع aliases الدلالية **الصريحة** لصور Sequence، لا fuzzy guessing.
- إصلاح story media بحيث يكون playback في context boundary ولا يعاد بصورة خاطئة في كل جولة.
- تفضيل exact audio manifest semantics قبل relaxed matching.
- منع legacy single prompt من إفساد explicit audio-sequence items.
- عزل story labels عن semantic matching العادي.

الـcommit الكبير الذي جمع آخر reconciliation قبل المراجعة:

`05fec87fa57aaa855615d45e94564e60fd30ae3a` — `fix(content): reconcile canonical learner and media contracts`

ثم تم توثيق الحالة وتشغيل CI عبر:

`7cb2192b0c31bc85dcf98a470023e9cc6f1598e0` — `docs: record canonical reconciliation progress before full gates`

## 5.2 إصلاحات الصوت والتنقل والتكيف قبل المراجعة

العقد الحالي للصوت في مسار التعلم:

- `uploaded/pending` = evidence غير محسوم أكاديميًا، `is_correct=None`.
- Pending audio **لا يمنع التنقل العادي** داخل المستوى.
- Pending audio **لا يمنع same-level support/reinforcement/verification adaptation**.
- Pending audio يمنع فقط الحدود غير القابلة للعكس: **الترقية للمستوى التالي أو إكمال رحلة L3**.
- `rerecord_required` لا يسحب الطالب فورًا للخلف؛ يظهر كمهمة صريحة مؤجلة.
- الطالب يفتح مهمة إعادة التسجيل صراحة، ثم يسجل من جديد.
- إعادة التسجيل تنشئ **AudioSubmission جديدًا**؛ القديم يبقى محفوظًا تاريخيًا.
- `graded` هو الحالة التي تدخل evidence الأكاديمي.
- أحدث AudioSubmission هو مصدر الحالة النشطة، وليس تسجيلًا قديمًا مرفوضًا.

الملفات التي تنفذ ذلك:

- `audio_review_state.py`
- `activity_runtime.py`
- `learning_experience.py`
- `adaptation.py`
- `adaptation_runtime.py`
- `StudentRerecordTasks.tsx`
- `StudentActivityStateBoundary.tsx`

Commits مهمة:

- `17d70322...` — hold unresolved review only at level boundaries.
- `2f80d882...` — same-level adaptation continues with unresolved review.
- `8ac9ae3a...` — deferred rerecord navigation tests.
- `fa6de483...` — nonblocking pending + explicit rerecord flow tests.
- `e0acbf...` — evaluate only latest review submission.
- `ed0ec94e...` — adaptation boundary semantics tests.
- `57d87b28...` — E2E learning audio journey aligned with deferred review.

تمت إضافة `test_audio_adaptation_boundaries.py` لإثبات:

1. same-level support لا يعتمد على irreversible audio gate.
2. unresolved audio يمنع promotion ثم يسمح بها بعد resolution.
3. graded فقط يدخل adaptation evidence.

## 5.3 E2E الصوت

كان `vertical-slice.spec.ts` يتوقع Overlay قديم يحجب الطالب عند Pending Audio. تم تحديثه لأن هذا لم يعد العقد الصحيح:

- بعد رفع تسجيل القراءة يمكن الانتقال.
- Pending يظهر في progress لكنه لا يفرض modal blocking.
- عند boundary يمكن أن تظهر `awaiting-audio-review`.
- المشرف يراجع/يقيّم ثم تستمر الرحلة.

## 5.4 Frontend / React / Dependencies

تم إصلاح مشاكل React 19:

- `useAudioQueue.ts`: لا ref writes أثناء render؛ المزامنة داخل effects؛ return memoized.
- صفحات session/activity تستخدم `stopPlayback` ثابتًا.
- Admin content preview أزيل منه sync setState-in-effect وأصبح async fetch flow نظيفًا.
- `StudentActivityStateBoundary` مركب داخل activity layout.
- CSS مفقود تمت إضافته.

تم إصلاح dependency audit:

- Next أصبح `^16.3.4`.
- `eslint-config-next` `^16.3.4`.
- sharp محدث إلى إصدار آمن >=0.35.4.
- js-yaml transitive issue أُغلق عبر lockfile regeneration.
- npm audit كان نظيفًا في التشغيل السابق.

## 5.5 CI بدون Docker

تم إزالة اعتماد Docker من بوابات المشروع الرئيسية التي كانت ضمن المسار الحالي:

- `.github/workflows/ci.yml`
- `.github/workflows/m09-release-readiness.yml`

والبدائل:

- PostgreSQL native.
- Redis native.
- MinIO binary pinned/checksummed عند الحاجة.

لا تعيد Docker تحت أي ذريعة إلا إذا غيّر المستخدم القرار صراحة.

---

# 6) التسلسل التاريخي للاختبارات قبل بدء المراجعة

## تشغيل Backend الأقدم بعد تغييرات الصوت

تم جمع **825 tests** وكانت النتيجة:

- 812 passed
- 13 failed

هذه الـ13 لم تُعامل كـ«نعدل الاختبارات وخلاص»؛ تم تحليلها، وتبين خليط من stale expectations وفجوات حقيقية في المصدر الكانوني. تم إصلاح الجذور المذكورة أعلاه (visible stimuli، L3 media، POST-Q14، story/sequence contracts) وتحديث اختبارات قديمة عندما كان العقد نفسه قد تغير رسميًا.

## التشغيل الفعلي على HEAD `7cb2192...`

GitHub Actions run:

`34419490966`

النتيجة:

- Security: **PASS**.
- Frontend: **PASS** — install/typecheck/ESLint/unit/build.
- PostgreSQL native: **PASS**.
- canonical validation: **PASS**.
- Alembic upgrade → downgrade base → upgrade: **PASS**.
- `alembic check`: **PASS**.
- canonical seed twice/idempotency: **PASS**.
- Backend pytest: **823 passed / 2 failed**.
- Integration/E2E: **لم يبدأ** لأن Backend job فشل.

الفشلان الحاليان عند بدء المراجعة:

### AUD-BE-003
`learning-experience` قد يرجع `pending_audio_reviews=0` رغم وجود جولة صوت Pending إذا كانت محاولة العنصر نفسه تحتوي جولة أخرى قابلة للتنفيذ. المشكلة في خلط navigation selection مع session-level review summary. الحل الجذري يجب أن يفصل «ما هي الخطوة التالية؟» عن «كم evidence صوتي غير محسوم في الجلسة؟».

### AUD-BE-004
اختبار Recovery لـPRE-Q05 ما زال يستخدم `seed.run_seed()` القديم (عالم 105) بدل canonical publication الحالي 125، لذلك يرى 3 صور بدل العقد المعتمد 4. هذه علامة legacy test/seed path، وليست نقصًا في canonical release الحالي.

لا تصلح هذين كـassert patch فقط؛ عالج ownership/path الصحيح أثناء موجة الصيانة.

---

# 7) الصوت — ما هو موجود فعليًا وما هو غير مكتمل

## 7.1 الأصول الصوتية

حزمة `assets/audio/HIMMA_AUDIO_V1/` لديها manifest معروف بـ54 Asset، ولكل Asset WAV وMP3 في الحزمة المكتملة (108 ملفًا).

الأصول الواقعية التي تم التحقق منها سابقًا تشمل:

- `SYL-13 = سَا`
- `SYL-15 = مَ` ويحل محل LET-01 في الموضع المعتمد.
- `WRD-29 = موز`
- `INS-01 = قصة ليان`
- `INS-02 = قصة نادر`

وفي payload كان لهذه الخمسة WAV+MP3 = 10 ملفات فعلية.

## 7.2 التحليل الصوتي Reference-Guided

النية المعمارية المعتمدة:

`ASR → alignment مع النص المرجعي المعروف → Correct/Deletion/Insertion/Substitution → مراجعة بشرية/معايرة → evidence أكاديمي`

الملفات الحالية:

- `speech_provider.py`
- `speech_pipeline.py`
- `speech_alignment.py`
- `speech_worker.py`
- `speech_analysis.py`
- `db/speech_models.py`

ما تم إثباته أثناء المراجعة:

- Queue DB-backed دائم موجود.
- Worker async موجود.
- retry/backoff/dead-letter موجود.
- SpeechAnalysis immutable per submission موجود.
- alignment كلمة-بكلمة C/D/I/S موجود.
- provider execution خارج HTTP request path.
- provider absence لا ينتج fake score.

لكن **الإنتاج غير مكتمل**:

- `build_provider()` لا يملك Production ASR Adapter معتمدًا حتى الآن؛ يرجع `UnconfiguredSpeechProvider` أو يرفع `ProviderNotConfigured`.
- Arabic lexical alignment يتجاهل الحركات لأغراض lexical matching؛ phoneme/haraka scoring لم يُعتمد/يُعاير بعد.
- machine result يبقى `review_required` ما لم يوجد threshold + calibration version.
- manual reviewer flow في `review.py` ما زال منفصلًا عن machine-analysis lifecycle ويحتاج توحيد contract بدون تحويل machine confidence إلى academic truth مباشرة.
- بعض AuditLog/admin copy ما زال يقول إن محاولة الطالب «reopened» عند rerecord، بينما العقد الحالي هو deferred explicit rerecord task.

**هذه هي نقطة الاستكمال الأقرب: أكمل A03 من هنا.**

---

# 8) المراجعة الشاملة الحالية — الخطة A00 إلى A11

## A00 — Baseline / Governance / CI
الحالة: **مفحوصة مبدئيًا**.

تم تثبيت baseline، توثيق CI الفعلي، ومنع الخلط بين Runner failure وcode failure.

## A01 — Backend / Runtime / Routes
الحالة: **بدأت ومفهومة جزئيًا**.

فجوة رئيسية:

- `activities.py`
- `activities_v4.py`
- `activity_runtime.py`

Router ownership ليس مكررًا مباشرة، لكن service ownership موزع تاريخيًا ويحتاج تحليلًا قبل consolidation.

## A02 — DB / Seeds / Migrations / Canonical Content
الحالة: **جرد قوي تم، الإصلاح لم يبدأ**.

تم بناء AST import graph بدل grep فقط.

حقائق مهمة:

- `seed_all.py` = **ACTIVE_CANONICAL_ENTRYPOINT**.
- `content_projection_digest.py` له production imports فعلية.
- `verify_canonical_seed_idempotency.py` مستخدم في CI/M09.
- `seed.py` القديم ما زالت اختبارات كثيرة تعتمد عليه.
- بعض الملفات لا تملك direct import/workflow refs، لكنها لا تحذف قبل فحص CLI/history/migration semantics.

مرشحات تاريخية يجب تصنيفها يدويًا:

- `seed_db_runtime_contract.py`
- `seed_l1_auditory_story_replacement.py`
- `seed_learning_posttest_experience_2026_09_01.py`
- `seed_learning_posttest_projection_runtime.py`
- `seed_pretest_experience_2026_09_01.py`
- `seed_reinforcement_additions.py`
- `seed_reinforcement_additions_v2.py`
- `seed_student_choice_corrections.py`
- `seed_student_experience_v2.py`

**فجوة إضافية مثبتة:** `run_dev.py` يستدعي `seed_all` ثم ينتظر مفتاحًا تاريخيًا `student_experience_v2_items` لم يعد العقد الحالي يعيده؛ تشغيل dev قد ينتهي KeyError بعد seed ناجح. لا patch للkey؛ عالج dev contract مع canonical result.

## A03 — Audio / Speech Analysis / Adaptation
الحالة: **IN PROGRESS — هنا توقفت المراجعة العميقة**.

المطلوب التالي:

1. trace upload → AudioSubmission → queue → worker → SpeechAnalysis → human review → latest submission semantics.
2. تحديد contract واضح بين machine `review_required/auto_accepted` وبين `AudioSubmission.status` الأكاديمي.
3. منع أي auto grade قبل calibration واعتماد.
4. مراجعة concurrency/idempotency/retry/reprocessing.
5. مراجعة privacy/storage/retention/PII وRailway deployment implications.
6. فحص supervisor UI وstudent rerecord copy مع العقد الجديد.
7. فحص أن latest submission فقط يدخل active evidence.
8. فحص promotion/L3 completion gates مع machine-analysis statuses.

## A04 — Frontend / Admin UI / Mobile
الحالة: **هيكل Admin فُهم، الفجوات موثقة، لم تبدأ إعادة البناء**.

جدول الحالة الحالي:

- `/admin` → AdminUI — جيد مبدئيًا.
- `/admin/students` → AdminUI + desktop table/mobile cards — جيد مبدئيًا.
- `/admin/students/new` → AdminUI.
- `/admin/reports` → AdminUI.
- `/admin/skill-reports` → AdminUI.
- `/admin/audio-review` → AdminUI shell، يحتاج mobile E2E + copy contract.
- `/admin/content-preview` → AdminUI shell، التخصيص الداخلي مبرر.
- `/admin/settings` → **Design System ثاني فعليًا**: CSS/forms/panels/buttons محلية — GAP.
- `/admin/account` → legacy/duplicate candidate، غير موجود في sidebar، لا يحذف قبل dependency scan.
- `/admin/students/[id]` → **أولوية P1**؛ CSS كبير ومحلي ويعيد بناء header/cards/stats/tabs/forms/actions/modal بدل AdminUI.
- `/admin/login` → auth مستقل، يحتاج tokens/accessibility/mobile فقط، لا يفرض dashboard shell.

### Student Details mobile acceptance

يجب اختبار فعليًا:

- 320px
- 360px
- 390px
- 430px
- 768px
- desktop

مع:

- no horizontal overflow
- tabs usable باللمس
- summary cards لا تكسر الرمز/الأرقام
- actions stack واضح
- edit forms قابلة للكتابة
- focus/keyboard/error states
- RTL سليم

الحل المخطط: إعادة تكوين الصفحة من AdminUI primitives؛ لا CSS system جديد.

## A05 — Rewards / Badges
الحالة: **Backend موجود، visual/contract gaps مثبتة، E2E مفتوح**.

الموجود:

- Model `RewardEvent` دائم.
- جدول `reward_events`.
- unique `(student_id, reward_key)`.
- reward_type stars/badge.
- `adaptation.ensure_rewards()`.
- API طالب `/rewards`.
- API مشرف `/researcher/students/{student_id}/rewards`.
- unresolved audio/media-gap لا يحصل على reward evidence.

الفجوات:

### AUD-BADGE-001
Student UI يجلب rewards لكنه يعرض **total stars فقط**؛ لا يعرض badges بصريًا.

### AUD-BADGE-002
Admin Student Details يعرض badge label كchip نصي فقط.

### AUD-BADGE-003
حزمة `Himma_Characters_Badges_UI_Kit_v1.0` غير مدمجة حاليًا داخل `apps/web/public` كـrewards/levels assets.

### AUD-BADGE-004
عدم تطابق L3:

- Backend: `قارئ متميز`
- الحزمة: BDG-06 `نجم الفهم`

يحتاج Reward Catalog واحد بدل حقائق منفصلة.

### AUD-BADGE-005 — فجوة منطقية مهمة
Journey يعتبر L1/L2 مكتملًا عبر early promotion بعد 6–9 Core إذا تحققت الأدلة، لكن `ensure_rewards()` يمنح badge فقط عند `_completed_core_count >= 10`.

إذًا طالب قد يرى المستوى completed ولا يحصل على شارة المستوى.

الحل الجذري المرشح: **مصدر واحد لتعريف level completion** تستخدمه Journey + Rewards + posttest eligibility عند الحاجة، بعد تثبيت القرار في ADR/Source of Truth.

### AUD-BADGE-006
لا يوجد بعد E2E مثبت يغلق:

`level complete/promotion → badge event once → correct catalog asset/label → Student visible → Admin visible → persistence after refresh/restart`

## A06 — Images / Media
الحالة: **جرد Canonical image usage اكتمل مبدئيًا**.

نتيجة التقرير:

- Canonical items: **125**.
- Known image IDs: **71**.
- referenced by canonical release: **48**.
- original approved kit IDs unused: **23**.
- referenced IDs missing from known maps: **0**.
- assets used بأكثر من semantic label غير فارغ: **18** تحتاج manual review.

الـ23 صورة الأصلية غير المستخدمة:

`VOC-11` كوب ماء، `VOC-12` بطة، `VOC-13` سيارة، `VOC-14` نجم، `VOC-17` حقيبة، `VOC-18` مدرسة، `VOC-19` معلم، `VOC-20` عصفور، `VOC-21` حديقة، `VOC-22` مكتبة، `VOC-23` شاطئ، `VOC-24` بحر، `VOC-25` رمل، `VOC-26` أصداف، `VOC-27` سلة طعام، `VOC-28` زهرة، `VOC-29` بذرة، `VOC-30` أوراق شجر، `VOC-31` سحاب، `VOC-32` وادٍ، `VOC-33` أسرة، `VOC-34` طفل، `VOC-35` طفلة.

قاعدة الاستبدال:

- لا تستبدل صورة مكررة بمجرد وجود unused image.
- قارن semantic_text والسؤال/الخيار والسياق بصريًا.
- إذا الأصل غير المستخدم أدق دلاليًا فاستعمله في المصدر الكانوني.
- إذا الصورة الحالية أدق، اتركها ولو كانت مستخدمة أكثر من مرة.

مثال تمت مراجعته: `VOC-23` شاطئ غير مستخدم، بينما `STY-05` مشهد قصة شاطئ يستخدم في سياق آخر؛ لا يُستبدل أحدهما بالآخر تلقائيًا لأن وظيفة story scene تختلف عن vocabulary image.

### Public/static inventory

- tracked files: 1075 عند الجرد.
- `apps/web/public`: 28 files.
- zero direct references: 17.
- exact duplicate public SHA groups: 5.
- `assets/education`: 208 files.
- exact duplicate education SHA groups: 0.

الخمسة duplicates المؤكدة كلها نسخ Boy character:

- `characters/boy-encourage.png` == `characters/boy/encourage.png`
- `boy-explain.png` == `boy/explain.png`
- `boy-success.png` == `boy/success.png`
- `boy-try-again.png` == `boy/try-again.png`
- `boy-welcome.png` == `boy/welcome.png`

هذه **مرشحات تنظيف فقط** حتى يكتمل dynamic reference scan.

## A07 — Security / Performance / Accessibility / Observability
الحالة: **لم تكتمل**.

يجب فحص:

- auth/roles/IDOR
- upload/media authorization
- rate limiting
- secret/env handling
- dependency audit/gitleaks/guards
- N+1/query patterns
- payload/bundle/images/cache
- WCAG keyboard/focus/contrast/reduced motion
- readiness/health/logging/operational diagnostics
- speech worker observability
- Railway production diagnostics

## A08 — Full Tests / Full Journey / E2E
الحالة: **لم تكتمل**.

لا تعتمد المنصة قبل تشغيل فعلي على النسخة بعد الصيانة يشمل:

- backend
- frontend
- security
- migrations roundtrip
- drift
- seed twice
- canonical media
- audio
- integration
- E2E
- mobile flows
- pretest → placement → learning → reinforcement → promotion → L3 → posttest → reports
- rewards/badges
- rerecord lifecycle

## A09 — Branch Review / Unification
الحالة: **لم تبدأ المقارنة الكاملة لكل الفروع**.

المطلوب بعد A00–A08:

صنف كل فرع:

- `already-contained`
- `unique-relevant`
- `obsolete`
- `experimental`
- `archive-candidate`

استخدم compare commits، لا أسماء الفروع وحدها.

**لا تدمج فرع نموذج الصوت الاصطناعي المؤقت.**

لا تحذف أي فرع قبل معرفة هل يحتوي unique relevant commits.

بعد الاختيار، ابن final integration candidate نظيفًا ثم أعد البوابات كاملة.

## A10 — Maintenance / Improvement Waves
لا تبدأ حتى ينضج Master Gap Register.

ترتيب مرشح:

1. P0/P1 correctness/data/runtime gaps.
2. canonical/seed ownership cleanup.
3. audio/speech/review contract.
4. adaptation/completion/rewards semantics.
5. Admin design system + Student Details mobile.
6. badge catalog/assets/UI.
7. media semantic cleanup + unused assets.
8. accessibility/performance/security/observability.
9. dead/duplicate code/assets cleanup بعد dependency proof.
10. branch unification.

## A11 — Final Release Gate + Railway
فقط بعد الصيانة والدمج الداخلي والاختبارات:

- final full green gates.
- backup/rollback plan.
- production env contract.
- PostgreSQL service.
- storage strategy للأوديو/الميديا.
- worker process إن اعتمد ASR.
- migrations.
- canonical publication/seed strategy.
- readiness/smoke.
- post-deploy E2E.
- بعدها فقط استبدال نسخة التطوير الحالية بالنسخة النهائية على Railway.

---

# 9) Design System / Admin — لا تفقد هذه النية

`AdminUI` موجود ويجب البناء فوقه، لا اختراع نظام ثالث.

المكونات/المفاهيم المشتركة التي يجب تفضيلها:

- AdminPage
- AdminPageHeader
- AdminPanel
- AdminStatGrid
- AdminAction
- shared form/table/mobile-card patterns

إذا احتاج Student Details pattern غير موجود فعلًا، أنشئ shared primitive عام فقط إذا سيعاد استخدامه أو يمثل pattern حقيقي، وليس component خاصًا يكرر CSS.

Settings يجب تقليص CSS المحلي إلى ما لا يغطيه shared system.

`/admin/account` لا يحذف قبل route/link/test scan ثم redirect/migration decision إن لزم.

---

# 10) Rewards — التصميم الجذري المرشح

لا تضف if/else لكل Badge في Student page.

المسار الأفضل:

**Reward Catalog canonical واحد** يربط:

`reward_key → reward/catalog id → type → level → label → asset_id/url`

أصول الحزمة:

- BDG-01 نجمة واحدة
- BDG-02 نجمتان
- BDG-03 ثلاث نجوم
- BDG-04 مستكشف الحروف
- BDG-05 بطل الكلمات
- BDG-06 نجم الفهم

ويجب أن يخرج API display contract ثابتًا للطالب والإدارة.

لا تعِد حساب rewards التاريخية بطريقة تكسر `RewardEvent` السابق دون migration صريحة.

---

# 11) نقاط لا يجوز إعادة فتحها بلا سبب

هذه القرارات حُسمت سابقًا ولا ينبغي لمحادثة جديدة أن تعيد الجدال فيها من الصفر:

- لا Docker.
- المحتوى الكانوني 125 هو الخط الحالي، لا عالم 105 القديم.
- Pending audio neutral أكاديميًا.
- Pending audio لا يحجب same-level navigation/adaptation.
- promotion/L3 completion فقط هي الحدود التي تنتظر unresolved audio.
- rerecord deferred explicit task ويحفظ التاريخ.
- latest AudioSubmission هو active evidence.
- Runtime الطالب structured DB.
- semantic media mapping صريح.
- لا Merge/Deploy قبل البوابات.
- Railway هو هدف النشر بعد الإصلاح، لا أثناء التدقيق.

---

# 12) ملفات التوثيق التي يجب أن تقرأها المحادثة الجديدة بالترتيب

**اقرأ كاملًا، لا تكتفِ بالبحث عن كلمات:**

1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-10_AUDIT_AR.md` — هذا الملف.
2. `docs/maintenance/HIMMA_COMPREHENSIVE_REPOSITORY_AUDIT_2026-09-10_AR.md`.
3. `docs/maintenance/HIMMA_A02_A06_STATIC_INVENTORY_2026-09-10.md`.
4. `docs/maintenance/HIMMA_A02_PYTHON_IMPORT_GRAPH_2026-09-10.md`.
5. `docs/maintenance/HIMMA_A04_A05_ADMIN_BADGES_AUDIT_2026-09-10_AR.md`.
6. `docs/maintenance/HIMMA_A06_CANONICAL_IMAGE_USAGE_2026-09-10_AR.md`.
7. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-09_AR.md`.
8. `docs/maintenance/CANONICAL_CONTENT_EXECUTION_UPDATE_2026-09-10_AR.md`.
9. `docs/maintenance/CANONICAL_CONTENT_EXECUTION_CHECKPOINT_2026-09-09_AR.md`.
10. `docs/maintenance/CANONICAL_CONTENT_PORT_2026-09-08_AR.md`.
11. `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`.
12. `docs/specs/SOURCE_OF_TRUTH.md`.
13. `docs/ops/STATUS.md`.
14. `docs/ops/progress.json`.
15. `docs/ops/DECISIONS.md`.
16. `docs/ops/OPEN_ITEMS.md`.
17. `AGENTS.md`.
18. `.agents/rules/00-himma-core.md`.
19. `.agents/rules/10-delivery-protocol.md`.
20. `.agents/rules/20-security-quality.md`.

بعدها اقرأ الكود الفعلي للمجال الذي ستكمل منه، ولا تعتمد على الوثائق وحدها إذا كان HEAD أحدث.

---

# 13) نقطة الاستكمال الدقيقة للمحادثة القادمة

**لا تبدأ بتحسين Student Details مباشرة، ولا تبدأ دمج الفروع، ولا تبدأ Railway الآن.**

ابدأ من:

### المرحلة الحالية: A03 — Audio / Speech / Review / Adaptation deep audit

استكمل من ملفات:

- `services/api/speech_provider.py`
- `speech_pipeline.py`
- `speech_alignment.py`
- `speech_worker.py`
- `speech_analysis.py`
- `db/speech_models.py`
- `recordings.py`
- `review.py`
- `audio_review_state.py`
- `activity_runtime.py`
- `adaptation.py`
- `adaptation_runtime.py`
- frontend audio-review/rerecord components

ثم وثق فجوات A03 في سجل المراجعة.

بعد A03:

1. أكمل A04 بالمصفوفة التفصيلية + mobile behavior، بدون تنفيذ إصلاح واسع بعد.
2. أكمل A05 end-to-end evidence للشارات.
3. أكمل A06 manual semantic review للأصول المشكوك فيها + public dynamic usage.
4. نفذ A07.
5. نفذ A08 baseline/full journey evidence حسب ما يسمح به الكود الحالي.
6. نفذ A09 branch-by-branch comparison.
7. اجمع **Master Gap Register** موحدًا P0/P1/P2/P3 مع dependencies/root cause/owner/fix wave/test gate.
8. عندها فقط ابدأ A10 الصيانة قسمًا قسمًا.
9. بعد final green + branch unification انتقل A11 وRailway.

---

# 14) شكل Master Gap Register المطلوب لاحقًا

لكل فجوة سجل:

- ID
- المجال
- Severity
- Status
- Evidence/file/route/test
- Symptom
- Root cause
- Current workaround/legacy layer إن وجد
- Dependencies
- Correct owner of truth
- Root fix
- Migration/history risk
- Tests required
- Release risk
- Wave/order

لا تجعل «اسم الملف قديم» هو root cause.

---

# 15) التوثيق الواجب تحديثه مع التقدم

بعد كل مرحلة تدقيق أو موجة إصلاح، حدّث:

- `docs/maintenance/HIMMA_COMPREHENSIVE_REPOSITORY_AUDIT_2026-09-10_AR.md`
- تقرير المرحلة المتخصصة إذا وجد.
- هذا handoff إذا تغيرت نقطة الاستكمال بشكل كبير أو قبل تسليم محادثة جديدة.

وبعد بدء الإصلاحات التنفيذية حدث أيضًا:

- `docs/ops/STATUS.md`
- `docs/ops/progress.json`
- `docs/ops/DECISIONS.md`
- `docs/ops/OPEN_ITEMS.md`

ADR مهم ما زال مطلوبًا عند تثبيت سياسة الصوت النهائية: supersede التعريف القديم بحيث يوضح pending/graded/rerecord/latest-submission/boundary semantics.

ADR آخر محتمل عند تثبيت rewards: تعريف موحد لـlevel completion + reward catalog.

---

# 16) حالة الدمج والنشر الآن

حتى لحظة إنشاء هذا handoff:

- **لا يوجد Merge نهائي.**
- **لا يوجد Deploy نهائي.**
- Railway لم يُستبدل بالنسخة النهائية بعد.
- فرع المراجعة مخصص للفهم والتوثيق، وليس لإطلاق Production.
- branch review الشامل ما زال لاحقًا.
- فرع نموذج الصوت الاصطناعي المؤقت يجب أن يبقى خارج الدمج.

---

# 17) مبدأ القرار في كل خطوة

قبل أي تعديل اسأل:

1. ما السلوك الصحيح المطلوب أكاديميًا/منتجيًا؟
2. من يملك هذه الحقيقة حاليًا؟
3. هل الملف الذي أمامي مالك حقيقي أم compatibility/history layer؟
4. لماذا ظهرت الطبقة القديمة؟
5. من يعتمد عليها الآن؟
6. كيف أنقل السلوك الصحيح إلى المالك النهائي دون حذف التاريخ؟
7. ما Regression Test الذي يثبت أن الحل جذري؟
8. هل هذا التعديل يؤثر على المحتوى/الصوت/المكافآت/التقارير/الهجرة؟
9. هل بوابات النشر ستكتشف regression أم نحتاج Gate جديد؟

إذا لم تستطع الإجابة، لا تحذف ولا تدمج.

---

# 18) ملخص تنفيذي للمحادثة الجديدة

أنت لا تستلم مشروعًا غير مفهوم. المشروع وصل إلى canonical content حديث، وتحسينات صوت/تنقل/تكيّف مهمة، وCI قوي بدون Docker، لكن قبل الإغلاق طلب المستخدم تشريحًا شاملًا لكل الترقيعات والفجوات والتصميم والشارات والوسائط والفروع.

المراجعة بدأت فعلًا، ووثقت:

- Baseline/CI.
- legacy Python/import/seed inventory.
- Admin UI/Student Details/Settings/Account gaps.
- rewards/badges persistence والـUI/semantic gaps.
- canonical image usage و23 أصلًا غير مستخدم وduplicate public assets.
- بداية deep audit للصوت، التي أثبتت وجود pipeline حقيقي لكن بدون Production provider معتمد حتى الآن.

**نقطة الاستكمال الذكية: أكمل A03 ولا تعد التحليل من البداية.**

ثم أكمل A04–A09، اجمع الفجوات، ثم نفذ A10، وبعدها Final Gates وRailway في A11.
