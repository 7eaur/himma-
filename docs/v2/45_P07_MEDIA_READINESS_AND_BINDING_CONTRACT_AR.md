# هِمّة V2 — جرد P07 النهائي وعقد تبديل الوسائط

**تاريخ الفحص:** 2026-10-24  
**الحالة:** تجهيز P07 برمجيًا وتوثيقيًا بالتوازي مع CI للمرحلة P06، بطلب المالك. **لا يمثل اعتماد P06 أو P07 أو ترخيص نشر الإنتاج.**  
**المصدر:** دمج الميديا من بنوك L1 وL2 وL3 وASSESSMENT الحالية، وليس تعداد الملفات الثنائية وحده.  
**المراجع:** `09_IMPLEMENTATION_ROADMAP_AR.md`، `15_ALL_LESSON_VIDEO_BRIEFS_AR.md`، `16_REQUIRED_IMAGES_AR.md`، `17_REQUIRED_LISTENING_AUDIO_AR.md`، `18_STUDENT_READING_AI_REFERENCE_AR.md`، `41_RECEIVED_AUDIO_AND_SHARED_DEMO_VIDEO_AR.md`.

## 1. ملخص لا يخلط بين وجود الملف واعتماده

| الصنف | معرفات البنك | حالة الأصول |
|---|---:|---|
| فيديو أساسي | 19 | جميع الفيديوهات النهائية الـ19 غير متوفرة؛ يوجد **فيديو معاينة واحد TEST ONLY** يُعرض بدلها دون تغيير الهوية |
| صوت تعليمي | 47 | 33 مرشحًا سابقًا من V1 بحاجة تحكيم سمعي؛ 12 صوتًا جديدًا وصل MP3+WAV ويحتاج مراجعة، وصوتان في المسودة لم يعودا مستخدمين |
| صورة تعليمية | 23 | مرشحات من V1 ذات مسارات معروفة، تتطلب معاينة ومطابقة تربوية/حقوق |
| **الإجمالي** | **89** | **0 جاهز نشرًا، 56 بانتظار المراجعة و33 موصوفة في البنك مفقودة؛ 89 متاحة نظريًا بمعاينات TEST_ONLY في بيئة الاختبار** |

**المطلوب فعليًا للنشر: 73 وسيطًا مستخدمًا** — 19 فيديو و34 صوتًا و20 صورة. **16 عنصرًا غير مستخدم حاليًا** (13 صوتًا و3 صور) موثقة للاحتفاظ بالمصدر، ولا تدخل بوابة نشر الدروس الحالية. الـ12 صوتًا الجديد هي من الوسائط المستخدمة، بينما الصوتان الاختياريان لا يستخدمان.\n\n**مهم:** `missing_new` حالة اعتماد في البنك، وليست حكمًا بأن الملف لا يوجد محليًا. الصوتيات الـ12 موجودة فعليًا لكنها لا تتحول إلى approved دون تحكيم. `VID-L1-xx` تبقى 19 معرّفًا مستقلًا رغم تشغيل نفس MP4 للمعاينة. `AUD-L1-03-MA` و`AUD-L1-03-SI` موجودان فقط في سجل الأصول، لا في الأسئلة الجارية؛ لا تطلب إعادة إنتاجهما بلا قرار تحريري.

## 2. ما نفذناه في P07

- **MediaProvider صار fail-closed:** لا يعتبر المسار جاهزًا لمجرد `status=approved`. يلزم ملف حقيقي تحت `assets/` بمسار لا يخرج من الجذر وبامتداد يتوافق مع نوع الوسيط.
- **مسار approved reusable:** `/v2/content/media/{asset_id}` داخل API (يُعرَض للمتصفح عبر `/api/v2/content/media/{asset_id}`؛ راجع route الفعلي عند الربط)، لا يعيد ملفًا مفقودًا أو `TEST_ONLY`؛ التفعيل النهائي مرهون بإصدار معتمد في P10.
- **جرد admin محسّن:** `/v2/lessons/admin/media-inventory` يعرض معرف الأصل، حالته المرجعية، مسار المرشح إن وجد، نوع الاختبار، `publication_blocker`، وصلة الاستخدام الفعلي بكل درس أو سؤال. `/admin/v2-media` يعرض هذه البيانات.
- **استبدال تجريبي دون تغيير Player:** `services/api/test_fixtures/v2-preview-bindings.json` يسمح بوضع ربط محدد حسب asset_id إلى ملف من `assets/` أو `services/api/test_fixtures/` دون كتابة منطق خاص لكل درس، مع منع المسار غير الآمن، ورفض الملف المفقود بدل الرجوع إلى ملف آخر مضلل.
- تظل وسيطة `TEST ONLY` ويقتصر وصولها على معاينة الطالب المصادق عليها. البوابات الحقيقية للنشر لا تعتمد fixtures.

