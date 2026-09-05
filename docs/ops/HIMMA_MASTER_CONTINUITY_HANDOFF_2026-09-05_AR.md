# HIMMA MASTER CONTINUITY HANDOFF — 2026-09-05

> هذا الملف هو مرجع تسليم واستمرارية لمحادثة جديدة حتى تتابع تنفيذ منصة **هِمّة | HIMMA** من النقطة الحالية بدون إعادة اكتشاف المشروع من الصفر وبدون فقد القرارات الأكاديمية أو التقنية أو أدلة التنفيذ الحديثة.

---

## 0) قاعدة القراءة لهذا الملف

هذا الملف يوثق **الحالة التنفيذية الفعلية حتى آخر SHA تنفيذي تحقق منه**:

`07e83ba57244410f160a727b3c50001fbd7451a1`

الفرع الرسمي للعمل:

`recovery/ui-media-admin-overhaul`

المستودع الرسمي الوحيد:

`7eaur/himma-`

مهم: ملف `docs/ops/STATUS.md` الحالي ما زال يحتوي في رأسه على صياغة أقدم تعتبر Phase D هي المرحلة النشطة، و`docs/ops/progress.json` أقدم من آخر تنفيذ. لذلك عند استلام محادثة جديدة يجب اعتبار **هذا Handoff + GitHub HEAD + نتائج Actions الحديثة** المرجع الأحدث للحالة، ثم تحديث `STATUS.md` و`progress.json` أثناء الإغلاق القادم.

قبل أي كتابة جديدة على الفرع: **أعد جلب HEAD وتأكد أنه لم يتحرك**.

---

# 1) ما هي منصة هِمّة؟

منصة تعليمية عربية موجهة لطلاب الصف الثالث الذين لديهم صعوبات في القراءة.

المسار الأساسي للطالب:

`دخول بكود -> اختبار قبلي -> تحليل/مراجعة القراءة -> تصنيف مستوى -> أنشطة المستوى -> تقوية موجهة -> متابعة تكيفية -> اختبار بعدي -> تقارير المشرف`

المحتوى الأكاديمي الأساسي المعتمد:

- 30 سؤال اختبار قبلي.
- 30 سؤال اختبار بعدي.
- 3 مستويات.
- لكل مستوى 10 أنشطة أساسية + 5 أنشطة تقوية في المصدر الأكاديمي الأصلي.
- المصدر الأكاديمي الأصلي = 105 عناصر.
- Runtime الحالي = 125 عنصرًا.
- Reinforcement runtime total = 35.
- Skills = 44.

التصنيف الأساسي بعد الاختبار القبلي:

- أقل من 50% -> المستوى الأول.
- 50% إلى أقل من 80% -> المستوى الثاني.
- 80% إلى 100% -> المستوى الثالث.

هذا التصنيف يحدد **مستوى البداية فقط**، ثم تطبق قواعد الأدلة/التكيف والترقية المعتمدة.

---

# 2) القواعد الأكاديمية والتكيفية غير القابلة للكسر

## L1 / L2 — الترقية المبكرة

لا ترقية إلا بعد تحقق جميع الشروط التالية:

- تنفيذ 6 Core على الأقل.
- Mastery >= 85%.
- Critical floor >= 70%.
- تغطية المهارات الحرجة المطلوبة كاملة.
- لا يوجد Reinforcement blocker غير محلول.
- لا يوجد Audio Review blocker غير محلول.
- الترقية مستوى واحد فقط في المرة.
- لا يوجد Auto-demotion.

## L3

المستوى الثالث يحتاج الأدلة الكاملة المطلوبة قبل اكتمال الرحلة/فتح الاختبار البعدي، ويشمل اكتمال الأنشطة والتغطية وعدم وجود blockers حسب العقد الأكاديمي الحالي.

## Reinforcement

- تقوية مستهدفة حسب الضعف فقط.
- ممنوع Random fallback.
- ممنوع Cross-level fallback غير أكاديمي.

## Reports

التقارير **Read Models فقط**.

ممنوع على أي endpoint أو read في التقارير أن:

- ينشئ Mastery.
- يكمل Activity.
- يغير Student level.
- ينشئ Academic evidence.
- يحدد Official attempt.

