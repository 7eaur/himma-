# HIMMA MASTER CONTINUITY HANDOFF — 2026-09-05

> هذا الملف هو مرجع التسليم الرئيسي لمحادثة جديدة حتى تتابع تنفيذ منصة **هِمّة | HIMMA** من النقطة الحالية بدون إعادة اكتشاف المشروع من الصفر وبدون فقد القرارات الأكاديمية أو التقنية أو أدلة التنفيذ.

---

# 0) نقطة الاستئناف الحالية

المستودع الرسمي:

`7eaur/himma-`

الفرع الرسمي:

`recovery/ui-media-admin-overhaul`

آخر **Executable SHA** تم التحقق منه بالكامل قبل سلسلة توثيق الاستمرارية:

`07e83ba57244410f160a727b3c50001fbd7451a1`

وعلى نفس هذا الـSHA نجحت جميع البوابات الرئيسية:

- Quality Gate run `33958275012` — SUCCESS.
- M04 run `33958275097` — SUCCESS.
- M09 run `33958275085` — SUCCESS.

بعد ذلك أضيفت فقط توثيقات استمرارية/حالة:

- `8daf063994b9c4c8d50030703a5959e3dae33bf5` — إنشاء Handoff.
- `306367d4fa4e6b77430ca0cf09985db383e818bb` — تحديث `STATUS.md` حتى Phase E.
- `dbd2ff21613294c648a851ff9e9bb6893ad41036` — تحديث `progress.json` حتى Phase E.

لذلك في أي محادثة جديدة:

1. أعد جلب HEAD الحالي أولًا.
2. ميّز بين Documentation-only HEAD وبين آخر Executable candidate.
3. لا تعتبر أي SHA جديد PASS إلا بعد فحص Actions الخاصة به إذا كان يحتوي تغييرًا تنفيذيًا.
4. ابدأ التنفيذ من **Phase F** ما لم يظهر Regression حقيقيًا يفرض الرجوع.

`docs/ops/STATUS.md` و`docs/ops/progress.json` تم تحديثهما بالفعل ليتوافقا مع هذه الحالة.

---

# 1) تعريف المشروع

هِمّة منصة تعليمية عربية لطلاب الصف الثالث الذين لديهم صعوبات في القراءة.

المسار الأساسي:

`دخول بكود -> اختبار قبلي -> مراجعة التسجيلات -> تصنيف مستوى -> أنشطة المستوى -> تقوية موجهة -> متابعة تكيفية -> اختبار بعدي -> تقارير المشرف`

المحتوى الأكاديمي الأصلي المعتمد:

- 30 سؤال اختبار قبلي.
- 30 سؤال اختبار بعدي.
- 3 مستويات.
- لكل مستوى 10 أنشطة أساسية + 5 أنشطة تقوية في المصدر الأكاديمي الأصلي.
- الإجمالي الأصلي = 105 عنصرًا.

Runtime الحالي:

- total = 125.
- pretest = 30.
- learning = 65.
- posttest = 30.
- reinforcement total = 35.
- skills = 44.

التصنيف الأساسي بعد الاختبار القبلي:

- أقل من 50% -> L1.
- 50% إلى أقل من 80% -> L2.
- 80% إلى 100% -> L3.

هذا يحدد مستوى البداية فقط؛ بعده تطبق قواعد الأدلة والتكيف والترقية.

---

# 2) القواعد الأكاديمية غير القابلة للكسر

## L1 / L2 promotion

لا ترقية مبكرة إلا إذا تحقق كله:

- 6 Core على الأقل.
- Mastery >= 85%.
- Critical floor >= 70%.
- Full required critical coverage.
- لا Reinforcement blocker غير محلول.
- لا Audio Review blocker غير محلول.
- الترقية مستوى واحد فقط.
- لا Auto-demotion.

## L3

يحتاج full evidence قبل Journey completion / posttest.

## Reinforcement

- Targeted only.
- لا random fallback.
- لا cross-level fallback غير معتمد.

## Reports

التقارير Read Models فقط.

ممنوع أن تنشئ أو تعدل:

- mastery.
- activity completion.
- student level.
- academic evidence.
- official reporting attempt.

يوجد Regression test حديث على SHA `07e83...` يثبت أن قراءة التقارير لا تغير academic state.

## Retakes

- تنتهي عبر canonical assessment completion.
- تحفظ المحاولات القديمة.
- exactly one `official_for_reporting`.

---

# 3) عقد الصوت المعتمد

## Fixed approved assets

الحالة مغلقة من ناحية الملفات والـmanifest:

- 54 approved assets.
- 54 WAV.
- 54 MP3.
- missing required static audio = 0.

الربط المصحح:

