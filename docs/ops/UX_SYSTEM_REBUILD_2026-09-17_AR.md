# إعادة بناء UX لمنصة هِمّة — 2026-09-17

الحالة: **ACTIVE — التنفيذ البرمجي الأساسي موجود، الإغلاق البصري/الإصداري لم يكتمل**

الفرع: `fix/ux-system-rebuild-2026-09-17`

خط الأساس الرسمي قبل هذه الدفعة:

`765c42d769624ad13683798f68177f6597f2149f`

آخر Functional SHA اختُبر لهذه الدفعة قبل commits التوثيق فقط:

`09be49102d1aab8f09cf1a3267ccd073c46c7397`

> هذه الدفعة بدأت بعد مراجعة المالك لصور فعلية من النسخة المنشورة. القرار المعتمد: لا نعالج كل Screenshot كترقيعة CSS منفصلة؛ نعالج جذور نظام العرض، بنية Dashboard الطالب، Workflow مراجعة التسجيلات، Dashboard/Notifications للأدمن، ثم بقية Admin UX.

## Source of Truth لهذه الدفعة

1. الكود الحي في المستودع والـbranch الحالي.
2. سلوك Runtime/API الحالي.
3. الاختبارات القابلة للتنفيذ وCI exact-SHA.
4. عقود المنتج والصوت الحالية.
5. هذه الوثيقة والصور/الملاحظات المعتمدة من المالك.

إذا تعارض وصف قديم مع الكود/العقد الحالي، لا نرجع للسلوك القديم لمجرد أن Test أو وثيقة قديمة تتوقعه.

## المبادئ المعتمدة

1. إصلاح Design Primitives والمكونات المشتركة قبل ترقيع الصفحات.
2. البيانات المعروضة حقيقية من Runtime/API؛ لا بطاقات شكلية أو قيم تجريبية.
3. لا تغيير لعقود التقييم الأكاديمية أو المحتوى canonical بسبب متطلبات العرض.
4. Pending Audio لا يمنع الطالب من إكمال بقية أسئلة الجلسة؛ الانتظار الأكاديمي يكون عند نهاية الأسئلة إذا بقيت مراجعات معلقة.
5. Rerecord مهمة صريحة يفتحها الطالب، ولا تخطفه تلقائيًا من السؤال/النشاط الحالي.
6. Human Supervisor Review تبقى السلطة الأكاديمية للتسجيلات؛ لا Fake ASR ولا Audio Skip.
7. النجاح البرمجي وحده لا يكفي؛ الإغلاق يتطلب CI + Visual QA + M09 + Production QA.

---

## A — Student Question System

### المشكلة التي ظهرت في الصور

- النص داخل حاوية العرض كان يعامل الجملة كأنها حرف/كلمة قصيرة ويظهر بحجم ضخم.
- الحاوية نفسها تحجز فراغًا أكبر من المحتوى.
- عنوان السؤال على الهاتف كبير نسبيًا.
- خيارات الصور تملك بطاقات أكبر من الصورة الفعلية.
- صور الترتيب والـsequence تحتاج كثافة أعلى وترتيبًا أفضل على الهاتف.

### العقد المعتمد

- حرف/رمز قصير جدًا: عرض بارز وكبير.
- كلمة: عرض كبير ولكن أقل من الحرف.
- عبارة/جملة: حجم متوسط مرن مع طول النص والمساحة.
- الحاوية تتبع المحتوى ولا تفرض ارتفاعًا ضخمًا.
- الصور تستخدم `object-fit: contain` والبطاقة تتبع المحتوى مع Touch Target آمن.
- ترتيب الصور يظل مقروءًا بدون بطاقات ضخمة.
- نفس المبادئ تصل إلى Assessment + Activity + Admin Content Preview لمنع drift.

### المنفذ في الكود

- `apps/web/src/app/student/question-system.css` أضيف كنظام مشترك scoped على hooks مستقرة.
- يتم تحميله من `apps/web/src/app/student/layout.tsx`.
- يغطي Question Title، Stimulus، image choices، ordered images، sequence board، activity text/image options وreading text.
- Content Preview لديه hooks فعلية `data-preview-question`, `data-preview-stimulus`, `preview-image-options` ويتم ضبطها من `admin-workflow.css` بنفس مبدأ الكثافة.
- Playwright responsive يغطي viewports من 320px حتى 1440px ويتحقق من عدم Horizontal Overflow ومن حد Touch Target ومن حجم عنوان السؤال على الهاتف.

