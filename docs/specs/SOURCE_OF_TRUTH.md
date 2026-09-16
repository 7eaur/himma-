# خريطة مصدر الحقيقة — منصة هِمّة

**آخر تحديث تنفيذي:** 2026-09-16

تمنع هذه الخريطة اختيار مرجع بالاسم أو التاريخ فقط عند وجود نسخ تاريخية متجاورة. الهدف هو الحفاظ على التاريخ مع منع ملف قديم من تجاوز كود/عقد/قرار أحدث تم اختباره.

## ترتيب القوة العام

للسلوك التنفيذي الحالي:

1. **الكود الحي + PostgreSQL schema/Alembic migrations** على فرع التنفيذ الحالي.
2. **Executable tests + exact-SHA GitHub Actions** التي تثبت السلوك على نفس SHA.
3. **العقود الكانونية والقرارات المؤرخة المعتمدة** الخاصة بالمجال، ومنها content/reward/media/audio governance.
4. المواصفات والحالة التشغيلية الحالية داخل `docs/specs/` و`docs/ops/`.
5. بيانات الحزم التنفيذية داخل `assets/`.
6. الوثائق الأصلية داخل `reference/original/`.
7. النسخ النصية المشتقة داخل `reference/derived/`.
8. لوحات العرض ونموذج الواجهة بوصفهما مرجعًا بصريًا وتفاعليًا فقط.

إذا كان القرار داخل `docs/ops/DECISIONS.md` أحدث وما يزال صالحًا ومتسقًا مع الكود والاختبارات الحالية، فهو جزء من بند العقود/القرارات أعلاه. أما القرار الذي تجاوزه عقد أحدث موثق فيبقى تاريخيًا.

## الخريطة التنفيذية الحالية

| المجال | المصدر التنفيذي الحالي | دور الملفات الأخرى |
|---|---|---|
| اسم المنتج والهوية الأساسية | `.agents/rules/00-himma-core.md` + manifests المعتمدة داخل `assets/` | دليل الهوية الأصلي محفوظ للشرح والتاريخ؛ حزمة المطور هي مرجع الملفات القابلة للتطبيق. |
| نطاق المنتج والمنطق | الكود الحالي + tests + القرارات الفعالة في `docs/ops/DECISIONS.md` + `docs/specs/SYSTEM_SPEC.md` + `docs/specs/ACCEPTANCE_MATRIX.md` | أي صياغة أقدم متعارضة تبقى تاريخية. |
| الحالة والاستئناف | `docs/ops/STATUS.md` + `docs/ops/progress.json` + `NEXT_CONVERSATION_PROMPT.md` + أحدث Master Continuity Handoff | handoffs/checkpoints الأقدم chronology ولا تتقدم على الحالة الحالية. |
| سجل الفجوات | `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md` للfinding/root cause/dependencies/tests + أحدث execution/status addendum لحالة الإغلاق | لا نعيد كتابة سجل التدقيق تاريخيًا؛ status overlays توضح ما أُغلق لاحقًا. |
| المحتوى التعليمي الحالي | `services/api/content_approval_contract_2026_09_08.py` + `services/api/canonical_content_compiler.py` + `services/api/canonical_release.py` + `services/api/canonical_content_publisher.py` + executable projection/release tests | `reference/original/01_المحتوى_والتخطيط_المعتمد_لمنصة_همة.docx` ومصادر أقدم تمد الحقول/السياق التاريخي الذي لم يُستبدل، لكنها لا تتجاوز overrides/approvals الأحدث. |
| publication/runtime content | canonical release/publisher ثم PostgreSQL runtime | seed/correction/projection scripts التاريخية لا تصبح authority جديدة لمجرد وجودها؛ تصنف حسب runtime/migration/test/history. |
| التوزيع القبلي والتكيف المستمر | `services/api/placement_scoring.py` + `services/api/adaptation.py`/`adaptation_runtime.py` + canonical tests؛ والقرارات الفعالة ذات الصلة | Placement 50/80 منفصل عن learning adaptation. لا تعاد demotion أو gates تاريخية بلا قرار جديد. |
| Completion/Promotion | `services/api/level_completion.py` + Journey/Rewards consumers + W1 executable tests | UI pointer مثل `current_level` لا يثبت completion تاريخيًا بمفرده. |
| التسجيل والمراجعة | `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md` + current audio/review code + W1/W2 tests | Human Supervisor Review هي authority الحالية؛ machine analysis advisory. |
| Production ASR | `services/api/asr_governance.py` + `AUD-A03-008` external-approval boundary | لا يعتبر env/config أو experimental branch اعتمادًا. Provider/calibration/privacy/cost/governance مطلوبة قبل السلطة الإنتاجية. |
| الأصوات الجاهزة | `assets/audio/HIMMA_AUDIO_V1/manifest.csv` + current audio asset tests/contracts | أرقام الحزم القديمة تصف مراحل تاريخية ولا تتقدم على manifest الحالي. |
| الصور التعليمية | `assets/education/ASSET_MANIFEST.json` + `assets/education/developer/asset-map.json` + canonical media contracts/tests | الوثائق واللوحات تشرح الاستخدام، ولا تستبدل asset identity/manifest. |
| Media semantic role | current canonical media contract + owner/client approvals + final-release tests | Sep-08 media tuples يمكن أن تكون historical input؛ أي قرار أحدث معتمد يجب أن ينعكس في final release قبل hash/publication. |
| قرار W4 lexical media | `docs/ops/HIMMA_W4_OWNER_CLIENT_APPROVAL_2026-09-14.md` + `services/api/w4_media_semantics.py` بعد إغلاق gate | `lexical_stimulus` مباشر؛ `story_context` سياقي. لا يُعاد طلب القرار من العميل. عند كتابة هذا التحديث ما زال MEDIA-002 gate غير مغلق بسبب stale projection expectation موثق في current STATUS. |
| الشخصيات/الشارات/الأيقونات | asset manifests + `services/api/reward_catalog.py` + Reward Catalog API + approved W4 badge decision | لوحات الشخصيات مرجع بصري. لا hardcoded parallel reward map في Student/Admin. |
| تجربة الواجهة | current Next.js code + shared design/accessibility components + E2E | `reference/ui-prototype/` مرجع بصري وتفاعلي فقط، وليس معمارية إنتاجية أو مصدر بيانات. |
| الأمن/الأداء/الوصولية/الرصد | current runtime config/middleware + W2/W3 tests + Quality Gate | audit docs تشرح finding؛ الإغلاق يثبت بالكود والاختبار. |