## 3. مصفوفة الأصول الكاملة (89)

**تنبيه للمراجع:** العمود «النص المرجعي» بيانات تحريرية لمنتج الصوت/المشرف فقط، ولا يعرض مباشرة في سؤال الاستماع للطالب. الاستخدامات تشير إلى معرفات البنك لضمان تبديل الوسيط في جميع مواضعه.

| ID | النوع | حالة التسليم/الاعتماد | المسار الحالي أو المرشح | النص المرجعي | الاستخدامات |
|---|---|---|---|---|---|
| `VID-L1-01` | فيديو | جديد ناقص | — | — | L1-01:video |
| `VID-L1-02` | فيديو | جديد ناقص | — | — | L1-02:video |
| `VID-L1-03` | فيديو | جديد ناقص | — | — | L1-03:video |
| `VID-L1-04` | فيديو | جديد ناقص | — | — | L1-04:video |
| `VID-L1-05` | فيديو | جديد ناقص | — | — | L1-05:video |
| `VID-L1-06` | فيديو | جديد ناقص | — | — | L1-06:video |
| `VID-L2-01` | فيديو | جديد ناقص | — | — | L2-01:video |
| `VID-L2-02` | فيديو | جديد ناقص | — | — | L2-02:video |
| `VID-L2-03` | فيديو | جديد ناقص | — | — | L2-03:video |
| `VID-L2-04` | فيديو | جديد ناقص | — | — | L2-04:video |
| `VID-L2-05` | فيديو | جديد ناقص | — | — | L2-05:video |
| `VID-L2-06` | فيديو | جديد ناقص | — | — | L2-06:video |
| `VID-L3-01` | فيديو | جديد ناقص | — | — | L3-01:video |
| `VID-L3-02` | فيديو | جديد ناقص | — | — | L3-02:video |
| `VID-L3-03` | فيديو | جديد ناقص | — | — | L3-03:video |
| `VID-L3-04` | فيديو | جديد ناقص | — | — | L3-04:video |
| `VID-L3-05` | فيديو | جديد ناقص | — | — | L3-05:video |
| `VID-L3-06` | فيديو | جديد ناقص | — | — | L3-06:video |
| `VID-L3-07` | فيديو | جديد ناقص | — | — | L3-07:video |
| `AUD-L1-03-LI` | صوت | وُرِّد صوت؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V2/web_mp3/AUD-L1-03-LI.mp3` | — | L1-03-IC-A02:stimulus |
| `AUD-L1-03-MA` | صوت | جديد ناقص | — | — | غير مستخدم في أسئلة البنك الحالية |
| `AUD-L1-03-MU` | صوت | وُرِّد صوت؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V2/web_mp3/AUD-L1-03-MU.mp3` | — | SUP-02-GP-03:stimulus |
| `AUD-L1-03-NU` | صوت | وُرِّد صوت؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V2/web_mp3/AUD-L1-03-NU.mp3` | — | L1-03-IC-A01:stimulus |
| `AUD-L1-03-SA` | صوت | وُرِّد صوت؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V2/web_mp3/AUD-L1-03-SA.mp3` | — | L1-03-GP-03:stimulus |
| `AUD-L1-03-SI` | صوت | جديد ناقص | — | — | غير مستخدم في أسئلة البنك الحالية |
| `AUD-L1-L` | صوت | وُرِّد صوت؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V2/web_mp3/AUD-L1-L.mp3` | — | L1-01-GP-04:option |
| `AUD-L1-SAD` | صوت | وُرِّد صوت؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V2/web_mp3/AUD-L1-SAD.mp3` | — | L1-02-GP-03:stimulus، SUP-01-GP-03:stimulus |
| `AUD-L1-TA` | صوت | وُرِّد صوت؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V2/web_mp3/AUD-L1-TA.mp3` | — | L1-02-GP-04:stimulus |
| `AUD-L1-TAA` | صوت | وُرِّد صوت؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V2/web_mp3/AUD-L1-TAA.mp3` | — | L1-02-IC-A04:stimulus، SUP-01-SC-06:stimulus |
| `AUD-L2-RA` | صوت | وُرِّد صوت؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V2/web_mp3/AUD-L2-RA.mp3` | — | L2-02-IC-A04:stimulus |
| `AUD-V2-POST-BUU` | صوت | وُرِّد صوت؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V2/web_mp3/AUD-V2-POST-BUU.mp3` | — | V2-POST-Q13:stimulus |
| `AUD-V2-POST-TI` | صوت | وُرِّد صوت؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V2/web_mp3/AUD-V2-POST-TI.mp3` | — | V2-POST-Q04:stimulus |
| `AUD-V2-SUP-DAD` | صوت | وُرِّد صوت؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V2/web_mp3/AUD-V2-SUP-DAD.mp3` | — | SUP-01-SC-03:stimulus |
| `LET-01` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/LET-01.mp3` | مَ | L1-01-GP-04:option، L1-01-IC-A02:option، L1-01-IC-A04:stimulus |
| `LET-02` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/LET-02.mp3` | بْ | L1-01-GP-01:stimulus، SUP-01-GP-01:stimulus |
| `LET-03` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/LET-03.mp3` | سْ | L1-01-GP-02:option، L1-01-IC-A01:option، L1-01-IC-A02:option، L1-02-IC-A03:stimulus، SUP-01-GP-06:stimulus، V2-PRE-Q03:stimulus |
| `LET-04` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/LET-04.mp3` | قْ | L1-01-GP-02:option، L1-01-IC-A01:option، L1-01-IC-A03:stimulus، SUP-01-SC-04:stimulus، V2-POST-Q03:stimulus |
| `LET-05` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/LET-05.mp3` | رْ | L1-01-GP-02:option، L1-01-GP-04:option، L1-01-IC-A01:option، L1-01-IC-A02:option، SUP-01-SC-01:stimulus |
| `LET-06` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/LET-06.mp3` | نْ | L1-01-GP-03:stimulus، SUP-01-GP-04:stimulus |
| `SYL-01` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/SYL-01.mp3` | بَ | L1-04-IC-A04:stimulus، SUP-02-GP-01:stimulus |
| `SYL-02` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/SYL-02.mp3` | بِ | SUP-02-SC-05:stimulus، V2-PRE-Q04:stimulus |
| `SYL-03` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/SYL-03.mp3` | بُ | L1-03-GP-01:stimulus، SUP-02-SC-01:stimulus |
| `SYL-04` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/SYL-04.mp3` | مَا | L2-02-GP-01:stimulus، SUP-06-GP-01:stimulus |
| `SYL-05` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/SYL-05.mp3` | مِ | L1-04-GP-03:stimulus، SUP-02-GP-05:stimulus، L2-02-GP-02:stimulus |
| `SYL-06` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/SYL-06.mp3` | سُ | L1-04-GP-01:stimulus |
| `SYL-07` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/SYL-07.mp3` | رَ | L1-04-IC-A02:stimulus |
| `SYL-08` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/SYL-08.mp3` | قِ | L1-03-IC-A04:stimulus |
| `SYL-09` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/SYL-09.mp3` | بَا | V2-PRE-Q13:stimulus |
| `SYL-10` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/SYL-10.mp3` | فِي | SUP-06-SC-06:stimulus، V2-PRE-Q21:stimulus |
| `SYL-11` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/SYL-11.mp3` | نُو | L2-02-GP-04:stimulus، SUP-06-GP-03:stimulus |
| `SYL-12` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/SYL-12.mp3` | لِي | L2-02-IC-A02:stimulus، SUP-06-GP-04:stimulus، V2-POST-Q21:stimulus |
| `SYL-13` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/SYL-13.mp3` | سَا | L2-02-IC-A01:stimulus، SUP-06-SC-03:stimulus |
| `WRD-03` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/WRD-03.mp3` | باب | L1-06-GP-02:stimulus |
| `WRD-04` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/WRD-04.mp3` | قَلَم | غير مستخدم في أسئلة البنك الحالية |
| `WRD-05` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/WRD-05.mp3` | سَمَك | غير مستخدم في أسئلة البنك الحالية |
| `WRD-07` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/WRD-07.mp3` | شَمْس | غير مستخدم في أسئلة البنك الحالية |
| `WRD-08` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/WRD-08.mp3` | قَمَر | غير مستخدم في أسئلة البنك الحالية |
| `WRD-09` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/WRD-09.mp3` | نَخْلَة | SUP-04-GP-02:stimulus |
| `WRD-10` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/WRD-10.mp3` | كُرَة | L1-06-IC-A02:stimulus |
| `WRD-14` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/WRD-14.mp3` | نَجْم | غير مستخدم في أسئلة البنك الحالية |
| `WRD-15` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/WRD-15.mp3` | نور | غير مستخدم في أسئلة البنك الحالية |
| `WRD-16` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/WRD-16.mp3` | مَكْتَب | غير مستخدم في أسئلة البنك الحالية |
| `WRD-17` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/WRD-17.mp3` | بَحْر | غير مستخدم في أسئلة البنك الحالية |
| `WRD-18` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/WRD-18.mp3` | أَرْنَب | غير مستخدم في أسئلة البنك الحالية |
| `WRD-23` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/WRD-23.mp3` | فيل | غير مستخدم في أسئلة البنك الحالية |
| `WRD-29` | صوت | مرشح V1؛ مراجعة معلقة | `assets/audio/HIMMA_AUDIO_V1/web_mp3/WRD-29.mp3` | موز | غير مستخدم في أسئلة البنك الحالية |
| `VOC-01` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-01-banana-512.webp` | — | V2-PRE-Q09:option |
| `VOC-02` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-02-book-512.webp` | — | L2-01-GP-03:stimulus |
| `VOC-03` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-03-door-512.webp` | — | L2-01-GP-04:stimulus، V2-PRE-Q09:option |
| `VOC-04` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-04-pencil-512.webp` | — | L2-01-GP-01:stimulus، V2-PRE-Q11:stimulus، V2-PRE-Q12:stimulus |
| `VOC-05` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-05-fish-512.webp` | — | L2-01-IC-A03:stimulus |
| `VOC-06` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-06-sun-512.webp` | — | L1-06-GP-04:option، L1-06-IC-A04:option، L2-01-IC-A04:stimulus، V2-POST-Q30:stimulus |
| `VOC-07` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-07-moon-512.webp` | — | L1-06-GP-04:option، L2-01-IC-A01:stimulus، V2-PRE-Q30:stimulus، V2-POST-Q09:option |
| `VOC-08` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-08-tree-512.webp` | — | غير مستخدم في أسئلة البنك الحالية |
| `VOC-09` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-09-palm-tree-512.webp` | — | L1-06-GP-04:option، L1-06-IC-A04:option، SUP-05-SC-02:stimulus، V2-PRE-Q09:option، V2-POST-Q09:option |
| `VOC-10` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-10-ball-512.webp` | — | L2-01-IC-A02:stimulus، SUP-05-GP-01:stimulus |
| `VOC-12` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-12-duck-512.webp` | — | SUP-05-GP-04:stimulus |
| `VOC-14` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-14-star-512.webp` | — | L1-06-IC-A04:option، SUP-05-GP-02:stimulus، V2-PRE-Q10:stimulus، V2-POST-Q09:option |
| `VOC-16` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-16-cat-512.webp` | — | V2-POST-Q12:stimulus |
| `VOC-17` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-17-school-bag-512.webp` | — | SUP-07-SC-04:stimulus |
| `VOC-18` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-18-school-512.webp` | — | SUP-12-SC-02:stimulus |
| `VOC-20` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-20-bird-512.webp` | — | L3-07-IC-A01:stimulus |
| `VOC-21` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-21-garden-512.webp` | — | غير مستخدم في أسئلة البنك الحالية |
| `VOC-22` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-22-library-512.webp` | — | SUP-07-GP-04:stimulus، L3-07-IC-A02:stimulus |
| `VOC-24` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-24-sea-512.webp` | — | V2-POST-Q11:stimulus |
| `VOC-28` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-28-flower-512.webp` | — | L3-07-GP-02:stimulus |
| `VOC-30` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-30-leaves-512.webp` | — | غير مستخدم في أسئلة البنك الحالية |
| `VOC-34` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-34-boy-512.webp` | — | L3-07-GP-04:stimulus |
| `VOC-35` | صورة | مرشح V1؛ مراجعة معلقة | `assets/education/assets/vocabulary/webp/hem-voc-35-girl-512.webp` | — | SUP-12-GP-02:stimulus |

