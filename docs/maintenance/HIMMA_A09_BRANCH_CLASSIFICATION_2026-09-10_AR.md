# منصة هِمّة — A09 Branch Review & Classification

**التاريخ:** 2026-09-10  
**المرحلة:** A09  
**الحالة:** `COMPLETE — COMPARE ONLY — NO MERGE / NO DELETE`  
**المستودع:** `7eaur/himma-`  
**قاعدة المقارنة:** `audit/comprehensive-repository-review-2026-09-10`  
**HEAD عند بدء A09:** `9d512aa46397591adda332472a1ae5fc328711be`

---

## 1. المنهج

تم جلب قائمة الفروع الفعلية من GitHub ثم تنفيذ compare لكل فرع مقابل فرع المراجعة الحالي. لم يُستخدم اسم الفرع وحده للحكم. التصنيف يعتمد على:

- `ahead_by / behind_by` والـmerge base.
- الملفات الفريدة عندما يكون الفرع diverged.
- ما إذا كانت التغييرات موجودة أصلًا داخل الفرع الحالي.
- ما إذا كانت التغييرات تاريخية/توثيقية فقط.
- تعارضها مع القرارات الحالية: Canonical 125، no Docker، no temporary audio skip، عدم اعتماد Production ASR provider، وعدم Merge أثناء التدقيق.

التصنيفات المستخدمة:

- `already-contained`: لا commits فريدة أمام فرع المراجعة؛ محتواه داخل التاريخ الحالي.
- `unique-relevant`: يحتوي مادة فريدة قد تستحق نقلًا انتقائيًا بعد فهمها.
- `obsolete`: فريد لكنه يعكس عقدًا/حالة superseded.
- `experimental`: تجربة غير معتمدة للإنتاج.
- `archive-candidate`: لا ينبغي دمجه؛ يمكن أرشفته/حذفه لاحقًا فقط بعد اعتماد خطة cleanup.

---

## 2. قائمة الفروع الكاملة وقرار A09

| الفرع | HEAD | Compare مقابل audit | التصنيف | قرار الدمج |
|---|---|---|---|---|
| `audit/comprehensive-repository-review-2026-09-10` | current | base | ACTIVE AUDIT | لا Merge الآن؛ هو سطح التدقيق الحالي |
| `audit-comprehensive-2026-09-10` | `7cb2192...` | ahead 0 / behind 20 | already-contained + archive-candidate | لا حاجة للدمج |
| `integration/canonical-content-2026-09-08` | `7cb2192...` | ahead 0 / behind 20 | already-contained / pre-audit execution truth | لا حاجة للدمج إلى audit؛ يبقى مرجع التنفيذ قبل التدقيق |
| `integration/official-content-reconciliation-2026-09-08` | `e27e20d...` | ahead 0 / behind 179 | already-contained + archive-candidate | لا Merge |
| `recovery/ui-media-admin-overhaul` | `e1cb0bb...` | ahead 0 / behind 182 | already-contained + historical | لا Merge |
| `b01/content-source-of-truth` | `26d25e0...` | ahead 0 / behind 742 | already-contained + archive-candidate | لا Merge |
| `b02/stage2-closure` | `99a6dbd...` | ahead 0 / behind 711 | already-contained + archive-candidate | لا Merge |
| `b02/student-assessment-lifecycle` | `6a52938...` | ahead 0 / behind 738 | already-contained + archive-candidate | لا Merge |
| `b03/adaptive-learning-engine` | `53666a0...` | ahead 0 / behind 687 | already-contained + archive-candidate | لا Merge |
| `recovery/codex-baseline` | `e5fafe7...` | ahead 0 / behind 744 | already-contained + historical baseline | لا Merge |
| `recovery/p02-baseline` | `41bc2af...` | ahead 0 / behind 759 | already-contained + historical baseline | لا Merge |
| `stage/02-content` | `2626168...` | ahead 0 / behind 762 | already-contained + archive-candidate | لا Merge |
| `stage/03-design-routes` | `974598c...` | ahead 0 / behind 753 | already-contained + archive-candidate | لا Merge |
| `stage/04-production-slice` | `aa89aa8...` | ahead 0 / behind 749 | already-contained + historical client baseline | لا Merge |
| `b04/asr-pipeline` | `46eb03c...` | diverged: ahead 3 / behind 672 | obsolete unique docs + archive-candidate | لا Merge؛ فريدُه توثيق Status/Resume/Progress تاريخي فقط |
| `deployment/platform-sandbox` | `4468575...` | diverged: ahead 9 / behind 329 | experimental + obsolete deployment reference + archive-candidate | لا Merge؛ راجع فقط كمرجع A11 |
| `m08/speech-lab-google-stt` | `85d9311...` | diverged: ahead 9 / behind 439 | experimental | **EXCLUDE FROM MERGE** |
| `b08/speech-lab-google-stt` | `4603d16...` | diverged: ahead 29 / behind 439 | experimental + research reference | **EXCLUDE FROM MERGE** |
| `b08/arabic-pronunciation-lab` | `4290ba9...` | diverged: ahead 42 / behind 439 | experimental + research reference | **EXCLUDE FROM MERGE** |
| `b08/acoustic-pronunciation-evidence` | `a144a71...` | diverged: ahead 48 / behind 439 | experimental + unique-relevant research reference | **EXCLUDE FROM MERGE** |

إجمالي الفروع المرصودة في GitHub أثناء A09: **20 فرعًا بما فيها فرع المراجعة الحالي**.

---

## 3. الفروع contained بالكامل

