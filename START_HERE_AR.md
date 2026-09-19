# ابدأ من هنا — منصة هِمّة | الحالة الحالية الموحّدة

**هذه هي نقطة الدخول الوحيدة لأي محادثة أو وكيل جديد.**

آخر توحيد موثق: 2026-09-19  
Repository: 7eaur/himma-  
Official branch: stage/02-content  
آخر Functional Release SHA مثبت: 512f0a550eb098f0ce904ec4ed526d9e28098a6a  
حالة الإصدار: MERGED + CI GREEN + RAILWAY DEPLOYED + READY

Latest pre-merge current-state gate SHA: 5de29b71b9ab8d7df5c6c723136810f5ed56b213  
- QG #943 / Run 35403341210 = SUCCESS.  
- M04 #361 / Run 35403341212 = SUCCESS.  
- M09 #226 / Run 35403341199 = SUCCESS.  
- QG backend = 894 passed, 5 warnings; integration Playwright = 23 passed (3.8m).  
- M04 artifact = 10571297880; digest = sha256:3498fc96ea6f555b884bca91016048cbb0459e5354d9b76af5709160383b8518.  
- M09 runtime = 125 items / 44 skills; PostgreSQL restore PASS; object-store restore 35; audio bypass absent; readiness all ok.

هذا descendant لا يغيّر Product Runtime؛ Latest Functional SHA يبقى 512f0a550eb098f0ce904ec4ed526d9e28098a6a.


> قاعدة إلزامية: ابدأ دائمًا بجلب HEAD الحي للفرع الرسمي وحالة GitHub Actions وRailway. إذا كان هناك descendant توثيقي أحدث من SHA أعلاه فلا تعتبر اختلاف SHA اختلافًا وظيفيًا قبل مقارنة الملفات.

## 1. ترتيب الحقيقة

عند أي تعارض استخدم هذا الترتيب:

1. live code على stage/02-content.
2. PostgreSQL schema + Alembic migrations.
3. executable tests + exact-SHA GitHub Actions.
4. verified Railway runtime.
5. canonical content/audio/product contracts.
6. الوثائق الحالية المدرجة في docs/ops/DOCUMENTATION_INDEX.md.
7. الوثائق المؤرخة القديمة، handoffs، checkpoints، audits — تاريخ فقط.

أي وثيقة تاريخية تقول NOT MERGED أو NOT DEPLOYED أو STOP BEFORE A11 لم تعد تصف الحالة الحالية.

## 2. ما هي هِمّة؟

هِمّة منصة ويب عربية RTL تعليمية/بحثية لطلاب الصف الثالث ذوي صعوبات القراءة. لا يوجد تطبيق موبايل أصلي ضمن النطاق الحالي.

الأدوار الظاهرة:
- الطالب: يدخل بكود بسيط أنشأه المشرف؛ لا تسجيل ذاتي ولا بريد للطفل.
- المشرف: ينشئ الطلاب، يتابع المسار، يراجع التسجيلات، يدير المحتوى والإعدادات والتقارير. القيمة الداخلية researcher باقية كتوافق تقني فقط ولا تظهر كمسمى منتج.

السعة الافتراضية المعتمدة: 50 طالبًا عبر HIMMA_MAX_STUDENTS، والحسابات غير النشطة تدخل في الحد.

## 3. رحلة الطالب الحالية

1. دخول الطالب بالكود.
2. اختبار قبلي من 30 بندًا.
3. توزيع أولي من الدرجة النهائية فقط:
   - أقل من 50 → L1.
   - من 50 إلى أقل من 80 → L2.
   - 80 فأعلى → L3.
4. التعلم يبدأ من المستوى المسند؛ المستويات الأدنى تعتبر متجاوزة بالتسكين لا مكتملة.
5. داخل النشاط:
   - >=80 نجاح.
   - 70..<80 إعادة موجهة.
   - <70 تقوية مستهدفة في المستوى نفسه.