## 4. خطوات ربط النسخة النهائية

1. يراجع المشرف جودة وحقوق كل ملف بنفس معرف `asset_id`؛ التأكد من النطق والتشكيل والصورة غير الكاشفة للإجابة.
2. تُرفع النسخة إلى `assets/` بالصيغة المناسبة؛ للفيديو MP4 H.264/AAC ومعه VTT، وللصوت MP3 ونسخة WAV، وللصورة WebP/PNG وبديل alt.
3. يُسجل `source_path` الحقيقي وتستوفى شروط `approved` في إصدار مراجَع جديد؛ لا تعدل بنك V2 الحالي بقصد التحايل على النواقص.
4. يتحقق الفاحص من `MediaProvider.assert_publishable` لجميع الوسائط المستخدمة قبل ترقية الإنتاج، ومن فتح الملفات بالأدوار الصحيحة وسلامة `Range` والاستئناف.
5. تُحذف/تُعطل خرائط `TEST ONLY` من وضع الإنتاج؛ تبقى في staging للرجوع واختبارات الانقطاع والخطأ.

## 5. ما لم يُغلق بعد

- نتيجة CI/M04/M09 على SHA موحَّد أخير لـP06/P07؛ الاختبارات القديمة لا تعني قبول تغييرات اليوم.
- فحص بصري/سمعي حقيقي لـ12 صوتًا و23 صورة وحقوق استخدامها؛ الصوتان الاختياريان غير مطلوبين.
- توريد 19 فيديو تدريسيًا نهائيًا وربطها واعتمادها يحدث في P10، **لا يحجب نجاح تجهيز P07 التقني**.
- استيراد ملف بديل ثم إرجاعه في بيئة المعاينة الفعلية واختبار المشغل على الهاتف والشبكة البطيئة، لا يكفي اختبار المصدر فقط.
- فحص `Railway` watchPatterns لتشمل `assets/video/**` عند استبدال الفيديوهات دون تغيير كود، مع إبقاء تشغيل المعاينة فقط.

