# HANDOFF — Himma UX System Rebuild — 2026-09-17

هذا الملف هو نقطة الاستئناف للمحادثة التالية الخاصة بآخر ملاحظات التصميم والصور التي أرسلها المالك في 2026-09-17.

## 1) قاعدة الحقيقة

لا تعتمد على هذا الملف كبديل عن الحالة الحية إذا تغير المستودع.

الترتيب:

1. live repository code
2. PostgreSQL schema/migrations
3. executable tests / CI exact-SHA
4. verified runtime
5. canonical product/content/audio contracts
6. current docs
7. هذا handoff

ابدأ دائمًا بـFetch للـHEADs الحالية.

## 2) الفروع والحالة عند إنشاء هذا handoff

Official branch:

`stage/02-content`

Official/Production baseline SHA عند آخر تحقق قبل دفعة UX:

`765c42d769624ad13683798f68177f6597f2149f`

Active UX branch:

`fix/ux-system-rebuild-2026-09-17`

آخر Functional SHA اختُبر قبل commits التوثيق فقط:

`09be49102d1aab8f09cf1a3267ccd073c46c7397`

مهم: فرع UX تلقى بعده commits توثيق فقط. في المحادثة الجديدة يجب Fetch live HEAD وعدم افتراض أن `09be...` هو HEAD؛ اعتبره **آخر Functional Evidence SHA** ما لم يظهر كود أحدث.

## 3) الإصدار الرسمي الموجود على Production قبل دفعة UX

النسخة الرسمية `765c42d...` كانت قد أغلقت بنجاح:

- Integration Quality Gate #911 / Run `35241996615`: SUCCESS.
- M09 #215 / Run `35241996654`: SUCCESS.
- Official Quality Gate #912 / Run `35243714139`: SUCCESS.
- Railway كان منشورًا على نفس SHA للـAPI/Web عند آخر تحقق.
- `/api/health` = 200.
- `/api/ready` = 200.
- PostgreSQL / Redis / object storage سليمة عند نقطة التحقق.
- canonical runtime = 125 items / 44 skills.

هذا هو Production baseline حتى يتم نشر UX batch الجديدة.

## 4) لماذا بدأت دفعة UX الجديدة

المالك راجع النسخة المنشورة بصور فعلية وقال إن جزءًا من التعديلات السابقة لم يعالج المشاكل جذريًا.

الملاحظات الأساسية من الصور/النقاش:

- خط/نص stimulus داخل حاوية العرض ضخم وغير مرن، خصوصًا عندما يصبح المحتوى جملة.
- حاوية العرض نفسها تخلق فراغًا أكبر من المحتوى.
- Student Dashboard/ملف الطالب يحتاج ترتيبًا حقيقيًا ومنع التعارض على الهاتف.
- Admin Dashboard يكرر `تسجيل جديد يحتاج مراجعة` لكل تسجيل بدل aggregate واحد.
- أزرار صفحة التسجيل/المراجعة غير متوازنة على الهاتف.
- صفحة اعتماد التسجيل فيها فراغات كبيرة وHierarchy ضعيف وControls غير واضحة.
- إشعار نجاح/تعديل يجب أن يختفي تلقائيًا أو بمجرد النقر، بدل بقائه عالقًا.
- يجب إعادة مراجعة المشاكل السابقة كاملة وعدم اعتبارها محسومة لمجرد وجود commit سابق.

قرار المالك المعتمد: لا patch لكل Screenshot؛ نعالج الجذور ونقسم العمل A–E.

## 5) الخطة المعتمدة A–E

### A — Student Question System

المطلوب:

- Stimulus typography/container responsive حسب طول المحتوى.
- حرف قصير يبقى كبيرًا؛ كلمة أقل؛ جملة/عبارة متوسطة ومرنة.
- Mobile question title أصغر ومتوازن.
- Image choices تتبع الصورة بدل بطاقات ضخمة فارغة.
- Ordered/sequence images أكثر compact على الهاتف.
- الحفاظ على إصلاحات rapid audio switching وعدم sticky audio error.
- Assessment + Activity + Admin Content Preview يجب أن تستخدم نفس منطق العرض.

### B — Student Dashboard & Journey

الترتيب المعتمد:

1. هوية الطالب + المستوى الحالي + حالة الرحلة.
2. Primary next action.
3. خط الرحلة Pretest → Level/Learning → Reinforcement عند الحاجة → Posttest.
4. Level progress.
5. Real rewards/stars/badges.
6. Results/history كطبقة ثانوية.