الحالة: **Functional/CI GREEN، Visual QA البشري النهائي ما زال مطلوبًا**.

---

## B — Student Dashboard & Journey

### المطلوب المعتمد

الترتيب المفاهيمي:

1. هوية الطالب + المستوى الحالي + حالة الرحلة.
2. الإجراء الرئيسي الآن: أكمل الاختبار / تابع نشاطك / افتح مهمة إعادة تسجيل / انتظار مراجعة.
3. خط الرحلة: قبلي → مستوى → أنشطة → تقوية عند الحاجة → بعدي.
4. تقدم المستوى: الأنشطة المنجزة + التقدم الحقيقي.
5. الشارات والنجوم من بيانات حقيقية فقط.
6. النتائج والسجل كمعلومات ثانوية.

الهدف: Dashboard رحلة، وليس مجموعة Cards متساوية الأهمية.

### المنفذ في الكود

- `apps/web/src/app/student/dashboard-system.css` يفرض hierarchy بصريًا على سطح `student-home`.
- Primary Action يبقى أول منطقة تشغيلية واضحة.
- Rerecord tasks تأتي بعد الإجراء الرئيسي ولا تستولي على الصفحة تلقائيًا.
- Journey/levels تأتي قبل badges والنتائج.
- النتائج أصبحت secondary surface أبسط بصريًا.
- التخطيط يتحول تدريجيًا من Desktop إلى Tablet ثم Mobile بدون تكدس أفقي.

الحالة: **Functional/CI GREEN، يحتاج مقارنة بصرية فعلية مع الهاتف الذي ظهرت عليه المشاكل**.

---

## C — Admin Audio Review Workflow

### المشاكل من الصور

- زر الاستماع وبدء المراجعة غير متوازنين بصريًا على الهاتف.
- صفحة اعتماد التسجيل فيها فراغات كبيرة، hierarchy ضعيف، وقيم/حقول تبدو كنصوص متلاصقة.
- أزرار الحفظ والإلغاء كبيرة ومتشابهة في الوزن.

### التدفق المعتمد

`التسجيل → استماع → قرار → أدلة/ملاحظات عند الحاجة → حفظ`

قرار المشرف أولًا:

- اعتماد القراءة.
- طلب إعادة تسجيل.

ثم تظهر الحقول ذات الصلة فقط.

### المنفذ في الكود

- `apps/web/src/app/admin/(dashboard)/admin-workflow.css` يضبط كثافة queue/form على الهاتف والديسكتوب.
- صفحة `audio-review` تعرض الطالب/نوع الجلسة/النص المطلوب/التسجيل ثم الإجراء.
- نموذج القرار Decision-first.
- Request Rerecord يوضح أن التسجيل السابق يبقى تاريخيًا وأن المهمة الجديدة لا توقف المسار الحالي.
- Feedback في هذه الصفحة انتقل إلى `AdminFeedbackToast` المشترك بدل Alert ثابت أعلى الصفحة.

الحالة: **Functional/CI GREEN، Visual QA النهائي مطلوب**.

---

## D — Admin Dashboard & Notifications

### المشكلة من الصور

Dashboard كان يكرر بطاقة `تسجيل جديد يحتاج مراجعة` لكل Recording، مع أن التفاصيل الفردية مكانها Review/Notifications.

### العقد المعتمد

- Dashboard يعرض Aggregates فقط، مثل `3 تسجيلات تحتاج مراجعة`.
- التفاصيل الفردية تبقى داخل Review Queue / Notification Center.
- لا تكرار لنفس event كعدة Attention Cards.
- الضغط على الملخص يفتح المساحة التشغيلية المناسبة.

### المنفذ في الكود

- Dashboard يجلب `/api/review/pending-audio` ويحسب `pendingAudioCount`.
- إشعارات audio review الفردية تستبعد من Attention Area.
- يوجد dedupe لبقية Attention Items حسب `href|title`.
- بطاقة واحدة مجمعة لمراجعة التسجيلات، مع إبقاء Notification Center منفصلًا.

الحالة: **Functional/CI GREEN، يحتاج فحص بصري نهائي على Mobile**.

---

## E — Remaining Admin UX

### Student Profile

