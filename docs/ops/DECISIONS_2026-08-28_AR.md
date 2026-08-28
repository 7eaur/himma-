# قرارات المراجعة والصيانة — 2026-08-28

هذا الملف يسجل أحدث القرارات. لا يحذف ADR التاريخي؛ عند التعارض الزمني يكون القرار الأحدث هو المرجع ما لم يكن موسومًا Proposed.

## D-2026-08-28-01 — المسار بعد القبلي

**معتمد.**

الاختبار القبلي يحدد نقطة البداية فقط. بعد ذلك يسير الطالب صعودًا حتى L3:

- L1→L2→L3.
- L2→L3.
- L3.

Posttest بعد اكتمال مسار التدخل المطلوب، لا بعد L1/L2 مباشرة.

## D-2026-08-28-02 — نتيجة النشاط

**معتمد.**

- >=80 pass.
- 70–79 guided retry للجزء الخاطئ.
- <70 weakness + targeted reinforcement.

## D-2026-08-28-03 — الترقية

**معتمد.**

50/30/20 لا يسمح بتخطي بقية Core. لا ترقية قبل إكمال 10/10 Core وعبور gates المطلوبة.

## D-2026-08-28-04 — Level Session history

**معتمد.**

كل مستوى يملك Core Session مستقلة. الانتقال يغلق القديمة ويفتح الجديدة؛ لا يعاد وسم التاريخ.

## D-2026-08-28-05 — التقوية

**معتمد.**

المسار:

`weakness → reinforcement → return to core → verification → continue`.

لا random fallback.

## D-2026-08-28-06 — Reinforcement Mapping

**معتمد.**

الربط المستهدف `Skill → Skill Family → Approved candidates` بدل exact skill-only.

## D-2026-08-28-07 — محتوى التقوية

**معتمد.**

إضافة 18 Micro-Reinforcement فوق 15 الأصلية؛ الإجمالي 33. التفاصيل في `REINFORCEMENT_CONTENT_ADDITIONS_2026-08-28_AR.md`.

## D-2026-08-28-08 — الصور الجديدة

**معتمد.**

الصور الناقصة للتقويات الجديدة سيتم توليدها داخليًا لاحقًا وفق هوية هِمّة؛ لا تطلب من العميل البحث عنها حاليًا.

## D-2026-08-28-09 — الصوت الثابت

**معتمد.**

50 موجود + «موز» + «سَا» = 52 هدفًا. لا فجوات جديدة بسبب التقويات الـ18.

## D-2026-08-28-10 — TEMP audio skip

**معتمد كمؤقت فقط.**

`HIMMA_TEMP_AUDIO_SKIP=true` يسمح بتجاوز recording tasks محايدًا دون AudioSubmission/score/mastery/reward. عند false يعود النظام الطبيعي.

## D-2026-08-28-11 — نموذج الصوت

**معتمد تصميميًا.**

Reference-Guided Arabic Reading Analysis:

ASR → alignment to known text → Correct/Deletion/Insertion/Substitution → confidence → optional calibrated phoneme/haraka evidence → human review.

Whisper alone ليس النظام الكامل.

## D-2026-08-28-12 — Product UI

**معتمد.**

الحالة الحالية Recovery Baseline، وليست Final Product UI. مطلوب Student full-screen learning stage + unified task kit + Admin IA rebuild + responsive/accessibility gate.

## D-2026-08-28-13 — المصطلح

**معتمد.**

الظاهر: «المشرف». `researcher` داخلي فقط.

## D-2026-08-28-14 — Local infrastructure

**معتمد.**

لا Docker محليًا.

## D-2026-08-28-15 — Automatic Demotion

**PROPOSED — غير مثبت نهائيًا.**

التوصية الحالية: إلغاء الخفض الآلي من المسار العادي؛ الدعم والتقوية داخل المستوى، والتغيير الاستثنائي يدوي للمشرف بسبب موثق.

السبب: Placement يحدد نقطة البداية، والتقلب بين المستويات أثناء التدخل يضعف وضوح الرحلة والتفسير البحثي.

**ممنوع حذف demotion من الكود قبل تحويل هذا القرار إلى Final/ADR.**
