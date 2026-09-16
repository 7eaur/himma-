# هِمّة — A10 / W4 — AUD-MEDIA-002 Gate Checkpoint

**التاريخ:** 2026-09-16  
**الحالة:** `IMPLEMENTED — EXACT-SHA QUALITY GATE FAILED — NOT CLOSED`  
**Gap:** `AUD-MEDIA-002`  
**Repository:** `7eaur/himma-`  
**Execution branch:** `audit/comprehensive-repository-review-2026-09-10`  
**CI helper branch:** `stage/a10-w4-ci`

## لماذا هذا الملف مهم

هذا checkpoint يمنع أي محادثة لاحقة من تفسير تنفيذ `AUD-MEDIA-002` على أنه إغلاق ناجح. التنفيذ موجود، والقرار الأكاديمي معتمد، لكن Quality Gate الأخير فشل في **اختبار قديم واحد** لا يزال يطلب دلالة Sep-08 التاريخية. لذلك لا يجوز إعلان W4 Green حتى إصلاح ملكية الحقيقة وتشغيل Gate جديد على SHA دقيق.

## القرار الأكاديمي المعتمد

المرجع: `docs/ops/HIMMA_W4_OWNER_CLIENT_APPROVAL_2026-09-14.md`.

القرار المعتمد الذي لا يُطلب من العميل مرة أخرى:

- `lexical_stimulus` = صورة تمثل معنى الكلمة المستهدفة مباشرة.
- `story_context` = صورة سياقية/مساندة وليست محفزًا لفظيًا مباشرًا.
- `L2-CORE-09 / R03`، كلمة `سَمَك` تستخدم الأصل `VOC-05`، وتمثيله المباشر سمكة.
- `L2-CORE-09 / R05`، كلمة `نُور` تستخدم الأصل `VOC-15`، وتمثيله المباشر مصباح/ضوء.

## ما تم تنفيذه

### 1. عقد دلالي صريح

أضيف:

`services/api/w4_media_semantics.py`

ويحتوي عقدًا محدودًا مقصودًا لحالتي القرار فقط:

- `L2-CORE-09/R03` → `VOC-05` → `سَمَك` → `lexical_stimulus`
- `L2-CORE-09/R05` → `VOC-15` → `نُور` → `lexical_stimulus`

لا يغير هذا العقد بقية جولات L2-CORE-09 ولا أي media أخرى.

### 2. التطبيق قبل البصمة الكانونية

تم تحديث:

`services/api/canonical_release.py`

بحيث يطبق semantic authority الجديدة **قبل حساب canonical release hash** وقبل publication. هذا يمنع وجود release hash لبيانات ثم تعديلها بعد التوقيع/البصمة.

### 3. Fail-Closed على هوية الأصل

العقد لا يغيّر `usage` بشكل أعمى. قبل الترقية إلى `lexical_stimulus` يشترط:

- وجود الجولة المستهدفة.
- وجود صورة واحدة فقط في الجولة.
- أن تكون هوية الصورة بالضبط الأصل المعتمد.

إذا تم تبديل الصورة لاحقًا، لا يسمح النظام بإعادة وسم أصل خاطئ كأنه approved lexical stimulus.

### 4. Manifest semantics

يتم التحقق من `assets/education/developer/asset-map.json`:

- `VOC-05` يجب أن يبقى label الخاص به `سمكة`.
- `VOC-15` يجب أن يبقى label الخاص به `مصباح أو ضوء`.

### 5. اختبارات regression جديدة

أضيف:

`services/api/test_w4_lexical_media_semantics.py`

وفي Quality Gate #857 نجحت الاختبارات الجديدة الأربعة:

- final release emits exact direct lexical stimulus contract.
- source asset swap cannot be relabelled as approved lexical stimulus.
- role swap back to generic context is rejected.
- light identity is not confused with the tree asset.

## سلسلة commits التنفيذية

- `0e3d99da5b58b7896ecc70fdf27daa62c1f6669e` — `fix(w4): encode approved lexical media semantics`
- `668030cd6656d586206644256187238186ea68ed` — `fix(w4): apply lexical semantics before canonical hash`
- `43118993b4b2b22c1b1362d49a318102fdfb6bf2` — `fix(w4): fail closed on lexical media identity and role`
- `e642aa4b27974c2ec11970fa768f58195188f3f1` — `test(w4): lock lexical stimulus identity and role`

**آخر code candidate SHA:** `e642aa4b27974c2ec11970fa768f58195188f3f1`.

## نتيجة Quality Gate #857

- Workflow: `Himma CI — Quality Gate`
- Run: `#857`
- Run ID: `35040922310`
- Head SHA: `e642aa4b27974c2ec11970fa768f58195188f3f1`
- Conclusion: `FAILURE`