آخر HEAD يحتوي Regression test جديدًا يثبت أن قراءة التقارير لا تعدل الحالة الأكاديمية.

---

# 3) القرارات المعتمدة للصوت

## Fixed approved audio

الحزمة الثابتة المعتمدة مغلقة من ناحية Binary/manifest integrity:

- Approved assets = 54.
- WAV = 54.
- MP3 = 54.
- Missing required static audio = 0.

الربط المصحح المعتمد:

- `LET-01` = **مَ**، مع الاحتفاظ بالـStable ID القديم، والبايتات المعتمدة مصدرها `SYL-15`.
- `SYL-13` = **سَا**.
- `WRD-29` = **موز**.
- `INS-01` = قصة ليان في المزرعة.
- `INS-02` = قصة نادر في الشاطئ.

المرجع التشغيلي:

`docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`

والـmanifest:

`assets/audio/HIMMA_AUDIO_V1/manifest.csv`

التحقق بالـSHA-256 يتم من خلال validator الموجود في مسار المحتوى، ويدخل ضمن Quality Gate.

لا تدّع جودة إدراكية/سمعية perceptual quality لمجرد أن checksums صحيحة؛ هذا يحتاج استماعًا/تقييمًا صوتيًا منفصلًا.

---

# 4) عقد تسجيل الطالب ومراجعة المشرف

القرار الحالي والفعلي:

`record -> persist/upload -> supervisor review -> graded OR rerecord_required -> continue`

حالة التسجيل بعد الرفع وقبل قرار المشرف:

`AudioSubmission.status = "uploaded"`

هذه الحالة تعني **بانتظار المراجعة** ولا تعني:

- نجاح.
- Correct answer.
- Activity completion.
- Mastery evidence.

المشرف هو صاحب السلطة الحالية لقبول/رفض التسجيل.

لا يوجد Fake AI score.

إذا قرر المشرف:

- `graded` -> قد تصبح الجولة قابلة للاكتمال وفق نتيجة المراجعة.
- `rerecord_required` -> تعاد نفس جولة القراءة ويطلب تسجيل جديد.

لا تحذف تاريخ المحاولات أو التسجيلات أو المراجعات بهدف تسهيل المنطق.

---

# 5) قرار نموذج تحليل القراءة المستقبلي

إذا تم لاحقًا تنفيذ تحليل صوت آلي، فالقرار المعماري المعتمد هو:

**Reference-Guided Arabic Reading Analysis**

يتكون من:

- ASR.
- Alignment مع النص المرجعي المعروف مسبقًا.
- تحليل Correct / Deletion / Insertion / Substitution.
- Phonemic helper evidence.

لكن هذا **Future production gate** وليس مطلوبًا لإغلاق الصيانة الحالية.

لا تنفذ Provider أو Automatic scoring أو Calibration الآن إلا إذا طلب المستخدم ذلك صراحة كمرحلة منفصلة.

---

# 6) المعمارية المستهدفة للمحتوى

المسار الصحيح:

`Approved Academic Source -> Versioned Content Source/Projection -> PostgreSQL Runtime -> Structured APIs -> Deterministic Student Renderer`

الهدف هو منع المعمارية القديمة من النوع:

`raw prompt -> regex/string parsing -> DOM inference/runtime patches`

القواعد:

- Stable IDs محفوظة.
- لا تستنتج Correct answer من نص Prompt.
- لا تستنتج نوع interaction من نص حر إذا كانت البيانات المنظمة موجودة.
- لا تنقل Prompt parsing من backend إلى frontend كحل التفافي.
- Seeds يجب أن تكون version-aware + idempotent + non-destructive.

---

# 7) قيود التنفيذ وGitHub

يجب الالتزام بما يلي في كل محادثة جديدة:

- لا Docker محليًا.
- لا Force push.
- لا `reset --hard`.
- لا `git clean`.
- لا حذف branch/history.
- لا تعديل الفروع الأساسية المقبولة مباشرة.
- لا حذف/تصفير البيانات الأكاديمية:
  - students
  - sessions
  - attempts
  - mastery
  - recordings
  - reviews
  - audits
  - retakes
  - notifications