Dashboard = journey surface، وليس مجموعة cards متساوية الأهمية.

### C — Admin Audio Review Workflow

التدفق:

`Recording → Listen → Decision → Evidence/Notes if needed → Save`

- قرار أولًا: Approve أو Request Rerecord.
- الحقول التابعة للقرار تظهر بعده.
- تقليل الفراغات.
- أزرار الهاتف واضحة ومتوازنة.
- لا نموذج اعتماد ضخم ومبعثر.

### D — Admin Dashboard & Notifications

- Dashboard يعرض aggregate واحد لعدد التسجيلات التي تنتظر المراجعة.
- لا بطاقة مستقلة لكل recording.
- التفاصيل الفردية مكانها Review Queue / Notification Center.
- بقية Attention items يتم dedupe لها.

### E — Remaining Admin UX

- Student Profile mobile tabs/layout.
- Add Student flow.
- Content Preview fidelity.
- Toast/Feedback system.

Toast contract:

- Success ≈ 3.2s ثم auto-dismiss.
- Error غير الحرج ≈ 5.2s ثم auto-dismiss.
- click على toast يغلقه.
- النقرة التالية على الشاشة تغلقه.
- زر X للإغلاق.
- critical/actionable errors يمكن أن تبقى inline قرب الإجراء.

## 6) ما نُفذ فعليًا في فرع UX

الفرق عن `stage/02-content` قبل commits التوثيق شمل 15 مسارًا وظيفيًا/توثيقيًا رئيسيًا، منها:

- `apps/web/src/app/student/question-system.css` — جديد.
- `apps/web/src/app/student/dashboard-system.css` — جديد.
- `apps/web/src/app/student/layout.tsx` — تحميل النظامين المشتركين.
- `apps/web/src/app/admin/(dashboard)/admin-workflow.css` — جديد.
- `apps/web/src/app/admin/(dashboard)/layout.tsx` — تحميل Admin workflow CSS.
- `apps/web/src/app/admin/(dashboard)/page.tsx` — aggregate pending audio + dashboard hierarchy.
- `apps/web/src/app/admin/(dashboard)/audio-review/page.tsx` — feedback/workflow cleanup.
- `apps/web/src/app/admin/(dashboard)/students/[id]/student-detail.module.css` — mobile layout/tabs/cards/actions.
- `apps/web/src/app/admin/(dashboard)/students/new/page.tsx` — Add Student UX/real access-code behavior.
- `apps/web/src/app/admin/(dashboard)/settings/page.tsx` — shared transient feedback.
- `apps/web/src/components/admin/AdminFeedbackToast.tsx` — جديد.
- `apps/web/src/components/admin/AdminFeedbackToast.module.css` — جديد.
- `apps/web/tests/e2e/w6-responsive.spec.ts` — responsive/visual evidence additions.

لا تعتمد على هذه القائمة كبديل عن live compare؛ Fetch/Compare عند البدء.

## 7) ما ثبت من الكود أثناء المراجعة

### Student Question System

`question-system.css` يغطي:

- `question-title`
- `question-stimulus`
- `image-options`
- `sequence-image-options`
- `sequence-board`
- activity text/image/sequence options
- activity reading text

ويستخدم media queries للهاتف، مع حدود أصغر للنص والصور.

### Student Dashboard

`dashboard-system.css` يعيد hierarchy بصريًا على `student-home`:

- primary action أولًا
- rerecord بعده
- journey/level journey بعده
- badges ثم results
- responsive collapse على tablet/mobile

### Admin Dashboard

الكود يجلب `/api/review/pending-audio` ويعرض `pendingAudioCount` كبطاقة Aggregate واحدة.

Notifications التي رابطها `/admin/audio-review...` لا يعاد عرضها فرديًا داخل Attention Area.

### Audio Review

الصفحة الحالية تعرض:

- الطالب + نوع الجلسة + وقت الإرسال
- expected reading text
- audio player
- Start Review
- Decision-first approve/rerecord
- evidence counters + notes عند approve
- explicit explanation عند rerecord

### Toast

`AdminFeedbackToast`:

- success 3200ms
- error 5200ms
- click dismiss
- next pointer dismiss after arm delay
- explicit close button
- `status`/`alert` semantics

### Content Preview

الصفحة تستخدم payload الحقيقي لـAssessment/Learning، وبها hooks فعلية:

- `admin-content-preview-stage`
- `data-preview-question`
- `data-preview-stimulus`
- `preview-image-options`
- `preview-context-reading-text`

ولذلك `admin-workflow.css` يمكنه ضبط نفس density rules التي يستخدمها student question system.

