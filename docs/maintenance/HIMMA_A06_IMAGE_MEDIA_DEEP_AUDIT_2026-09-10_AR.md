# هِمّة — A06 تدقيق الصور والوسائط العميق

**التاريخ:** 2026-09-10  
**الحالة:** `STATIC/SOURCE AUDIT COMPLETE — NO DELETE — NO REPLACEMENT — NO MERGE — NO DEPLOY`  
**الفرع:** `audit/comprehensive-repository-review-2026-09-10`

---

## 1. نطاق A06 ومصادر الحقيقة

هذه الجولة لم تعِد الجرد من الصفر. بُنيت على:

- `HIMMA_A06_CANONICAL_IMAGE_USAGE_2026-09-10_AR.md`
- `HIMMA_A02_A06_STATIC_INVENTORY_2026-09-10.md`
- canonical release/approval contract الحالي.
- `canonical_media_guard.py` و`content_runtime.py` و`content_student_view.py` و`media.py`.
- manifest الرسمي `assets/education/developer/asset-map.json` وخرائط generated.
- حزمة الصور التعليمية الرسمية المرفقة للمشروع عند الحاجة للمراجعة البصرية.

القاعدة: **عدم الاستخدام لا يعني orphan، وتطابق bytes لا يعني أن حذف URL آمن، والصورة البديلة لا تعتمد لأنها “أجمل” بل فقط إذا كانت أدق دلاليًا للمهمة.**

---

## 2. خط الأساس المثبت

- canonical items: **125**.
- image IDs المعروفة: **71**.
- image IDs المشار إليها من canonical release: **48**.
- original approved kit IDs غير المستخدمة في canonical release: **23**.
- referenced image IDs المفقودة من الخرائط: **0**.
- image IDs لها أكثر من runtime semantic label: **18**.
- `assets/education`: **208 ملفًا**، ولا توجد exact duplicate SHA groups داخله.
- `apps/web/public`: **28 ملفًا**، منها **17** بلا direct textual reference، و**5** exact duplicate SHA groups.

هذه الأرقام تصف الحالة ولا تمنح إذن حذف.

---

## 3. ملكية media الحالية — سليمة في الأساس

### 3.1 Canonical identity لا تعتمد على ترتيب الصور

`content_runtime.step_assets()` يخرج لكل asset:

- stable `asset_id`
- `asset_type`
- `usage`
- `semantic_text`
- URL من الشكل `/api/media/{asset_id}`
- `option_id` للصورة الاختيارية عند وجود mapping صريح

و`content_student_view` يعيد ترتيب choice assets وفق `option_id` عند shuffle، ولا يستخدم موضع الصورة كهوية إجابة.

**الحكم:** هذا contract صحيح ويجب الحفاظ عليه.

### 3.2 Serving مقيد بالmanifest

`media.py` لا يقبل مسار ملف خام من المستخدم. يبني index من audio/image manifests المعتمدة ويخدم `asset_id` فقط. المسار يحبس resolution داخل جذور الأصول.

**الحكم:** owner العام للـserving واضح ومناسب.

### 3.3 Canonical media guard قوي للـchoice media

`canonical_media_guard.py` يفشل عند:

- stable IDs مكررة في الخرائط.
- referenced IDs غير معروفة.
- files مفقودة/فارغة.
- selectable choice image لا تطابق semantic target.
- choice image تحمل embedded answer text.
- audio غير approved أو لا يطابق target.

وهذا أفضل من positional/fuzzy inference ويجب عدم تخفيفه.

---

## 4. تصنيف الـ18 multi-semantic image IDs

### 4.1 `SEQ-01..SEQ-08` — ACCEPTED EXPLICIT ALIASES

الاختلافات التالية ليست misuse مخفيًا؛ هي مسجلة صراحة في `IMAGE_SEMANTIC_ALIASES`:

- `SEQ-01`: زرع البذرة / زرعت البذرة
- `SEQ-02`: سقي البذرة / سقتها
- `SEQ-03`: نمو الزهرة / ظهور النبتة
- `SEQ-04`: غسل التفاحة / غسلت
- `SEQ-05`: تقطيع التفاحة / قطعت
- `SEQ-06`: أكل التفاحة / أكلت
- `SEQ-07`: إخراج الكتاب / أخذ الكتاب
- `SEQ-08`: قراءة الكتاب / القراءة / قرأ الكتاب