- قبل كل write: أعد جلب branch HEAD.
- لا تعتبر أي مرحلة PASS بسبب SHA قديم.
- PASS = نفس SHA النهائي له Gate مكتمل وناجح.

المستودع المرجعي التاريخي:

`7eaur/himma-deployment-sandbox`

يستخدم للمرجعية فقط، وليس مكان التنفيذ الرسمي.

---

# 8) الملفات التي يجب قراءتها في بداية أي محادثة جديدة

اقرأ قبل أي تنفيذ:

- `AGENTS.md`
- `.agents/rules/00-himma-core.md`
- `.agents/rules/10-delivery-protocol.md`
- `.agents/rules/20-security-quality.md`
- `docs/specs/SOURCE_OF_TRUTH.md`
- `docs/specs/ACCEPTANCE_MATRIX.md`
- `docs/ops/STATUS.md`
- `docs/ops/progress.json`
- `docs/ops/DECISIONS.md`
- `docs/ops/OPEN_ITEMS.md`
- `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`
- **هذا الملف** `docs/ops/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-05_AR.md`

ثم:

1. Fetch branch HEAD.
2. Fetch GitHub Actions على ذلك الـSHA.
3. قارن الحالة مع هذا الملف.
4. لا تسأل المستخدم أن يعيد شرح المشروع إذا كانت المعلومات هنا وفي المستودع كافية.

---

# 9) حالة المراحل A -> I حتى الآن

## Phase A — Audio Review Vertical Slice Recovery — CLOSED

الهدف كان إصلاح المسار الحقيقي للتسجيل بدل استخدام Skip أو Fake score.

الإغلاق التنفيذي المؤكد:

`6ab969730f99585afa8053e5fece882538c5caaa`

على نفس SHA نجحت:

- Quality Gate run `33954323651`.
- M04 run `33954323671`.
- M09 run `33954323649`.

ما تم:

- الطالب يسجل فعليًا.
- التسجيل يحفظ ويرتبط بالمحاولة.
- يظهر انتظار مراجعة المشرف.
- `uploaded` لا يحسب complete/mastery.
- `graded` يسمح بالاستمرار وفق المراجعة.
- `rerecord_required` يعيد نفس الجولة.
- E2E أصبح يختبر السيناريو الحقيقي بدل تجاوز الصوت.
- إصلاح locator في Responsive admin tables بدون إضعاف سلوك المنتج.

---

## Phase B — Runtime Bypass Closure — CLOSED

تمت مراجعة bypasses ولم يحتج الإغلاق إلى تغيير تنفيذي جديد فوق Phase A candidate.

الحالة:

- `temporary_audio_skip` غير قابل للوصول من مسار الطالب.
- `/api/runtime-flags` Compatibility-only ويعيد `temporary_audio_skip: false`.
- `declared_media_gap_skip` لا يصنع إكمالًا؛ المسار العام Fail-closed ويرفضه.
- Historical markers تبقى للقراءة التاريخية فقط.
- Historical markers مستبعدة من score/mastery evidence.

لا تحذف هذه العلامات التاريخية إذا كانت لازمة لقراءة بيانات قديمة.

---

## Phase C — Approved Audio Binary Contract — CLOSED

تم تأكيد:

- manifest.
- WAV/MP3 pairs.
- static references.
- checksum validator.
- LET-01/SYL-13/WRD-29/INS-01/INS-02.

لا توجد Migration.

---

## Phase D — Deterministic Structured Projection — IMPLEMENTED + EXACT-SHA GREEN

المشكلة القديمة:

`services/api/seed_learning_posttest_projection_runtime.py`

كان يستنتج Student-visible data من `prompt_text` باستخدام regex/string parsing.

التنفيذ الحديث:

### Commit

`30356bdb2301cf213e9ff257470730693900ceaa`

`refactor(content): make learning projection structured and deterministic`

ما تغير:

- إزالة `import re` من مسار الإسقاط الفعلي.
- عدم قراءة `step.prompt_text` لبناء stimulus/question/hint/options.
- الاعتماد على structured DB runtime + explicit approved/source-derived overrides.
- إضافة contract:
  - `structured_db_runtime_v1`