كل فرع ظهر `ahead_by=0` بالنسبة لفرع المراجعة لا يحمل commits فريدة يجب نقلها. هذا يشمل مراحل B01/B02/B03، فروع Recovery الأساسية، Stage 02/03/04، reconciliation السابق، و`integration/canonical-content-2026-09-08` نفسه.

النتيجة الهندسية: **لا يوجد مبرر Cherry-pick أو Merge لهذه الفروع**. حذفها/أرشفتها قرار Cleanup لاحق فقط، بعد Final branch creation والنسخ الاحتياطي، وليس أثناء A09.

---

## 4. `b04/asr-pipeline`

هذا الفرع diverged لكنه يملك فقط 3 commits فريدة مقارنة بالمسار الحالي، والفرق الظاهر محصور في:

- `docs/ops/RESUME_HERE.md`
- `docs/ops/STATUS.md`
- `docs/ops/progress.json`

لا توجد شفرة ASR فريدة أمام الحالة الحالية في compare. لذلك الاسم لا يعني وجود implementation مفقود. التغييرات الفريدة هي حالة تشغيلية تاريخية superseded بواسطة handoff/audit الحالي.

**التصنيف:** `obsolete + archive-candidate`، لا Merge.

---

## 5. فروع Speech/Pronunciation Lab

الفروع الأربعة التالية تحمل شفرة فريدة فعلًا:

- `m08/speech-lab-google-stt`
- `b08/speech-lab-google-stt`
- `b08/arabic-pronunciation-lab`
- `b08/acoustic-pronunciation-evidence`

الـcompare أثبت وجود إضافات من نوع:

- Google/Azure speech providers.
- Admin speech-lab UI.
- Arabic pronunciation helpers.
- pronunciation evidence/quality modules.
- تغييرات `speech_provider.py` و`speech_pipeline.py`.
- اختبارات وتجارب E2E خاصة بالـspeech lab.

والفروع ليست خطًا واحدًا نظيفًا نهائيًا: مثلًا `b08/acoustic-pronunciation-evidence` diverged عن `b08/speech-lab-google-stt` و`b08/arabic-pronunciation-lab`، أي أن النقل الأعمى سيفقد/يخلط قرارات متنافسة.

الأهم أن قرار المشروع الحالي ما زال: **لا Production ASR Provider معتمد**، وmachine confidence ليس حقيقة أكاديمية قبل calibration/approval. لذلك لا يجوز اعتبار وجود provider code في فرع تجريبي اعتمادًا تقنيًا أو أكاديميًا.

### الحكم

- جميع Speech Lab branches: `experimental` و**مستبعدة من الدمج الحالي**.
- `b08/acoustic-pronunciation-evidence` يحمل أفكارًا unique-relevant يمكن الرجوع إليها بحثيًا عند اتخاذ قرار Production ASR مستقل، لكن **لا Cherry-pick الآن**.
- أي فرع صوت اصطناعي/تجريبي مؤقت يقع تحت القاعدة نفسها: **EXCLUDE FROM MERGE حتى اعتماد مستقل صريح**.

---

## 6. `deployment/platform-sandbox`

الفرع يحمل 9 commits فريدة ومواد deployment حقيقية، منها:

- `DEPLOYMENT_ARCHITECTURE.md`
- `DEPLOYMENT_STATUS.md`
- `ENVIRONMENT_VARIABLES.md`
- workflow sandbox
- `.env.production` للويب
- `deploy/railway-api.Dockerfile`

لكنها تعكس تجربة نشر قديمة:

- Vercel frontend + Railway API + Supabase DB/Storage.
- تعتمد Dockerfile، بينما القرار الحالي **NO Docker**.
- الوثائق تذكر `HIMMA_TEMP_AUDIO_SKIP=true` للـsandbox، وهذا bypass أزيل من العقد الحالي ولا يجوز إحياؤه.
- تستخدم architecture متعددة المنصات بينما A11 الحالي يستهدف إعداد Railway النهائي بعد إغلاق الإصلاحات والبوابات.

### الحكم

`experimental + obsolete deployment reference + archive-candidate`.

يمكن الاستفادة في A11 فقط من الأفكار العامة غير المتعارضة مثل قائمة متغيرات البيئة، readiness، rollback وفصل secrets، لكن لا يُدمج الفرع ولا يُعاد استخدام Docker/Temporary Audio Skip.

---

## 7. قرار الدمج النهائي من A09

**لا يوجد أي فرع يجب دمجه الآن.**

- الفروع القديمة: contained أصلًا.
- `b04/asr-pipeline`: فريدُه توثيق تاريخي فقط.
- deployment sandbox: متعارض مع قرارات deployment الحالية جزئيًا وتجريبي.
- Speech/Pronunciation branches: تجريبية وغير معتمدة، ومستبعدة صراحة.

هذا يمنع أخطر سيناريو كان محتملًا: إعادة إدخال patches/overlays/providers/bypasses قديمة إلى المستودع الرسمي فقط لأن أسماء فروعها تبدو مهمة.

---

## 8. ما بعد A09

بإغلاق A09 تكون مراحل التدقيق A00–A09 قد وصلت إلى نقطة تسمح ببناء **Master Gap Register** قبل أي إصلاح. الخطوة التالية ليست Merge، بل:

1. تجميع جميع الفجوات من A01–A09 في سجل واحد.
2. ربط كل فجوة بالمالك الصحيح للحقيقة والسبب الجذري.
3. إزالة التكرار بين findings التي تصف السبب نفسه.
4. ترتيبها إلى Execution Waves لـA10.
5. بعد A10 فقط تشغيل Final Gates على exact SHA.
6. بعد Green حقيقي فقط يبدأ A11 Railway finalization.

**A09 CLOSED — NO MERGE PERFORMED.**
