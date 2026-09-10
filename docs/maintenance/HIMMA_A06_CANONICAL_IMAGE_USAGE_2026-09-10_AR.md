# هِمّة — A06 Canonical Image Usage Audit

- Canonical release: `HIMMA-CONTENT-APPROVAL-2026-09-08`
- Canonical items: **125**
- Known image IDs (kit + generated): **71**
- Image IDs referenced by canonical release: **48**
- Original kit IDs not referenced by canonical release: **23**
- Referenced image IDs absent from known maps: **0**
- Image IDs used with more than one non-empty semantic label: **18**

## 1. Usage by asset

| asset | source/category | approved label | use count | runtime semantics | locations |
|---|---|---|---:|---|---|
| `HIMMA-GEN-SEQ-001` | generated_sequence/generated_sequence | غسل اليدين | 1 | غسل اليدين ×1 | `L1-REIN-12/R01` |
| `HIMMA-GEN-SEQ-002` | generated_sequence/generated_sequence | الأكل | 1 | الأكل ×1 | `L1-REIN-12/R01` |
| `HIMMA-GEN-SEQ-003` | generated_sequence/generated_sequence | فتح الكتاب | 1 | فتح الكتاب ×1 | `L1-REIN-12/R03` |
| `HIMMA-GEN-SEQ-004` | generated_sequence/generated_sequence | سقي الزهرة | 1 | سقي الزهرة ×1 | `L1-REIN-12/R04` |
| `HIMMA-GEN-SEQ-005` | generated_sequence/generated_sequence | لبس الحذاء | 1 | لبس الحذاء ×1 | `L1-REIN-12/R05` |
| `HIMMA-GEN-SEQ-006` | generated_sequence/generated_sequence | الخروج من المنزل | 1 | الخروج من المنزل ×1 | `L1-REIN-12/R05` |
| `HIMMA-GEN-SEQ-007` | generated_sequence/generated_sequence | دخول المكتبة | 1 | دخول المكتبة ×1 | `L3-REIN-10/R03` |
| `HIMMA-GEN-SEQ-008` | generated_sequence/generated_sequence | الذهاب إلى الشاطئ | 1 | ذهب ×1 | `L3-REIN-10/R04` |
| `HIMMA-GEN-SEQ-009` | generated_sequence/generated_sequence | اللعب بالرمل | 1 | لعب ×1 | `L3-REIN-10/R04` |
| `HIMMA-GEN-SEQ-010` | generated_sequence/generated_sequence | تنظيف المكان | 1 | نظف ×1 | `L3-REIN-10/R04` |
| `HIMMA-GEN-VOC-001` | generated_vocabulary/generated_vocabulary | بيت | 1 | بيت ×1 | `PRE-Q17/R01` |
| `SEN-01` | kit/sentences | سالم يقرأ كتابًا | 1 | سالم يقرأ كتابًا ×1 | `L2-CORE-10/R01` |
| `SEN-02` | kit/sentences | مريم تشرب الحليب | 1 | مريم تشرب الحليب ×1 | `L2-CORE-10/R02` |
| `SEN-03` | kit/sentences | عصفور فوق نخلة | 1 | عصفور فوق نخلة ×1 | `L2-CORE-10/R03` |
| `SEN-04` | kit/sentences | هند تضع القلم في الحقيبة | 1 | هند تضع القلم في الحقيبة ×1 | `L2-CORE-10/R04` |
| `SEN-05` | kit/sentences | ماجد يلعب بالكرة | 1 | ماجد يلعب بالكرة ×1 | `L2-CORE-10/R05` |
| `SEN-06` | kit/sentences | سالم ذاهب إلى المدرسة | 1 | سالم ذاهب إلى المدرسة ×1 | `L3-CORE-03/R01` |
| `SEN-07` | kit/sentences | مريم تجلس تحت الشجرة | 1 | مريم تحت الشجرة ×1 | `L3-CORE-03/R02` |
| `SEN-08` | kit/sentences | خالد يقرأ كتابًا مفيدًا | 1 | خالد يقرأ كتابًا مفيدًا ×1 | `L3-CORE-03/R03` |
| `SEN-09` | kit/sentences | أطفال يلعبون في الساحة | 1 | أطفال يلعبون في الساحة ×1 | `L3-CORE-03/R04` |
| `SEN-10` | kit/sentences | أسرة تعود إلى البيت | 1 | أسرة تعود إلى البيت ×1 | `L3-CORE-03/R05` |
| `SEQ-01` | kit/sequences | زرع البذرة | 4 | زرع البذرة ×3; زرعت البذرة ×1 | `PRE-Q10/R01`<br>`L1-CORE-10/R01`<br>`L1-REIN-12/R02`<br>`L3-REIN-10/R02` |
| `SEQ-02` | kit/sequences | سقي البذرة | 3 | سقي البذرة ×2; سقتها ×1 | `PRE-Q10/R01`<br>`L1-CORE-10/R01`<br>`L3-REIN-10/R02` |
| `SEQ-03` | kit/sequences | نمو الزهرة | 4 | نمو الزهرة ×3; ظهور النبتة ×1 | `PRE-Q10/R01`<br>`L1-CORE-10/R01`<br>`L1-REIN-12/R02`<br>`L1-REIN-12/R04` |
| `SEQ-04` | kit/sequences | غسل التفاحة | 2 | غسل التفاحة ×1; غسلت ×1 | `L1-CORE-10/R02`<br>`L3-REIN-10/R05` |
| `SEQ-05` | kit/sequences | تقطيع التفاحة | 2 | تقطيع التفاحة ×1; قطعت ×1 | `L1-CORE-10/R02`<br>`L3-REIN-10/R05` |
| `SEQ-06` | kit/sequences | أكل التفاحة | 2 | أكل التفاحة ×1; أكلت ×1 | `L1-CORE-10/R02`<br>`L3-REIN-10/R05` |
| `SEQ-07` | kit/sequences | إخراج الكتاب | 3 | إخراج الكتاب ×2; أخذ الكتاب ×1 | `L1-CORE-10/R03`<br>`L3-REIN-10/R01`<br>`POST-Q10/R01` |
| `SEQ-08` | kit/sequences | قراءة الكتاب | 5 | قراءة الكتاب ×2; القراءة ×2; قرأ الكتاب ×1 | `L1-CORE-10/R03`<br>`L1-REIN-12/R03`<br>`L3-REIN-10/R01`<br>`L3-REIN-10/R03`<br>`POST-Q10/R01` |
| `SEQ-09` | kit/sequences | إعادة الكتاب | 3 | إعادة الكتاب ×3 | `L1-CORE-10/R03`<br>`L3-REIN-10/R03`<br>`POST-Q10/R01` |
| `STY-01` | kit/stories | نص الاختبار القبلي | 1 | نص الاختبار القبلي ×1 | `PRE-Q24/ITEM` |
| `STY-02` | kit/stories | مريم والبذرة | 4 | مريم والبذرة ×3; البذرة ×1 | `L3-CORE-04/ITEM`<br>`L3-CORE-04/R01`<br>`L3-CORE-10/R02`<br>`L3-REIN-05/R03` |
| `STY-03` | kit/stories | خالد في المكتبة | 4 | خالد في المكتبة ×3; المكتبة ×1 | `L3-CORE-06/ITEM`<br>`L3-CORE-06/R01`<br>`L3-CORE-10/R01`<br>`L3-REIN-05/R01` |
| `STY-04` | kit/stories | رحلة الوادي | 1 | رحلة الوادي ×1 | `L3-CORE-10/R03` |
| `STY-05` | kit/stories | نص الاختبار البعدي | 2 | الشاطئ ×1; نص الاختبار البعدي ×1 | `L3-REIN-05/R02`<br>`POST-Q24/ITEM` |
| `STY-06` | kit/stories | هند والزهرة | 2 | هند والزهرة ×2 | `L3-REIN-04/ITEM`<br>`L3-REIN-04/R01` |
| `VOC-01` | kit/vocabulary | موزة | 9 | موزة ×9 | `PRE-Q05/R01`<br>`L1-CORE-04/R01`<br>`L1-CORE-04/R03`<br>`L1-CORE-04/R04`<br>`L1-CORE-08/R03`<br>`L1-REIN-02/R01`<br>`L1-REIN-02/R04`<br>`L1-REIN-10/R03`<br>`POST-Q05/R01` |
| `VOC-02` | kit/vocabulary | كتاب | 10 | كتاب ×7; كِتَاب ×3 | `PRE-Q05/R01`<br>`L1-CORE-04/R01`<br>`L1-CORE-04/R04`<br>`L1-CORE-08/R03`<br>`L2-CORE-09/R04`<br>`L1-REIN-02/R01`<br>`L1-REIN-10/R03`<br>`L2-REIN-04/R03`<br>`L2-REIN-04/R04`<br>`L2-REIN-04/R05` |
| `VOC-03` | kit/vocabulary | باب | 19 | باب ×16; بَاب ×3 | `PRE-Q05/R01`<br>`PRE-Q14/R01`<br>`L1-CORE-04/R01`<br>`L1-CORE-04/R02`<br>`L1-CORE-04/R03`<br>`L1-CORE-04/R05`<br>`L1-CORE-08/R01`<br>`L2-CORE-09/R01`<br>`L1-REIN-02/R02`<br>`L1-REIN-02/R05`<br>`L1-REIN-03/R01`<br>`L1-REIN-03/R04`<br>`L1-REIN-03/R05`<br>`L1-REIN-10/R02`<br>`L2-REIN-04/R01`<br>`L2-REIN-04/R04`<br>`L2-REIN-04/R05`<br>`POST-Q05/R01`<br>`POST-Q17/R01` |
| `VOC-04` | kit/vocabulary | قلم | 17 | قلم ×14; قَلَم ×3 | `PRE-Q05/R01`<br>`L1-CORE-04/R01`<br>`L1-CORE-04/R02`<br>`L1-CORE-04/R03`<br>`L1-CORE-04/R04`<br>`L1-CORE-08/R01`<br>`L2-CORE-09/R02`<br>`L1-REIN-02/R02`<br>`L1-REIN-02/R04`<br>`L1-REIN-03/R01`<br>`L1-REIN-03/R02`<br>`L1-REIN-03/R05`<br>`L1-REIN-10/R01`<br>`L2-REIN-04/R01`<br>`L2-REIN-04/R02`<br>`L2-REIN-04/R05`<br>`POST-Q05/R01` |
| `VOC-05` | kit/vocabulary | سمكة | 9 | سمكة ×8; سمك ×1 | `L1-CORE-04/R02`<br>`L1-CORE-04/R03`<br>`L1-CORE-08/R02`<br>`L2-CORE-09/R03`<br>`L1-REIN-02/R03`<br>`L1-REIN-03/R02`<br>`L1-REIN-03/R03`<br>`L1-REIN-03/R04`<br>`L1-REIN-10/R04` |
| `VOC-06` | kit/vocabulary | شمس | 12 | شمس ×7; شَمْس ×3; الشمس ×2 | `PRE-Q17/R01`<br>`L1-CORE-04/R05`<br>`L1-CORE-08/R02`<br>`L1-REIN-03/R01`<br>`L1-REIN-03/R02`<br>`L1-REIN-03/R03`<br>`L1-REIN-10/R02`<br>`L2-REIN-04/R01`<br>`L2-REIN-04/R02`<br>`L2-REIN-04/R03`<br>`POST-Q05/R01`<br>`POST-Q17/R01` |
| `VOC-07` | kit/vocabulary | قمر | 4 | القمر ×2; قمر ×2 | `PRE-Q17/R01`<br>`L1-CORE-08/R03`<br>`L1-REIN-10/R05`<br>`POST-Q17/R01` |
| `VOC-08` | kit/vocabulary | شجرة | 1 | الشجرة ×1 | `PRE-Q17/R01` |
| `VOC-09` | kit/vocabulary | نخلة | 9 | نخلة ×8; النخلة ×1 | `L1-CORE-04/R02`<br>`L1-CORE-04/R04`<br>`L1-CORE-04/R05`<br>`L1-CORE-08/R02`<br>`L1-REIN-02/R03`<br>`L1-REIN-02/R05`<br>`L1-REIN-10/R04`<br>`POST-Q14/R01`<br>`POST-Q17/R01` |
| `VOC-10` | kit/vocabulary | كرة | 7 | كرة ×7 | `L1-CORE-04/R05`<br>`L1-CORE-08/R01`<br>`L1-REIN-03/R03`<br>`L1-REIN-03/R04`<br>`L1-REIN-03/R05`<br>`L1-REIN-10/R01`<br>`L1-REIN-10/R05` |
| `VOC-15` | kit/vocabulary | مصباح أو ضوء | 1 | نور ×1 | `L2-CORE-09/R05` |
| `VOC-16` | kit/vocabulary | قطة | 3 | قِطَّة ×3 | `L2-REIN-04/R02`<br>`L2-REIN-04/R03`<br>`L2-REIN-04/R04` |