6. التكيف المستمر يستخدم أحدث 3 أدلة صالحة من جلسة Core النشطة بأوزان 50/30/20.
7. L1/L2 يمكن ترقيتهما مبكرًا بعد 6 Core على الأقل مع mastery >=85 وتغطية المهارات الحرجة وأدنى مهارة حرجة >=70 وعدم وجود تقوية/مراجعة معلقة.
8. لا يوجد خفض تلقائي.
9. L3 نهائي، ويحتاج 10 Core لإكمال رحلة التعلم.
10. البعدي 30 بندًا ولا يفتح إلا بعد اكتمال رحلة التعلم وتفعيل المشرف له.
11. النتائج والتقارير تحفظ من المصدر نفسه دون إعادة حساب مختلفة في الواجهة.

## 4. عقد التسجيل الصوتي الحالي

المراجعة البشرية للمشرف هي السلطة الأكاديمية الحالية.

السلوك المعتمد:
- تسجيل القراءة يحفظ ويرسل للمراجعة.
- التسجيل pending/uploaded لا يتحول تلقائيًا إلى خطأ أو mastery أو انتقال.
- إذا بقيت أسئلة غير مجابة في القبلي/البعدي، الطالب يكمل الأسئلة التالية ولا يتوقف بعد كل تسجيل.
- الإنهاء الأكاديمي النهائي للجلسة يبقى محجوبًا حتى تُحسم التسجيلات المطلوبة.
- طلب إعادة التسجيل ينشئ مهمة صريحة مستقلة؛ لا يخطف السؤال أو النشاط الحالي تلقائيًا.
- التسجيل السابق يبقى في التاريخ؛ لا حذف history ولا استبدال صامت.
- لا Student Audio Skip ولا Temporary Audio Skip ولا bypass.
- التحليل الصوتي الآلي/مزود ASR الإنتاجي خارج الإغلاق الحالي وغير سلطوي أكاديميًا حتى اعتماد مستقل.

مرجع العقد الحالي:
docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_CURRENT_AR.md

## 5. المحتوى القانوني

Approval: HIMMA-CONTENT-APPROVAL-2026-09-08

هناك رقمان يجب عدم خلطهما:
- Catalog baseline/source = 105 بندًا: 30 قبلي + 30 بعدي + 30 Core + 15 تقوية baseline.
- Runtime المعتمد = 125 بندًا: 30 قبلي + 30 بعدي + 30 Core + 35 تقوية، بعد 20 إضافة تقوية versioned معتمدة.
- المهارات canonical = 44.

مسار الحقيقة:
approved/versioned sources → canonical compile/release → deterministic publication → PostgreSQL → APIs → UI

لا runtime patches ولا seeding تاريخي متعارض ولا content hardcoding داخل JSX.

## 6. الأصول والهوية

الهوية الأساسية:
- Blue #347FD9
- Green #51B985
- Yellow #FFC857
- Navy #20364D
- Light #F7FBFF
- Border #DCE8F2
- Tajawal لواجهة الطالب.
- IBM Plex Sans Arabic لواجهة المشرف والتقارير.
- Noto Sans Arabic fallback.

الصوت الثابت المعتمد:
- 54 IDs.
- 54 WAV masters + 54 MP3 web = 108 binaries.
- 4 feedback + 6 letter sounds + 13 syllables + 29 words + 2 auditory stories.
- manifest.csv هو مرجع IDs.
- INS-01 وINS-02 القصتان المعتمدتان.
- المصدر SYL-15 منشور تحت runtime ID المستقر LET-01 بصوت مَ.

## 7. المعمارية الحالية

Frontend:
- apps/web
- Next.js 16.3.4 + React 19.2.8 + TypeScript + Tailwind 4.
- صفحات الطالب والمشرف وRTL/Responsive.
- لا يملك قواعد الدرجات أو التكيف المرجعية.

Backend:
- services/api
- FastAPI + SQLAlchemy + PostgreSQL + Alembic.
- مصادقة وصلاحيات، الطلاب، المحتوى، الاختبارات، التعلم، التكيف، الصوت، المراجعة، التقارير، التدقيق.
- الشجرة الحالية تحتوي 15 Alembic migration files.