## 8) Quality Gate الحالي للـUX

Exact tested functional SHA:

`09be49102d1aab8f09cf1a3267ccd073c46c7397`

Quality Gate #917 / Run `35261495545`: **SUCCESS**.

- Security: SUCCESS.
- Frontend: SUCCESS.
- Backend: SUCCESS.
- Integration: SUCCESS.

Playwright report:

- Artifact ID `10515801114`
- Digest `sha256:12ce698a4bda93921eec73414b15f59efb24050c648a9a02d90ef370df145a74`

`w6-responsive.spec.ts` يلتقط screenshots لـStudent Home + Assessment على:

- 320x720
- 360x800
- 390x844
- 430x932
- 768x1024
- 1440x1000

ويتحقق من:

- no horizontal overflow
- primary action touch target >=44px
- mobile question title <=25px
- interactive control >=44px

## 9) عقود الصوت — لا ترجع للسلوك القديم

العقد الصحيح الحالي:

- Student uploads assessment reading.
- إذا توجد أسئلة غير مجابة: الطالب يكمل `next` عادي.
- لا ينتظر Human Review بعد كل recording.
- بعد انتهاء الأسئلة، finalization يبقى blocked إذا توجد audio submissions pending review.
- Supervisor review هي السلطة الأكاديمية الحالية.
- Request Rerecord ينشئ task مستقلة.
- task لا hijack السؤال/النشاط الحالي تلقائيًا.
- student يفتح rerecord explicitly.
- previous recording يبقى historical.

ممنوع:

- Fake ASR
- Student/Temporary Audio Skip
- bypass
- حذف history
- weakening tests / skip / xfail / retry masking

## 10) ما لم يتم بعد — لا تدّعي إغلاقه

1. **Visual QA البشري للصور الناتجة من Playwright** مقابل صور المالك الأصلية ومشاكل A–E.
2. إذا ظهر mismatch: Root Cause fix + exact-head QG جديد.
3. **M09 Release Readiness للـfinal UX functional SHA** لم يغلق لهذه الدفعة بعد.
4. UX branch **لم تُدمج** إلى `stage/02-content` حتى نقطة هذا handoff.
5. UX branch **لم تُنشر** على Railway حتى نقطة هذا handoff.
6. Production QA للـUX SHA لم ينفذ.
7. Manual screen-reader QA ما زال غير claimed.
8. Production ASR provider ما زال external/deferred.

## 11) أول مهمة في المحادثة التالية

ابدأ هكذا، بدون إعادة العمل من الصفر:

1. Fetch live HEAD لـ`stage/02-content`.
2. Fetch live HEAD لـ`fix/ux-system-rebuild-2026-09-17`.
3. اقرأ:
   - `docs/ops/STATUS.md`
   - `docs/ops/UX_SYSTEM_REBUILD_2026-09-17_AR.md`
   - `docs/ops/UX_SYSTEM_REBUILD_PROGRESS_2026-09-17_AR.md`
   - `docs/ops/progress.json`
   - هذا handoff
4. Compare official vs UX branch.
5. تحقق أن آخر functional evidence ما زال #917 على `09be...` أو استبدله بأحدث evidence إذا تغير الكود.
6. افتح/راجع Playwright visual evidence وscreenshots على المقاسات المحددة.
7. لا تعدل لمجرد التعديل؛ قارن تحديدًا مع المشاكل المعتمدة A–E.
8. إذا كل شيء بصريًا صحيح، انتقل إلى M09. إذا لا، أصلح Root Cause أولًا ثم QG exact-head جديد.

## 12) شرط الدمج والنشر

لا merge ولا deploy لهذه الدفعة إلا بعد:

`Visual QA GREEN + Quality Gate exact-head GREEN + M09 exact-head GREEN`

ثم:

- merge/fast-forward إلى `stage/02-content`
- official exact-head CI
- Railway deploy
- verify deployed SHA
- `/health` + `/ready`
- Production QA على Student/Admin/Audio/Pending/Rerecord/Toasts/Responsive
- تحديث final closure docs

## 13) قاعدة القرار

لا ترقيع Screenshot.

اسأل دائمًا:

- ما Root Cause؟
- هل component/shared primitive هو المكان الصحيح للإصلاح؟
- هل Student/Admin/Preview متناسقون؟
- هل Mobile + Desktop سليمين؟
- هل business/audio contract لم يتغير؟
- هل يوجد exact-SHA evidence؟

هذا هو checkpoint الذي يجب أن تكمل منه المحادثة الجديدة.