## العقود الأكاديمية المختصرة التي لا تُستنتج من وثيقة قديمة

- Placement: `<50 → L1`, `50..<80 → L2`, `80..100 → L3`.
- Learning adaptation: `>=80 success`, `70..<80 guided retry`, `<70 reinforcement`.
- L1/L2 early promotion يمكن بعد >=6 Core عند استيفاء evidence الكانونية.
- L3 يتطلب 10 Core.
- لا automatic demotion.
- latest valid active-session evidence له الأولوية وفق العقد الحالي.
- pending/uploaded learning audio محايد أكاديميًا.
- rerecord append-only، القديم immutable، والـlatest submission active.
- Manual override لا يعني completion أو badge.

التفاصيل واختبارات الإثبات في W1/W2 checkpoints والكود الحالي؛ لا تستخدم هذه النقاط كبديل عنها.

## قاعدة التعارض

لا يُحذف المرجع التاريخي ولا يُعدّل بصمت لإخفاء التعارض. عند وجود قرار أحدث:

1. حدد owner الصحيح للحقيقة.
2. طبّق القرار الأحدث في canonical/runtime path الصحيح.
3. حدّث الاختبارات التي تتحقق من **الحقيقة الحالية** بدل إجبار المنتج على قيمة تاريخية.
4. احتفظ باختبارات migration/history منفصلة عندما تكون القيمة القديمة لازمة للتوافق التاريخي.
5. سجل الحالة في STATUS/progress/checkpoint/gap overlay.

إذا لم يوجد قرار يحسم أثرًا أكاديميًا/بيانيًا/أمنيًا حقيقيًا، لا تخترع اعتمادًا؛ سجّل الحاجة للقرار في موضعها المناسب وتوقف فقط عند boundary التي لا يمكن تنفيذها بأمان.