**القرار:** P07 media-readiness implementation prepared؛ لا `approved` حتى اكتمال أدلة الاختبارات، ولا يُعتمد P06 دون فحصه وقول «تم» المستقلة.


## 6. دليل التنفيذ الإضافي وملاحظات التشغيل

- آخر كود مختبر قيد CI: `3ec6a1c47717e2573505f21bd25d93d009b0288b` (يراجع HEAD الحالي قبل إصدار نتيجة نهائية).
- نقاط الربط الفعلية: `services/api/v2_content/readiness.py`، `media.py`، `v2_content_api.py`، `v2_lesson_runtime.py`، وصفحة `apps/web/src/app/admin/(dashboard)/v2-media/page.tsx`، وملف `services/api/test_fixtures/v2-preview-bindings.json`.
- اختبارات الدمج: `test_v2_lesson_runtime.py` و`test_v2_content_foundation.py`، تشمل عينة swap ثم revert، الرفض عند file/path invalid، فصل test_only عن source approval، قائمة 73 أصلًا مستخدمًا، والامتناع عن اعتماد 16 أصلًا خاملاً.
- اكتشفنا وصححنا فرق المسار بين `MediaProvider` وRoute الفعلي: approved URL هو `/api/v2/content/media/{asset_id}` (endpoint upstream `/v2/content/media/{asset_id}`). مسار المعاينة يظل `/api/v2/lessons/test-fixtures/{kind}/{asset_id}`.
- تم تعديل Railway WatchPatterns في **حساب «وصل تك كلاود همّه»** وخدمة API الحالية ليشمل الفيديو والصور، مع بقاء الخدمات وقاعدة البيانات كما هي.
- اختبار التبديل آلي داخل CI لا يعادل تجربة المشرف/الطالب الفعلية؛ والموافقة التربوية/الوسائط النهائية تبقى مؤجلة إلى P10.