- إبقاء Stable IDs/options/media/correctness metadata.
- إضافة explicit visible stimuli فقط للحالات القديمة التي يحتاج عرضها learner-visible field واضحًا.
- منع تسريب correct answer إلى stimulus/question.

### Regression commit

`62136541e7f8fdef0464d9535c7cc1876dae3b48`

`test(content): lock structured learning projection contract`

الاختبار يثبت، من ضمن أمور أخرى:

- لا `import re`.
- لا `step.prompt_text` في owner الحالي.
- لا `_extract_quoted`.
- لا `_single_visible_stimulus`.
- لا `_strip_serialized_choices`.
- لا `_clean_stimulus`.
- العقد `structured_db_runtime_v1` موجود.
- الإجابات لا تتسرب إلى student stimuli.
- `L1-CORE-06` يحتفظ بالسؤال/التعليمة المعتمدة.

Phase D لم تعد تحتاج Coding أساسي؛ تحتاج فقط توثيق الإغلاق في `STATUS/progress` ضمن الإغلاق التالي.

---

## Phase E — Runtime Readiness Hardening — IMPLEMENTED + EXACT-SHA GREEN

### Commit

`ba8940cff873a1982389a61715cdb5e8b864ff1c`

`feat(readiness): enforce exact content and approved audio contracts`

تم تقوية `/ready` بحيث لا يكتفي بأن API/storage متاحان.

أصبح يتحقق من:

- Config.
- Database.
- Redis.
- Object storage.
- Content runtime counts.
- Exact experience versions.
- Learning rounds count مقابل DB steps.
- Approved corrective audio contract.

الحسابات التي يجب أن تكون صحيحة:

- pretest = 30.
- learning = 65.
- posttest = 30.

كما يتحقق من أصول الصوت المصححة:

- LET-01.
- SYL-13.
- WRD-29.
- INS-01.
- INS-02.

ومن وجود WAV + MP3 لكل منها.

### Tests

`4e495cbddf9dcfa84fd6caee39a844394bb902f0`

`test(readiness): cover exact projection and approved audio gates`

ثم حصل تصحيح للإصدار الفعلي النشط:

`1ee0c939eac20b4b9aa2236958010ebbb53c1928`

`fix(readiness): match active structured learning projection version`

مهم: لا توسع `/ready` بطريقة تجعل تشغيل API نفسه يقرأ المحتوى من الملفات بدل DB؛ الـstudent runtime يبقى DB-driven، والـreadiness مجرد fail-closed deployment check.

Phase E أيضًا تحتاج فقط توثيق الإغلاق في ops docs عند الاستئناف.

---

## Additional invariant added after Phase E

### Commit

`07e83ba57244410f160a727b3c50001fbd7451a1`

`test(reports): prove report reads cannot mutate academic state`

هذا التغيير أضاف Regression يثبت أن report reads لا تغير academic state.

هذا Commit مهم جدًا لكنه **لا يغلق Phase F/G/H تلقائيًا**؛ هو hardening إضافي ضمن الطريق للإغلاق النهائي.

---

# 10) آخر حالة CI مؤكدة — مهمة جدًا

آخر SHA تنفيذي مؤكد قبل إضافة هذا Handoff:

`07e83ba57244410f160a727b3c50001fbd7451a1`

وعليه ثلاث بوابات مكتملة وناجحة على **نفس SHA**:

- Himma CI — Quality Gate
  - run `33958275012`
  - run number `601`
  - **SUCCESS**

- Himma M04 — Responsive Visual Gate
  - run `33958275097`
  - run number `185`
  - **SUCCESS**

- Himma M09 — Release Readiness Gate
  - run `33958275085`
  - run number `59`
  - **SUCCESS**

إذن Phase D + E التنفيذية ومجموعة hardening الحالية **Exact-SHA green** عند هذه النقطة.

إذا أصبح HEAD بعد هذا الملف Documentation-only commit، لا تخلط بين Documentation SHA وExecutable candidate. أعد جلب HEAD وأثبت الفرق.

---

# 11) المتبقي الحقيقي الآن

المتبقي ليس A/B/C/D/E من ناحية التنفيذ الأساسي.

المتبقي التنفيذي الأساسي:

**Phase F -> Phase G -> Phase H -> Phase I**