- `LET-01` = `مَ` مع الاحتفاظ بالـStable ID، والبايتات مصدرها approved `SYL-15`.
- `SYL-13` = `سَا`.
- `WRD-29` = `موز`.
- `INS-01` = قصة ليان في المزرعة.
- `INS-02` = قصة نادر في الشاطئ.

Manifest:

`assets/audio/HIMMA_AUDIO_V1/manifest.csv`

العقد المرجعي:

`docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`

الـvalidator يتحقق من وجود الملفات وعضوية الـmanifest وSHA-256.

لا تعتبر checksum دليلًا على perceptual listening quality.

---

# 4) عقد تسجيل الطالب ومراجعة المشرف

المسار الحالي:

`record -> persist/upload -> supervisor review -> graded OR rerecord_required -> continue`

حالة التسجيل المرفوع قبل المراجعة:

`AudioSubmission.status = "uploaded"`

`uploaded` تعني Waiting only، ولا تعني:

- Correct.
- Success.
- Activity completion.
- Mastery evidence.

المشرف هو السلطة الحالية.

لا Fake AI scoring.

- `graded` -> قد يسمح للجولة بالاكتمال وفق قرار المراجعة.
- `rerecord_required` -> يعيد نفس جولة القراءة.

لا تحذف history للتسجيلات أو المراجعات أو المحاولات.

---

# 5) ASR المستقبلي

إذا طُلب مستقبلًا تحليل آلي، المعمارية المعتمدة:

**Reference-Guided Arabic Reading Analysis**

- ASR.
- Reference alignment.
- Correct / Deletion / Insertion / Substitution.
- Phonemic helper evidence.

هذا Future gate وليس شرطًا لإغلاق الصيانة الحالية.

لا تنفذ provider/calibration/automatic production score إلا بطلب منفصل صريح.

---

# 6) المعمارية المستهدفة للمحتوى

المسار الصحيح:

`Approved Academic Source -> Versioned Structured Projection -> PostgreSQL Runtime -> Structured API -> Deterministic Renderer`

ممنوع الرجوع إلى:

`raw prompt -> regex/string parsing -> DOM inference/runtime CSS patch`

القواعد:

- Stable IDs محفوظة.
- لا correct-answer inference من prompt text.
- لا interaction inference من raw prose إذا structured data موجودة.
- لا نقل prompt parsing للfrontend كحل التفافي.
- Seeds version-aware + idempotent + non-destructive.

Projection contract الحالي:

`structured_db_runtime_v1`

---

# 7) قيود التنفيذ وGitHub

- لا Docker محليًا.
- لا force push.
- لا reset/clean مدمر.
- لا حذف history أو branches.
- لا تعديل accepted stage branches مباشرة.
- لا حذف/تصفير students/sessions/attempts/mastery/recordings/reviews/audits/retakes/notifications.
- قبل كل write: Fetch branch HEAD من جديد.
- PASS فقط على exact SHA.
- لا Merge/Release production بدون موافقة المستخدم الصريحة.

المستودع التاريخي:

`7eaur/himma-deployment-sandbox`

Reference only.

---

# 8) ملفات البداية الإلزامية للمحادثة الجديدة

اقرأ قبل التنفيذ:

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
- `docs/ops/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-05_AR.md`

ثم اجلب HEAD وActions على الـSHA الحالي.

لا تطلب من المستخدم إعادة شرح المشروع إذا كانت المعلومات في المستودع كافية.

---

# 9) حالة Phases A -> E

## Phase A — CLOSED

Audio Review Vertical Slice Recovery.

Closed executable candidate:

`6ab969730f99585afa8053e5fece882538c5caaa`

Exact-SHA green evidence:

- Quality `33954323651`.
- M04 `33954323671`.
- M09 `33954323649`.

تم إصلاح المسار الحقيقي للتسجيل/المراجعة بدون bypass أو score مزيف، وإصلاح E2E بحيث يختبر التسجيل ثم انتظار المشرف ثم continuation.

## Phase B — CLOSED

Runtime bypass audit.

- `temporary_audio_skip` غير reachable للطالب.
- `/api/runtime-flags` compatibility-only ويرجع false.
- `declared_media_gap_skip` fail-closed ولا يصنع completion.
- Historical markers تبقى لقراءة السجل القديم فقط ومُستبعدة من scoring/mastery.

## Phase C — CLOSED

Approved Audio Binary Contract.

تم تثبيت manifest + WAV/MP3 + checksums + corrected assets.

## Phase D — CLOSED / EXACT-SHA GREEN

Implementation:

`30356bdb2301cf213e9ff257470730693900ceaa`

`refactor(content): make learning projection structured and deterministic`

Regression:

`62136541e7f8fdef0464d9535c7cc1876dae3b48`