Infrastructure:
- PostgreSQL = transactional truth.
- Redis = coordination/rate limiting؛ ليس مصدر حقيقة أكاديمي.
- private object storage = تسجيلات/أصول خاصة.
- Railway يشغل النسخة المنشورة.
- CI يشغل PostgreSQL وRedis وMinIO native/pinned بدون Docker containers.
- Railway يستخدم Dockerfiles كوسيلة build/deploy للمنصة فقط؛ هذا لا يغير قاعدة عدم الاعتماد على Docker كبيئة تطوير/اختبار محلية للمشروع.

## 8. واجهات المنتج الحالية

طالب:
- /student/login
- /student
- /student/session/[id]
- /student/activity/[id]

مشرف:
- /admin/login
- /admin
- /admin/students
- /admin/students/new
- /admin/students/[id]
- /admin/audio-review
- /admin/content-preview
- /admin/reports
- /admin/skill-reports
- /admin/settings
- /admin/account

آخر دفعة UX أعادت بناء:
- Student question system responsive.
- Student Dashboard كرحلة واضحة بدل بطاقات متساوية.
- Admin dashboard aggregation للتسجيلات المعلقة.
- Audio Review workflow: Recording → Listen → Decision → Evaluation/Notes → Save.
- وضوح حقول إجمالي الوحدات/الحذف/الاستبدال/الإضافة.
- قرار واضح: اعتماد القراءة أو طلب إعادة تسجيل.
- Student Profile mobile tabs.
- Add Student الحقيقي.
- Content Preview.
- Toast/feedback behavior.
- responsive/RTL/overflow coverage.

## 9. أدلة الاختبار للنسخة الوظيفية الحالية

Functional SHA:
512f0a550eb098f0ce904ec4ed526d9e28098a6a

Quality Gate:
- #933 / Run 35301572062 = SUCCESS.
- Security = SUCCESS.
- Frontend = SUCCESS.
- Backend = 894 passed, 5 warnings.
- Integration Playwright = 20 passed (3.6m).
- Playwright report artifact ID = 10530208479.

M04 Responsive Visual Gate:
- #359 / Run 35299593387 = SUCCESS.
- artifact ID = 10529103623.
- digest = sha256:04a0b08ac2e25e27405ab24b2ec85bc1229b67909c47eb558c69bd859cd2826b.

M09 Release Readiness:
- #224 / Run 35299593312 = SUCCESS.
- Backend product regression = 894 passed, 5 warnings.
- deterministic browser regression = 20 passed (3.6m).
- readiness checks config/database/content/approved_audio/storage/redis/security_mode = ok.
- PostgreSQL backup/restore = PASS.
- restored content_items = 125; skills = 44.
- object storage backup/restore = 35 objects verified.
- deleted student audio bypass route = absent.

ملاحظة تحقق: بعد توحيد التوثيق يجب تشغيل exact-head gate للـdocs/CI descendant؛ functional evidence أعلاه يبقى مرجع السلوك ما لم يتغير الكود الوظيفي.

## 10. Production على Railway

المشروع الفعلي: friendly-dream  
Environment: production

الخدمات:
- himma-api
- himma-web
- PostgreSQL
- Redis
- bucket: himma-audio

إصدار الوظائف المثبت:
512f0a550eb098f0ce904ec4ed526d9e28098a6a

Railway evidence:
- API deployment 283feef7-ce46-41c1-84a1-f714e508405e = SUCCESS.
- Web deployment 629571e4-8188-4b91-bfe5-79fe5e1ecae1 = SUCCESS.
- API pre-deploy migrations = PASS.
- canonical publication = 125 runtime items.
- researcher seed = PASS.
- /ready healthcheck during deployment = HTTP 200.
- Postgres and Redis deployments = SUCCESS.
- himma-audio bucket present.
- Web service domain: himma-web-production.up.railway.app.

أي docs-only descendant قد يسبب Railway redeploy بCommit أحدث مع نفس functional tree؛ لا تخلط بين deployment commit وfunctional release SHA.

## 11. حالة الفروع — ما عدا فروع مزود الصوت

تمت مراجعة كل الفروع غير الخاصة بمزود/مختبر الصوت مقابل official SHA الحالي.