إضافة إلى تحديث `STATUS.md` و`progress.json` ليتطابقا مع الواقع الحالي.

---

# 12) Phase F — Student Path Regression Closure — المتبقي

الهدف: إثبات رحلة الطالب كاملة وليس مجرد أجزاء منفصلة.

يجب اختبار/تدقيق السيناريو التالي End-to-End:

`student login -> pretest -> audio review blockers -> placement -> level activities -> reinforcement -> promotion rules -> L3 completion -> posttest`

Checklist المطلوب:

- دخول الطالب بالكود يعمل deterministic.
- الاختبار القبلي = 30 سؤالًا.
- PRE/POST feedback محايد:
  - لا revealing correct/wrong.
  - لا hint يكشف الإجابة.
  - لا retry يفسد حياد التقييم.
- PRE-Q03:
  - target = `م`
  - other form = `مـ`
- POST-Q14 = `نَخْلَة`.
- Read-aloud في assessments:
  - uploaded لا يصبح تقييمًا نهائيًا.
  - canonical completion يبقى blocked حتى review.
- راجع Assessment navigation helpers أيضًا للتأكد أن `uploaded` لا يُعامل كـanswered في أي خطوة UI/next-state حتى لو كان completion preflight نفسه fail-closed.
- Placement thresholds صحيحة.
- L1/L2 promotion gates مطابقة للعقد.
- لا Auto-demotion.
- L3 لا يفتح completion/posttest بدون full evidence.
- Reinforcement target-only.
- لا cross-level fallback.
- Memory interaction:
  - الصور تظهر أولًا.
  - لا timer auto-hide.
  - الطالب يضغط `التالي` بنفسه.
  - بعدها recall/reorder.
- `L1-CORE-06` exact approved contract:
  - السؤال: `استمع إلى الكلمتين، ثم حدّد: هل تبدأان بالصوت نفسه أم بصوتين مختلفين؟`
  - التعليمة: `استمع إلى الكلمتين كاملتين، ثم قارن أول صوت في كل كلمة.`
  - pair text مخفي إذا flag يطلب ذلك.
  - `موز` يستخدم `WRD-29`.
- L1 auditory:
  - `L1-CORE-09` = قصة ليان / `INS-01` / skill `الفهم السمعي المباشر`.
  - `L1-REIN-11` = قصة نادر / `INS-02` / skill نفسه.
  - لا old `path_sequence` runtime fallback.
- Retakes:
  - تنتهي عبر canonical assessment completion.
  - تحافظ على المحاولات القديمة.
  - exactly one `official_for_reporting`.

المخرجات المطلوبة لـPhase F:

- targeted regression tests عند وجود نقص.
- E2E أو integration coverage يغطي الرحلة المطلوبة بدون bypass.
- لا تغييرات أكاديمية غير معتمدة فقط لجعل الاختبارات خضراء.

---

# 13) Phase G — Supervisor Audio/Admin UX Closure — المتبقي

يجب تدقيق/تثبيت تجربة المشرف كاملة:

- Queue التسجيلات pending = `AudioSubmission.status == "uploaded"`.
- تشغيل التسجيل من الـadmin.
- عرض معلومات الطالب/النشاط بوضوح.
- قبول التسجيل عبر supervisor review authority.
- طلب إعادة التسجيل عبر `rerecord_required`.
- learner waiting state واضح عند الرجوع/refresh.
- learner rerecord state واضح بعد الرفض.
- لا Fake AI scoring.
- لا hidden auto-grade.
- لا تخريب review history.
- لا حذف التسجيل السابق لتسهيل إعادة التسجيل.
- أي audit/review history يجب أن يبقى durable.
- بعد `graded` يجب أن يستأنف learner المسار canonical عند reload/next بدون manual DB repair.

راجع بشكل خاص:

- `services/api/review.py`
- learner activity renderer.
- admin review UI/routes.
- review-history/audit models.

إذا كان السلوك موجودًا أصلًا ويغطيه الاختبار، أغلق المرحلة بدون churn غير لازم.

---

# 14) Phase H — Proven-Dead Legacy Cleanup — المتبقي

الهدف ليس حذف كل Legacy؛ الهدف حذف **المثبت أنه ميت فقط**.