**الحكم:** `ACCEPTED`. لا توليد صور جديدة لهذه الاختلافات لمجرد اختلاف الصياغة.

### 4.2 `VOC-02/03/04/06/07/09` — ACCEPTED ORTHOGRAPHIC/ARTICLE VARIANTS

- كتاب / كِتَاب
- باب / بَاب
- قلم / قَلَم
- شمس / شَمْس / الشمس
- قمر / القمر
- نخلة / النخلة

`_image_semantic_key()` يزيل الحركات و`الـ` التعريف للاختيار المرئي؛ هذه variants لا تغيّر الهوية البصرية للمفهوم.

**الحكم:** `ACCEPTED`.

### 4.3 `STY-02/03/05` — ACCEPTED CONTEXT SCENE REUSE مع ملاحظة metadata

الاستخدامات الأوسع مثل:

- `STY-02`: مريم والبذرة / البذرة
- `STY-03`: خالد في المكتبة / المكتبة
- `STY-05`: نص الاختبار البعدي / الشاطئ

هي `usage=context` وليست choice asset تربط إجابة واحدة. في `L3-REIN-05` السؤال هو اختيار عنوان مناسب للصورة، ومشهد القصة الغني أنسب للمهمة من استبداله تلقائيًا بأيقونة مفردة مثل `VOC-22 مكتبة` أو `VOC-23 شاطئ` أو `VOC-29 بذرة`.

**الحكم:** إبقاء المشاهد الحالية مرشح أقوى من الاستبدال التلقائي. لكن manifest labels للقصص تمزج أحيانًا “غرض الأصل في المحتوى” مع “المعنى البصري للمشهد”، لذلك يلزم metadata context semantics أو aliases موثقة إذا أردنا تدقيقًا آليًا أعمق للـcontext.

---

## 5. الفجوة الأكاديمية الأهم: context-image semantics لا تُفحص بدقة

### AUD-MEDIA-002 — Context semantic blind spot

الـguard الحالي يطبق semantic equality الصارمة على `usage == choice` فقط. وهذا قرار مفهوم للمشاهد الواسعة، لكنه يترك مهامًا يكون فيها **context image نفسه هو clue أكاديميًا مباشرًا** بلا فحص lexical مناسب.

أوضح مثال: `L2-CORE-09`.

المهمة الحالية: **«كوّن اسم الصورة من الحروف»**، والتعليمات: **«اضغط الحروف بالترتيب الصحيح حتى تكتمل الكلمة.»**

لكن:

- R03 target/source = `سَمَك: س/م/ك`، والصورة `VOC-05` manifest label = `سمكة`، alt = سمكة واحدة.
- R05 target/source = `نُور: ن/و/ر`، والصورة `VOC-15` manifest label = `مصباح أو ضوء`، والأصل البصري مصباح مضيء.

هذه ليست مثل صورة story context عامة؛ الصورة هنا هي stimulus الذي يُطلب من الطالب استخراج **اسم دقيق** منه. لذلك لا يكفي أن تكون مرتبطة بالمفهوم تقريبًا.

**الحكم:** `P1 — ACADEMIC REVIEW REQUIRED`، وليس حكمًا بأن الصورتين خاطئتان قطعًا. يجب أن يعتمد المسؤول الأكاديمي واحدًا من خيارين لكل جولة:

1. يثبت أن الصورة الحالية تمثل target lexical المطلوب بلا غموض ويضيف context alias/contract صريحًا؛ أو
2. يعتمد أصلًا أدق/يولد أصلًا جديدًا مطابقًا للtarget إذا لم يوجد أصل مناسب.

لا يتم التغيير أثناء A06.

### لماذا لم يمسكه test الحالي؟

`test_canonical_media_guard.py` يثبت semantic protection للـ**choice image** (مثل منع تبديل موزة بكتاب)، لكنه لا يوجد فيه regression يعامل `build_word + image stimulus` كحالة تحتاج lexical semantic contract خاصًا.