النتيجة:
- stage/02-content هو الفرع الرسمي الوحيد.
- fix/ux-polish-audit-2026-09-18 وintegration/ux-polish-audit-20260918 مطابقان للـfunctional official SHA.
- كل فروع audit/recovery/stage القديمة وبقية integration/release/fix ذات الصلة موجودة داخل تاريخ stage/02-content ولا تحمل عملًا مطلوبًا للدمج.
- deployment/platform-sandbox هو الفرع غير الصوتي الوحيد المتشعب؛ لديه 9 commits قديمة فريدة تخص topology نشر تجريبي قديم، ولا تُدمج لأنها superseded بالـRailway production الحالي.
- لا يوجد أي non-audio branch يحمل feature حديثة لازمة ومفقودة من الفرع الرسمي.

التفاصيل:
docs/maintenance/HIMMA_BRANCH_INVENTORY_2026-09-18_AR.md

فروع مزود/مختبر الصوت مستبعدة من هذه المصالحة بطلب المالك ولا تُدمج ضمن الحالة الحالية.

## 12. ما هو مغلق وما هو مفتوح

مغلق:
- A00–A09 audit chronology.
- W1–W6 corrective execution.
- canonical content reconciliation.
- student/admin core journeys.
- human audio review and rerecord contract.
- latest UX rebuild.
- exact-SHA QG/M04/M09.
- merge to stage/02-content.
- Railway deployment of the latest functional release.
- backup/restore proof in M09.

مفتوح/خارجي فقط:
- Production ASR provider/calibration/governance — مستبعد من هذا التسليم.
- مدة الاحتفاظ النهائية ببيانات/تسجيلات الأطفال قبل دراسة حقيقية.
- تفاصيل الدراسة البحثية النهائية مثل عدد/مدة الجلسات إذا لم يعتمدها المالك بعد.
- manual human screen-reader acceptance غير مدعى؛ automated axe/keyboard/responsive coverage موجود.
- custom domain/branding entity details only if owner wants them; current Railway deployment does not depend on them.

## 13. قواعد لا يجوز كسرها

- No fake ASR.
- No Student/Temporary Audio Skip.
- No history deletion.
- No random/cross-level reinforcement.
- No automatic demotion.
- لا إضعاف tests، skip/xfail، retry masking.
- لا runtime repair overlays.
- لا secrets أو بيانات أطفال أو recordings في Git.
- reference/ read-only.
- Root Cause fixes only.
- كل PASS مهم يحتاج exact SHA evidence.
- أي migration مؤثر يحتاج rollback/restore proof.
- كل تغيير أكاديمي يحتاج ADR + tests.

## 14. ترتيب القراءة لمحادثة جديدة

بعد قراءة هذا الملف، اقرأ فقط بالترتيب:

1. docs/ops/STATUS.md
2. docs/ops/progress.json
3. docs/specs/SOURCE_OF_TRUTH.md
4. docs/specs/SYSTEM_SPEC.md
5. .agents/rules/00-himma-core.md
6. .agents/rules/10-delivery-protocol.md
7. .agents/rules/20-security-quality.md
8. docs/ops/DECISIONS.md
9. docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_CURRENT_AR.md
10. docs/ops/EVIDENCE_INDEX.md
11. docs/maintenance/HIMMA_BRANCH_INVENTORY_2026-09-18_AR.md
12. docs/ops/OPEN_ITEMS.md
13. docs/ops/DOCUMENTATION_INDEX.md

ثم افتح الملفات التاريخية فقط إذا احتجت سبب قرار أو chronology.

## 15. بروتوكول الاستلام لمحادثة جديدة

1. Fetch live stage/02-content HEAD.
2. تحقق هل HEAD functional أو docs-only descendant.
3. تحقق من آخر QG/M04/M09 المرتبط بأحدث تغيير وظيفي.
4. تحقق من Railway إذا كانت المهمة تتعلق بالإنتاج.
5. لا تعِد audit أو UX rebuild أو recovery بدون regression evidence.
6. ابدأ من أول طلب جديد للمالك فوق هذه الحالة.

هذا الملف هو handoff الحالي. أي handoff مؤرخ قبله تاريخ فقط.