`test(content): lock structured learning projection contract`

النتيجة:

- لا `import re` في active projection owner.
- لا `step.prompt_text` لبناء learner structured projection.
- لا `_extract_quoted` / `_single_visible_stimulus` / `_strip_serialized_choices` / `_clean_stimulus` active inference.
- structured DB runtime + explicit source-derived overrides.
- answers لا تتسرب إلى student stimulus/question.
- `L1-CORE-06` locked by regression.

## Phase E — CLOSED / EXACT-SHA GREEN

Implementation:

`ba8940cff873a1982389a61715cdb5e8b864ff1c`

Tests:

`4e495cbddf9dcfa84fd6caee39a844394bb902f0`

Version correction:

`1ee0c939eac20b4b9aa2236958010ebbb53c1928`

`/ready` أصبح fail-closed على:

- config.
- PostgreSQL.
- Redis.
- object storage.
- exact pretest/learning/posttest counts.
- exact experience versions.
- learning rounds مقابل DB steps.
- required corrective approved audio WAV/MP3 presence.

ثم أضيف:

`07e83ba57244410f160a727b3c50001fbd7451a1`

`test(reports): prove report reads cannot mutate academic state`

وعلى هذا الـSHA كانت Quality + M04 + M09 كلها SUCCESS.

---

# 10) المتبقي الحقيقي الآن

المتبقي التنفيذي الأساسي:

**Phase F -> Phase G -> Phase H -> Phase I**

A/B/C/D/E لا تعاد من الصفر إلا إذا ظهر Regression حقيقي على HEAD الحالي.

---

# 11) Phase F — Student Path Regression Closure

ابدأ منها.

يجب إثبات End-to-End:

`login -> pretest -> reviewed audio -> placement -> level activities -> reinforcement -> promotion -> L3 completion -> posttest`

Checklist:

- Student code login.
- 30 pretest questions.
- 30 posttest questions.
- PRE/POST feedback محايد: لا revealing correct/wrong، لا answer-revealing hints، لا retry يفسد assessment neutrality.
- PRE-Q03 target `م` وother form `مـ`.
- POST-Q14 = `نَخْلَة`.
- Assessment audio `uploaded` يبقى pending review.
- Re-audit assessment navigation helpers حتى لا يصبح pending audio "answered" في UI/next-state قبل المراجعة؛ canonical completion preflight أصلًا fail-closed.
- Placement thresholds صحيحة.
- L1/L2 promotion gates صحيحة.
- لا auto-demotion.
- L3 full evidence required.
- Reinforcement targeted only.
- Memory: images first -> learner presses `التالي` -> recall/reorder؛ لا timer auto-hide.
- `L1-CORE-06` exact approved question/instruction، و`موز` يستخدم `WRD-29`.
- `L1-CORE-09` -> `INS-01` / ليان / `الفهم السمعي المباشر`.
- `L1-REIN-11` -> `INS-02` / نادر / same skill.
- لا old `path_sequence` runtime fallback.
- Retakes preserve history and exactly one official reporting attempt.

لا تغير academic meaning فقط لجعل test أخضر.

---

# 12) Phase G — Supervisor Audio/Admin UX Closure

Reconfirm:

- pending queue = `uploaded`.
- playback works.
- accept review path.
- `rerecord_required` path.
- learner waiting state survives reload.
- learner rerecord state clear.
- no hidden auto-grade.
- supervisor authority preserved.
- review/audit history durable.
- بعد `graded` يعود learner للمسار canonical بدون manual DB repair.

راجع خصوصًا:

- `services/api/review.py`
- learner activity page/renderer.
- admin audio review UI/routes.
- review history/audit persistence.

إذا كانت كل invariants مثبتة أصلًا، أغلق بدون churn غير ضروري.

---

# 13) Phase H — Proven-Dead Legacy Cleanup

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
- portal DOM injection
- hashed-class CSS patching
- repeated `!important`
- absolute-position patch architecture

لكل hit صنّفه:

- active runtime.
- historical compatibility.
- docs.
- tests.
- dead code.

احذف فقط proven-dead runtime/UI code.

لا تحذف compatibility المطلوبة لقراءة السجل الأكاديمي القديم.

Frontend standard:

React components + CSS modules/design tokens + explicit state.

لا تعيد إدخال `AssessmentExperienceEnhancer` أو `AssessmentLetterStimulusPreviewFix`.

---

# 14) Phase I — Final Single-Candidate Closure

بعد F/G/H اختر SHA تنفيذي نهائي واحد.

لا تغلق المشروع حتى ينجح على نفس الـSHA:

- approved content validation.
- audio manifest/binary validation.
- Alembic upgrade/downgrade/upgrade.
- model drift.
- seed idempotency twice.
- full backend tests.
- TypeScript.
- ESLint.
- frontend unit tests.
- Next production build.
- MinIO/API/Web startup.
- Playwright E2E.
- M04.
- M09.

ثم حدّث:

- `STATUS.md`.
- `progress.json`.
- `DECISIONS.md` / `OPEN_ITEMS.md` إذا تغيرت حقيقة تشغيلية.

وسجل:

- final executable SHA.
- run IDs.
- conclusions.

لا production merge/release بدون موافقة المستخدم.

---

# 15) Current canonical owners

## Public activities

`services/api/main.py` يركب `activities_v4` كـpublic canonical activities router.

لا تعيد legacy activities router كمنافس parallel owner.

## Learning experience

`services/api/learning_experience.py`

Student deterministic view owner الأساسي.

## Assessment completion

`services/api/assessment_completion.py`

Canonical assessment completion، وفيه audio blocker/preflight.

## Audio review

`services/api/review.py`

Supervisor review authority.

## Runtime projection

`services/api/seed_learning_posttest_projection_runtime.py`

بعد Phase D يجب أن يبقى structured ولا يعود prompt parser.

## Readiness

`services/api/readiness.py`

بعد Phase E exact/fail-closed runtime readiness owner.

---

# 16) Recent commit trail المهم

- `6ab969730f99585afa8053e5fece882538c5caaa` — Phase A executable closure candidate.
- `045c66babf9d88e8887259c9abd7dbaec091ea65` — close A/start bypass audit docs.
- `7a862fa7c2ef12133687d4dc931c9d6f5f14f623` — close B/C/start D docs.
- `30356bdb2301cf213e9ff257470730693900ceaa` — structured projection refactor.
- `62136541e7f8fdef0464d9535c7cc1876dae3b48` — projection regression lock.
- `ba8940cff873a1982389a61715cdb5e8b864ff1c` — readiness hardening.
- `4e495cbddf9dcfa84fd6caee39a844394bb902f0` — readiness tests.
- `1ee0c939eac20b4b9aa2236958010ebbb53c1928` — readiness version fix.
- `07e83ba57244410f160a727b3c50001fbd7451a1` — report non-mutation regression; exact-SHA green candidate.
- `8daf063994b9c4c8d50030703a5959e3dae33bf5` — initial continuity handoff docs.
- `306367d4fa4e6b77430ca0cf09985db383e818bb` — STATUS reconciliation through E.
- `dbd2ff21613294c648a851ff9e9bb6893ad41036` — progress reconciliation through E.

---

# 17) Definition of Done

المشروع لا يعتبر مغلقًا لمجرد أن الصفحات تعمل.

الإغلاق يعني:

- content semantics صحيحة.
- no audio bypass.
- no fake scoring.
- static audio contract صحيح.
- student path كامل.
- supervisor review كامل.
- adaptive evidence صحيح.
- reports read-only.
- retakes/history محفوظة.
- seeds non-destructive/idempotent.
- readiness fail-closed.
- no DOM-state hacks.
- final exact-SHA Quality + M04 + M09 green.
- ops docs updated.
- explicit user approval قبل الإنتاج.

---

# 18) برومبت جاهز للمحادثة الجديدة

> اقرأ كامل `docs/ops/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-05_AR.md` من الفرع `recovery/ui-media-admin-overhaul` في المستودع `7eaur/himma-`، ثم اقرأ AGENTS وSOURCE_OF_TRUTH وACCEPTANCE_MATRIX وSTATUS وprogress وDECISIONS وOPEN_ITEMS والعقد الصوتي المذكورة داخله. بعد ذلك اجلب HEAD الحالي ونتائج GitHub Actions لذلك الـSHA. لا تبدأ من الصفر ولا تعيد فتح A/B/C/D/E إلا إذا ظهر Regression فعلي. آخر Executable candidate المثبت في الـHandoff هو `07e83ba57244410f160a727b3c50001fbd7451a1` وكانت Quality/M04/M09 كلها خضراء عليه؛ بعده توجد commits توثيقية فقط حتى لحظة التسليم. ابدأ Phase F ثم G ثم H ثم I بإتقان. لا Docker، لا destructive git، لا حذف بيانات أكاديمية، لا Fake AI score، ولا production release قبل exact-SHA final gates وموافقتي الصريحة.

---

# 19) أول عمل للمحادثة الجديدة

1. Fetch current branch HEAD.
2. Fetch current Actions.
3. Confirm whether changes since `07e83...` are docs-only or executable.
4. اقرأ `STATUS.md` و`progress.json` المحدثين.
5. ابدأ **Phase F** مباشرة.
6. أغلق F بالأدلة، ثم G، ثم H، ثم I.