ابحث وصنف:

- `temporary_audio_skip`
- `TemporaryAudioSkip`
- `TEMP_AUDIO_SKIP`
- `HIMMA_TEMP_AUDIO_SKIP`
- `skip_recording`
- `temporary-audio`
- `runtime-flags`
- `declared_media_gap_skip`
- `AssessmentExperienceEnhancer`
- `AssessmentLetterStimulusPreviewFix`
- `MutationObserver`
- `querySelector`
- `innerText`
- portal/runtime DOM injection
- CSS patches المرتبطة بالـhashed classes
- repeated `!important`
- absolute positioning used as patch architecture

التصنيف المطلوب لكل hit:

- active runtime
- historical compatibility
- docs
- tests
- dead code

المسموح بالحذف:

- dead runtime/UI code فقط بعد إثبات أنه غير reachable وغير مطلوب للبيانات التاريخية.

الممنوع:

- حذف compatibility marker مطلوب لقراءة سجلات قديمة.
- حذف historical fields من DB لمجرد أنها لم تعد تستخدم في current UI.
- كسر seeds أو migrations.

القاعدة التصميمية للواجهة:

- React components.
- CSS modules/design tokens.
- explicit React state.
- لا DOM inference لإدارة state.

لا تعيد إدخال:

- `AssessmentExperienceEnhancer`
- `AssessmentLetterStimulusPreviewFix`

---

# 15) Phase I — Final Single-Candidate Closure — المتبقي النهائي

بعد إغلاق F/G/H:

اختر **SHA تنفيذي نهائي واحد**.

لا تعتبر المشروع جاهزًا إلا بعد نجاح جميع ما يلي على نفس SHA:

- approved content catalog validation.
- audio manifest/binary validation.
- Alembic upgrade.
- Alembic downgrade.
- Alembic upgrade مرة ثانية.
- model drift.
- seed idempotency مرتين.
- full backend tests.
- TypeScript.
- ESLint.
- frontend unit tests.
- Next.js production build.
- MinIO/API/Web integration startup.
- Playwright E2E.
- M04 responsive visual gate.
- M09 release readiness gate.

ثم:

- تحديث `docs/ops/STATUS.md`.
- تحديث `docs/ops/progress.json`.
- تحديث DECISIONS/OPEN_ITEMS إذا تغيرت حقيقة تشغيلية.
- تسجيل Run IDs + conclusions + final executable SHA.
- التمييز بوضوح بين executable SHA وأي docs-only SHA بعده.

**لا Merge/Release production بدون موافقة المستخدم الصريحة.**

---

# 16) ملفات/مكونات مهمة تم تحديد مالكيتها

## Public activity runtime

`services/api/main.py` يركب `activities_v4` كمسار public canonical للأنشطة.

`services/api/activities_v4.py` هو public owner الحالي ويستخدم بعض service helpers من legacy `activities.py`.

لا تعيد تركيب legacy router بالتوازي بشكل يخلق مالكين للمسار نفسه.

## Learning experience

`services/api/learning_experience.py`

هو جزء أساسي في بناء student view deterministic.

## Assessment completion

`services/api/assessment_completion.py`

هو canonical owner لإكمال الاختبارات، وفيه audio preflight يمنع الإكمال مع pending/rerecord blockers.

## Review

`services/api/review.py`

هو supervisor audio review authority الحالي.

## Runtime projection

`services/api/seed_learning_posttest_projection_runtime.py`

بعد Phase D يجب أن يبقى structured/deterministic ولا يعود prompt parser.

## Readiness

`services/api/readiness.py`

بعد Phase E أصبح fail-closed على exact content + approved corrective audio contract.

---

# 17) ملاحظات متعلقة بالـSTATUS/progress الحالية

`docs/ops/STATUS.md` يوثق A/B/C جيدًا، لكنه عند آخر قراءة ما زال يضع Phase D كـActive vertical slice ولا يحتوي إغلاق D/E الحديث.

`docs/ops/progress.json` أقدم بوضوح، ويحتوي executable candidate قديمًا ومهام open work من 2026-09-04.

أول خطوة توثيقية مناسبة في المحادثة الجديدة:

- لا تغير code لمجرد تحديث الوثائق.
- Fetch HEAD/Actions أولًا.
- حدّث STATUS/progress بحيث يسجلا:
  - D implemented/green.
  - E implemented/green.
  - current executable evidence = `07e83...` إذا لم يحدث code جديد.
  - F/G/H remaining.
  - I final closure remaining.

إذا كان HEAD قد تحرك، وثق SHA الجديد بدل الافتراض.

---

# 18) قائمة Recent commits المهمة

من Phase A وما بعده:

- `6ab969730f99585afa8053e5fece882538c5caaa`
  - `test(e2e): scope student evidence to desktop tables`
  - Phase A exact-SHA closure candidate.

- `045c66babf9d88e8887259c9abd7dbaec091ea65`
  - `docs(ops): close Phase A and start bypass closure audit`

- `7a862fa7c2ef12133687d4dc931c9d6f5f14f623`
  - `docs(ops): close bypass and audio audits; start structured projection`

- `30356bdb2301cf213e9ff257470730693900ceaa`
  - `refactor(content): make learning projection structured and deterministic`

- `62136541e7f8fdef0464d9535c7cc1876dae3b48`
  - `test(content): lock structured learning projection contract`

- `ba8940cff873a1982389a61715cdb5e8b864ff1c`
  - `feat(readiness): enforce exact content and approved audio contracts`

- `4e495cbddf9dcfa84fd6caee39a844394bb902f0`
  - `test(readiness): cover exact projection and approved audio gates`

- `1ee0c939eac20b4b9aa2236958010ebbb53c1928`
  - `fix(readiness): match active structured learning projection version`

- `07e83ba57244410f160a727b3c50001fbd7451a1`
  - `test(reports): prove report reads cannot mutate academic state`

---

# 19) Definition of Done للمشروع الحالي

لا يكفي أن الصفحات تفتح.

الإغلاق يعني:

- content semantics صحيحة.
- audio contract صحيح.
- no bypass.
- no fake scoring.
- student path كامل.
- supervisor review كامل.
- adaptation evidence صحيح.
- reports read-only.
- retakes/history محفوظة.
- seeds idempotent/non-destructive.
- readiness fail-closed.
- no DOM-state hacks.
- exact-SHA CI/M04/M09 green.
- ops docs updated.
- explicit user approval قبل الإنتاج.

---

# 20) نص جاهز لبدء المحادثة الجديدة

انسخ للمحادثة الجديدة:

> اقرأ كامل الملف `docs/ops/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-05_AR.md` من الفرع `recovery/ui-media-admin-overhaul` في المستودع `7eaur/himma-`، ثم اقرأ ملفات AGENTS وSOURCE_OF_TRUTH وACCEPTANCE_MATRIX وSTATUS وprogress وDECISIONS وOPEN_ITEMS المذكورة داخله. بعد ذلك اجلب HEAD الحالي ونتائج GitHub Actions لذلك الـSHA. لا تبدأ من الصفر ولا تعيد تحليل ما تم إغلاقه. اعتبر A/B/C مغلقة، وD/E منفذة ومثبتة بالـexact-SHA حسب الأدلة في Handoff ما لم يظهر HEAD أحدث يخالف ذلك. صحح STATUS/progress أولًا حسب الحالة الحالية ثم أكمل Phase F ثم G ثم H ثم I بإتقان. لا Docker، لا destructive git، لا حذف بيانات أكاديمية، لا Fake AI score، ولا تنتقل للإطلاق قبل Quality + M04 + M09 على نفس SHA النهائي وموافقتي الصريحة.

---

# 21) نقطة الاستئناف الدقيقة

**ابدأ من هنا:**

1. Re-fetch branch HEAD.
2. Confirm latest Quality/M04/M09.
3. Reconcile `STATUS.md` + `progress.json` مع D/E الحاليين.
4. نفذ **Phase F — Student Path Regression Closure**.
5. أغلقها بالأدلة.
6. انتقل إلى G ثم H.
7. أخيرًا Phase I على final single candidate.

لا حاجة لإعادة Phase A/B/C/D/E من الصفر إلا إذا كشف فحص HEAD الحالي Regression حقيقيًا.