### ما نجح

Frontend = SUCCESS:
- install
- TypeScript
- ESLint
- unit tests
- Next.js build

Security = SUCCESS:
- Python dependency audit
- frontend dependency audit
- secret scan
- unfinished-placeholder guard
- disabled/skipped-test guard

Backend قبل pytest = SUCCESS:
- native PostgreSQL
- catalog validation
- canonical release validation: 125 items + media verified
- Alembic upgrade → downgrade → upgrade
- model drift check
- canonical seed idempotency

Canonical publication على هذا SHA أثبتت:

- 125 items
- 30 Pretest
- 30 Posttest
- 30 Core
- 35 Reinforcement
- 44 skills
- 358 steps
- 824 options
- 265 asset links
- Release SHA256: `d23153f45fd8ad5ad6d5eed234d515dc8ec53e0b51c514506619a842277bc1cc`
- Projection SHA256: `a9a2873307e9bebc24680edaaaf5250d98cca1f84c15a93f9538878a371cd3f3`

### الفشل الوحيد

Pytest:

`1 failed, 866 passed`

الاختبار الوحيد الفاشل:

`test_sep8_approval_projection.py::test_every_declared_image_relationship_is_semantic_and_exact`

الموقع:

`L2-CORE-09 / R03`

Actual الحالي الصحيح وفق قرار 2026-09-14:

`('VOC-05', 'image', 'lexical_stimulus', 'سَمَك')`

Expected القديم من `STEP_MEDIA` داخل `content_approval_contract_2026_09_08.py`:

`('VOC-05', 'image', 'context', 'سمك')`

وبسبب فشل Backend تم Skip لـIntegration؛ لذلك لا يوجد Playwright exact-SHA Green على candidate #857.

## Root Cause

المشكلة ليست أن تنفيذ lexical stimulus خاطئ. المشكلة أن لدينا **سلطتين زمنيتين غير موحدتين في الاختبارات**:

1. عقد Sep-08 القديم في `content_approval_contract_2026_09_08.py` ما يزال يقول `context` في `STEP_MEDIA`.
2. قرار Owner/Client الأحدث بتاريخ 2026-09-14، المطبق في `w4_media_semantics.py`، يقول `lexical_stimulus` للحالتين المعتمدتين.
3. `test_sep8_approval_projection.py` يتعامل مع `STEP_MEDIA` التاريخي على أنه الحقيقة النهائية دون استثناء/تركيب مع authority الأحدث.

إذن المطلوب **توحيد ملكية الحقيقة**، لا التراجع عن القرار الأحدث ولا تعطيل الاختبار.

## أول مهمة للمحادثة التالية

ابدأ من هذه المشكلة فقط قبل W5:

1. Fetch للـlive HEAD على `audit/comprehensive-repository-review-2026-09-10` ولا تفترض أن SHA المحفوظ ما زال HEAD بعد commits التوثيق.
2. اقرأ:
   - `services/api/content_approval_contract_2026_09_08.py`
   - `services/api/w4_media_semantics.py`
   - `services/api/canonical_release.py`
   - `services/api/test_sep8_approval_projection.py`
   - `services/api/test_w4_lexical_media_semantics.py`
   - `docs/ops/HIMMA_W4_OWNER_CLIENT_APPROVAL_2026-09-14.md`
3. أصلح Root Cause بحيث يظل التاريخ محفوظًا لكن اختبار الـfinal release يقارن مع **الحقيقة الحالية المركبة/الأحدث**.
4. لا تغيّر المنتج إلى `context` فقط لإرضاء الاختبار القديم.
5. لا skip/xpass ولا حذف للاختبار.
6. لا تغيّر R01/R02/R04 بدون evidence/approval؛ implementation الحالي مقصود أن يغير R03/R05 فقط.
7. بعد الإصلاح، حرّك `stage/a10-w4-ci` fast-forward إلى exact audit HEAD الجديد.
8. تحقق أن Quality Gate `head_sha` يساوي SHA المرشح.
9. لا تغلق `AUD-MEDIA-002` أو W4 إلا إذا نجح Backend + Security + Frontend + Integration/Playwright كلها على نفس SHA.
10. بعدها فقط حدّث STATUS/progress/checkpoint إلى `W4 GREEN` وابدأ W5.

## الممنوع

- لا W5 قبل W4 Green.
- لا تضعف الاختبارات.
- لا runtime repair/overlay جديد كترقيع.
- لا تعديل عشوائي للصور.
- لا حذف History.
- لا Docker.
- لا Merge أو Deploy أو Railway.
- لا fake ASR ولا Temporary Audio Skip.
- لا ادعاء PASS قبل exact-SHA evidence.
