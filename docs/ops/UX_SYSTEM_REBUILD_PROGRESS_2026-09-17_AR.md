> **HISTORICAL / SUPERSEDED:** هذه الوثيقة محفوظة للتاريخ والدليل فقط. الحالة الحالية بعد 2026-09-18 موجودة في START_HERE_AR.md وdocs/ops/STATUS.md. أي عبارة هنا مثل NOT MERGED / NOT DEPLOYED / ACTIVE / STOP أو branch قديم لا تصف الوضع الحالي.

# تقدم إعادة بناء UX — 2026-09-17

الفرع التنفيذي: `fix/ux-system-rebuild-2026-09-17`

خط الأساس الرسمي: `765c42d769624ad13683798f68177f6597f2149f`

آخر Functional SHA مختبر لهذه الدفعة:

`09be49102d1aab8f09cf1a3267ccd073c46c7397`

Quality Gate #917 / Run `35261495545`: **SUCCESS** على نفس الـSHA.

## حالة الدفعات A–E

### A — Student Question System

منفذ برمجيًا:
- نظام responsive مشترك للنص/العنوان/الصور/الترتيب.
- Assessment + Activity مشمولان.
- Content Preview يستخدم نفس مبدأ الكثافة عبر admin workflow CSS.
- Playwright responsive يغطي 320/360/390/430/768/1440 ويمنع horizontal overflow.

الحالة: **CI GREEN — Visual QA النهائي مطلوب**.

### B — Student Dashboard & Journey

منفذ برمجيًا:
- Dashboard يعامل الصفحة كرحلة: الهوية → الإجراء الحالي → الرحلة → المستويات → الشارات → النتائج.
- Rerecord يأتي بعد الإجراء الرئيسي ولا يخطف المستخدم تلقائيًا.
- النتائج أصبحت secondary surface.

الحالة: **CI GREEN — Visual QA النهائي مطلوب**.

### C — Admin Audio Review Workflow

منفذ برمجيًا:
- queue أكثر كثافة ووضوحًا.
- Decision-first: اعتماد أو طلب إعادة تسجيل ثم الحقول ذات الصلة.
- تحسين أزرار الهاتف وتقليل الفراغات.
- Toast مشترك لنتائج الحفظ/الخطأ بدل Alert ثابت.

الحالة: **CI GREEN — Visual QA النهائي مطلوب**.

### D — Admin Dashboard & Notifications

منفذ برمجيًا:
- إزالة تكرار بطاقة مستقلة لكل تسجيل معلق من Dashboard.
- `/api/review/pending-audio` يوفر count مجمعًا.
- تفاصيل التسجيلات تبقى داخل Review Queue / Notification Center.
- Dedupe لبقية Attention Items.

الحالة: **CI GREEN — Visual QA النهائي مطلوب**.

### E — Remaining Admin UX

منفذ برمجيًا:
- Student Profile responsive/mobile tabs محسنة.
- Add Student يعرض access code الحقيقي بعد الإنشاء بدل preview عشوائي.
- Content Preview يستخدم payload الحقيقي ويدعم round navigation/context intro.
- `AdminFeedbackToast` يطبق auto-dismiss + click/pointer dismiss + close button.
- Feedback ملف الطالب والإعدادات ومراجعة التسجيلات تم تحسينه في هذه الدفعة.

الحالة: **جزء التنفيذ موجود وCI GREEN — يلزم مرور Visual QA نهائي على بقية Admin surfaces**.

## عقد الصوت المحمي

- Pending recording لا يمنع الطالب من الأسئلة التالية.
- النتيجة النهائية تبقى محجوبة حتى Human Supervisor Review عند الحاجة.
- Rerecord مهمة مستقلة وصريحة.
- التسجيل السابق يبقى محفوظًا.
- لا Fake ASR ولا Student/Temporary Audio Skip.

## Evidence

- Quality Gate #917 / Run `35261495545`: SUCCESS.
- Security: SUCCESS.
- Frontend: SUCCESS.
- Backend: SUCCESS.
- Integration: SUCCESS.
- Playwright report artifact ID `10515801114`.

## المتبقي قبل الدمج والنشر

1. فتح ومراجعة screenshots/Playwright visual evidence مقابل صور المالك الأصلية.
2. إصلاح أي mismatch يظهر وإعادة exact-head QG إذا تغير الكود.
3. تشغيل M09 Release Readiness على final UX functional SHA.
4. دمج/fast-forward إلى `stage/02-content` فقط بعد Visual QA + QG + M09.
5. official exact-head CI بعد الدمج عند الحاجة.
6. Railway deployment.
7. Production QA: `/health`, `/ready`, login, question sizing, Student Dashboard, Admin Dashboard, Audio Review, Pending Audio, Rerecord, Toasts, mobile responsiveness.
8. تحديث أدلة الإغلاق النهائي.

**لا تعتبر الدفعة CLOSED أو منشورة حتى تكتمل النقاط أعلاه.**