## 2. Original approved kit images currently unused by canonical content

- `VOC-11` — **كوب ماء** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-11-glass-of-water-512.webp`
- `VOC-12` — **بطة** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-12-duck-512.webp`
- `VOC-13` — **سيارة** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-13-car-512.webp`
- `VOC-14` — **نجم** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-14-star-512.webp`
- `VOC-17` — **حقيبة** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-17-school-bag-512.webp`
- `VOC-18` — **مدرسة** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-18-school-512.webp`
- `VOC-19` — **معلم** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-19-teacher-512.webp`
- `VOC-20` — **عصفور** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-20-bird-512.webp`
- `VOC-21` — **حديقة** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-21-garden-512.webp`
- `VOC-22` — **مكتبة** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-22-library-512.webp`
- `VOC-23` — **شاطئ** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-23-beach-512.webp`
- `VOC-24` — **بحر** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-24-sea-512.webp`
- `VOC-25` — **رمل** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-25-sand-512.webp`
- `VOC-26` — **أصداف** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-26-shells-512.webp`
- `VOC-27` — **سلة طعام** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-27-food-basket-512.webp`
- `VOC-28` — **زهرة** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-28-flower-512.webp`
- `VOC-29` — **بذرة** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-29-seed-512.webp`
- `VOC-30` — **أوراق شجر** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-30-leaves-512.webp`
- `VOC-31` — **سحاب** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-31-clouds-512.webp`
- `VOC-32` — **وادٍ** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-32-valley-512.webp`
- `VOC-33` — **أسرة** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-33-family-512.webp`
- `VOC-34` — **طفل** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-34-boy-512.webp`
- `VOC-35` — **طفلة** — category `vocabulary` — `assets/vocabulary/webp/hem-voc-35-girl-512.webp`