**Root fix في A10:** semantic policy بحسب **دور الصورة في المهمة** لا فقط `usage` العام. مثل `choice`, `lexical_stimulus`, `story_context`, `sequence_event`، ولكل دور validation مناسب.

---

## 6. الـ23 approved unused vocabulary assets

الحالة الحالية:

`VOC-11..14`, `VOC-17..35` غير مستخدمة في canonical release، ومنها كوب ماء/بطة/سيارة/نجم/حقيبة/مدرسة/معلم/عصفور/حديقة/مكتبة/شاطئ/بحر/رمل/أصداف/سلة طعام/زهرة/بذرة/أوراق/سحاب/وادٍ/أسرة/طفل/طفلة.

### AUD-MEDIA-003 — Unused approved ≠ orphan

هذه أصول **معتمدة داخل kit**، وليست garbage لمجرد أن الإصدار الحالي لا يشير إليها.

أمثلة تؤكد ضرورة عدم الاستبدال العشوائي:

- `L3-REIN-05` يستخدم story scene للمكتبة/الشاطئ/البذرة؛ استبداله بـ`VOC-22/23/29` سيقلل السياق المطلوب لاختيار “عنوان الصورة”.
- `VOC-17 حقيبة`, `VOC-18 مدرسة`, `VOC-20 عصفور`, `VOC-21 حديقة` قد تكون مفيدة مستقبلًا، لكن وجود الكلمة في نص أو جملة لا يعني أن السؤال يحتاج object image منفصلة.

**الحكم:** الـ23 = `APPROVED UNUSED RESERVE`، وليست deletion candidates حاليًا. إعادة استخدامها في A10 فقط عندما يثبت semantic improvement لموضع محدد.

---

## 7. Public assets والنسخ المكررة

### AUD-MEDIA-004 — خمس مجموعات character binaries متطابقة

ثبت SHA-identical بين:

- `characters/boy-encourage.png` و`characters/boy/encourage.png`
- `characters/boy-explain.png` و`characters/boy/explain.png`
- `characters/boy-success.png` و`characters/boy/success.png`
- `characters/boy-try-again.png` و`characters/boy/try-again.png`
- `characters/boy-welcome.png` و`characters/boy/welcome.png`

النسخ top-level ليس لها direct source refs في الجرد، بينما عدد من nested URLs مستخدم فعليًا.

**Severity:** P2 cleanup/debt، لا user-facing defect مثبت.

**قرار A06:** لا حذف. في A10 يجب عمل URL/dependency scan يشمل dynamic path construction + E2E 404 gate، ثم اختيار canonical nested path وإزالة النسخة الأخرى فقط إن ثبت عدم اعتماد خارجي/داخلي.

### AUD-MEDIA-005 — 17 public files بلا direct textual refs ليست dead-code proof

تضم feedback mp3، `logo-flat.svg`، بعض character states وNext scaffold SVGs.

المرجع النصي المباشر لا يرى dynamic string construction أو URLs محفوظة؛ لذلك:

- feedback audio يحتاج فحص resolver/event mapping قبل الحكم.
- character `try-again` يحتاج فحص dynamic state resolver.
- Next scaffold SVGs أقرب إلى archive candidates لكن لا تحذف في audit.

**الحكم:** `DEPENDENCY REVIEW REQUIRED`, وليس `DELETE`.

---

## 8. فجوة ownership بين validation وserving

### AUD-MEDIA-006 — Runtime media index لا يفشل بذاته عند duplicate ID

`canonical_media_guard` يرفض duplicate image/audio stable IDs، لكن `_build_asset_index()` في `media.py` يستخدم assignment إلى dict؛ duplicate ID لو دخل runtime سيجعل آخر قيمة تفوز صامتًا.

الإصدار الطبيعي يجب أن يمر validation، ولذلك لا نسجل incident حاليًا. لكن runtime owner نفسه ليس fail-closed إذا تم تشغيله/نشره خارج gate.

**Severity:** P2 defense-in-depth.