- تبويبات ملف الطالب تبقى Horizontal Scroll بدل التداخل.
- تحسين identity/header/summary/cards/controls على الهاتف.
- تم ضبط responsive CSS في `student-detail.module.css` لتقليل التزاحم والمحافظة على hierarchy.

### Add Student

- صفحة إضافة الطالب تستخدم رمزًا حقيقيًا من الخادم بعد الحفظ؛ لا Preview عشوائي يوحي بأنه الرمز النهائي.
- على الهاتف إجراءات النموذج تصبح بعرض مناسب ولا تتعارض.

### Content Preview

- الـPreview يستخدم payload الحقيقي Assessment/Learning.
- يوجد تنقل بين الجولات في Learning Preview.
- Context intro/audio/reading يعرض وفق payload الفعلي.
- القواعد البصرية الجديدة تتبع نفس منطق Student Question System.

### Toast / Feedback Contract

المعتمد:

- Success: يختفي تلقائيًا تقريبًا بعد 3.2 ثانية.
- Error غير الحرج: يبقى أطول قليلًا (حوالي 5.2 ثانية) ثم يختفي.
- النقر على Toast يغلقه.
- النقرة التالية على الشاشة بعد ظهوره تغلقه.
- زر إغلاق واضح متاح.
- الأخطاء التي تحتاج قرارًا تبقى Inline قرب الإجراء عندما يكون ذلك أنسب من Toast فقط.

المنفذ:

- `AdminFeedbackToast.tsx` + module CSS.
- مربوط حاليًا بمراجعة التسجيلات، إعدادات المشرف، وFeedback ملف الطالب للعمليات التي تم تعديلها في هذه الدفعة.

الحالة: **Functional/CI GREEN، ما زال المرور البصري النهائي مطلوبًا على بقية Admin surfaces قبل CLOSED**.

---

## عقود الصوت التي لا يجوز كسرها أثناء UX

- التسجيل المرسل أثناء الاختبار لا يمنع `next` إذا توجد أسئلة أخرى.
- `finish` يبقى fail-closed إلى أن تكتمل مراجعات الصوت المطلوبة.
- Rerecord يظهر كمهمة مستقلة.
- فتح Rerecord يتم explicit من الطالب.
- التسجيل القديم لا يحذف ولا يستبدل تاريخيًا.
- Human Supervisor Review هي السلطة الأكاديمية الحالية.
- مزود ASR الخارجي ما زال مؤجلًا.

---

## Regression checklist قبل الإغلاق

- Admin login + الرجوع للرئيسية.
- Student login + الرجوع للرئيسية.
- Add student.
- Student profile mobile tabs.
- Image-choice sizing.
- Image-sequence ordering.
- Short/medium/long stimulus sizing.
- Mobile question title.
- Rapid audio click + switch audio without sticky error.
- Pending Audio journey.
- Rerecord explicit task.
- Student Dashboard real progress/results/badges.
- Audio Review queue + decision form.
- Admin Dashboard aggregated attention states.
- Toast auto-dismiss + click dismiss + close button.
- Content Preview fidelity.
- No horizontal overflow at narrow viewports.

---

## Exact CI evidence الحالي

Functional SHA:

`09be49102d1aab8f09cf1a3267ccd073c46c7397`

Quality Gate #917 — Run `35261495545`: **SUCCESS**.

- Security: SUCCESS.
- Frontend: SUCCESS.
- Backend: SUCCESS.
- Integration: SUCCESS.
- Playwright report artifact: `10515801114`.
- Artifact digest: `sha256:12ce698a4bda93921eec73414b15f59efb24050c648a9a02d90ef370df145a74`.

مهم: أي commits لاحقة لتحديث التوثيق فقط لا تستبدل هذا SHA كـfunctional evidence.

---

## ما لم يتم بعد

1. مراجعة screenshots/visual evidence الناتجة من Playwright مقابل مشاكل الصور الأصلية.
2. إصلاح أي mismatch بصري إن ظهر، ثم rerun QG على exact new functional HEAD.
3. M09 Release Readiness على final UX SHA — **لم يُغلق لهذه الدفعة حتى الآن**.
4. Merge إلى `stage/02-content` — **لم يتم لهذه الدفعة**.
5. Railway deployment للـUX SHA — **لم يتم لهذه الدفعة**.
6. Production Visual/Functional QA — **لم يتم لهذه الدفعة**.

لا تكتب CLOSED قبل اكتمال هذه السلسلة.