## 3. Multi-semantic reuse requiring manual review

- `SEQ-01` / زرع البذرة: `زرع البذرة` ×3, `زرعت البذرة` ×1
- `SEQ-02` / سقي البذرة: `سقي البذرة` ×2, `سقتها` ×1
- `SEQ-03` / نمو الزهرة: `نمو الزهرة` ×3, `ظهور النبتة` ×1
- `SEQ-04` / غسل التفاحة: `غسل التفاحة` ×1, `غسلت` ×1
- `SEQ-05` / تقطيع التفاحة: `تقطيع التفاحة` ×1, `قطعت` ×1
- `SEQ-06` / أكل التفاحة: `أكل التفاحة` ×1, `أكلت` ×1
- `SEQ-07` / إخراج الكتاب: `إخراج الكتاب` ×2, `أخذ الكتاب` ×1
- `SEQ-08` / قراءة الكتاب: `قراءة الكتاب` ×2, `القراءة` ×2, `قرأ الكتاب` ×1
- `STY-02` / مريم والبذرة: `مريم والبذرة` ×3, `البذرة` ×1
- `STY-03` / خالد في المكتبة: `خالد في المكتبة` ×3, `المكتبة` ×1
- `STY-05` / نص الاختبار البعدي: `الشاطئ` ×1, `نص الاختبار البعدي` ×1
- `VOC-02` / كتاب: `كتاب` ×7, `كِتَاب` ×3
- `VOC-03` / باب: `باب` ×16, `بَاب` ×3
- `VOC-04` / قلم: `قلم` ×14, `قَلَم` ×3
- `VOC-05` / سمكة: `سمكة` ×8, `سمك` ×1
- `VOC-06` / شمس: `شمس` ×7, `شَمْس` ×3, `الشمس` ×2
- `VOC-07` / قمر: `القمر` ×2, `قمر` ×2
- `VOC-09` / نخلة: `نخلة` ×8, `النخلة` ×1

## 4. Referenced IDs missing from image maps

- None

## 5. Category coverage

- `generated_sequence`: 10 distinct referenced IDs
- `generated_vocabulary`: 1 distinct referenced IDs
- `sentences`: 10 distinct referenced IDs
- `sequences`: 9 distinct referenced IDs
- `stories`: 6 distinct referenced IDs
- `vocabulary`: 12 distinct referenced IDs

## 6. Interpretation

1. الصورة غير المستخدمة ليست مرشحًا تلقائيًا للاستبدال؛ يلزم تطابق دلالي دقيق مع السؤال/الخيار.
2. تعدد semantic_text لنفس asset قد يكون alias صحيحًا (مثل التصريف أو الاختصار) أو misuse؛ يراجع يدويًا.
3. هذا التقرير مبني على الـcanonical release النهائي، وليس على ملفات legacy seed.
4. الأصول التي لا تظهر هنا قد تكون أصول واجهة/شخصيات وليست محتوى أكاديميًا؛ تفحص في جرد public منفصل.