**Root fix:** استخراج manifest index builder واحد مشترك يرفض duplicate IDs/files invalid عند startup، ويستهلكه guard + serving بدل منطقين مختلفين.

---

## 9. ما لا يحتاج إصلاحًا

- لا missing referenced image IDs في الجرد الحالي.
- لا exact duplicate binaries داخل `assets/education`.
- generated sequence images العشرة وgenerated house لها stable IDs وsemantic mappings، وليست temp placeholders.
- لا حاجة لتوليد صور جديدة فقط لأن asset reused عدة مرات.
- لا حاجة لاستخدام الـ23 unused assets لمجرد “التنويع”.
- story scenes في L3 title-selection لا تستبدل بأيقونات vocabulary أبسط دون سبب أكاديمي.

---

## 10. Master Gap Register — A06

| ID | Severity | Status | Symptom / Evidence | Root cause | Correct owner | Root fix | Required tests | Wave |
|---|---:|---|---|---|---|---|---|---|
| AUD-MEDIA-001 | P2 | VERIFIED BASELINE | 48/71 referenced؛ 23 approved unused | release لا يحتاج كل kit | canonical release + manifest | لا تغيير؛ classify reserve | inventory regression | A10 only if needed |
| AUD-MEDIA-002 | P1 | REVIEW REQUIRED | build-word image stimulus لديه `سمك↔سمكة` و`نور↔مصباح/ضوء` ولا يخضع lexical context validation | validation مبني على `usage=choice` لا الدور الأكاديمي للصورة | media semantic contract + academic content owner | role-aware semantic validation + academic approval/exact asset if needed | L2-CORE-09 round semantic tests + browser visual check | A10/A08 |
| AUD-MEDIA-003 | P2 | ACCEPTED WITH RULE | 23 kit assets غير مستخدمة | kit أوسع من release | manifest/catalog | تبقى approved reserve | unused inventory diff | none unless reused |
| AUD-MEDIA-004 | P2 | VERIFIED | 5 exact duplicate public character groups | historical URL layout copies | frontend asset registry | canonical path after dependency proof | static URL scan + E2E 404 | A10 |
| AUD-MEDIA-005 | P2 | REVIEW REQUIRED | 17 public direct-zero refs | static scan لا يرى dynamic usage | frontend media/character/audio registry | classify each before deletion | runtime path coverage | A10 |
| AUD-MEDIA-006 | P2 | VERIFIED | serving dict can last-write-win duplicate ID؛ guard rejects only in separate gate | duplicated manifest-index logic | shared media manifest service | one fail-closed index builder | duplicate-ID startup/unit test | A10 |
| AUD-MEDIA-007 | — | VERIFIED POSITIVE | learner choice assets aligned by explicit option_id and URLs by stable asset_id | canonical DB runtime | content_runtime/content_student_view | preserve | shuffle/media identity regressions | protect |

---

## 11. بوابات A06 المؤجلة للتنفيذ

قبل Final Release يجب أن يثبت:

- canonical media contract = zero failures.
- كل `/api/media/{referenced_id}` يرجع 200/content-type صحيح.
- no 404 لكل media في full student journey.
- `L2-CORE-09` lexical image targets معتمدة صراحة.
- context scenes لا تستبدل بأصول أقل دلالة.
- public duplicate cleanup — إن نفذ — لا يكسر أي URL.
- character/feedback dynamic paths مغطاة.
- image choice mapping يبقى option-id based بعد shuffle.

---

## 12. قرار إغلاق A06

A06 مغلق كـ **audit-only**.

لا صورة حُذفت، ولا أصل استُبدل، ولا generated asset أُعيد توليده، ولا Production code عُدل.

أخطر بند خرج من الجولة هو `AUD-MEDIA-002`: ليس “نقص صور” عامًا، بل أن عقد validation الحالي لا يميز الصور التي تعمل كـ**lexical stimulus** عن context scenes العامة، ما يسمح بحالات تحتاج مراجعة أكاديمية دقيقة مثل L2-CORE-09.

**نقطة الاستكمال التالية: A07 — Security / Performance / Accessibility / Observability.**
