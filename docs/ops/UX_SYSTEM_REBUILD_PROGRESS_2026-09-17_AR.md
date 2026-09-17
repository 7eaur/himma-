# تقدم إعادة بناء UX — 2026-09-17

الفرع التنفيذي: `fix/ux-system-rebuild-2026-09-17`

## المنفذ حتى الآن

- Student Question System: أضيف نظام مشترك لتصغير النصوص والخيارات والصور حسب المحتوى بدل الحاويات الضخمة.
- Assessment + Activity: أصبح النظام المشترك يغطي الاختبار والأنشطة عبر hooks مستقرة، مع ضبط خيارات الصور والنص والترتيب والقراءة على الهاتف.
- Student Dashboard: أضيف ترتيب بصري يجعل الصفحة رحلة واضحة: الهوية والإجراء الحالي أولًا، ثم الرحلة والمستويات والشارات، والنتائج كمعلومات ثانوية.
- Admin Dashboard: أزيل تكرار تسجيلات المراجعة داخل Attention Area. عدد التسجيلات المعلقة يأتي مباشرة من `/api/review/pending-audio` ويظهر كملخص واحد، بينما تبقى التفاصيل الفردية في Review Queue / Notifications.
- Admin Audio Review: أضيف Shared Workflow CSS لتقليل الفراغات وجعل نموذج القرار أوضح وأكثر تماسكًا على الهاتف.

## لم يُغلق بعد

- Visual QA الفعلي على الهاتف والديسكتوب.
- Content Preview fidelity مع نفس قواعد Student Question System.
- Add Student + Student Profile mobile tabs.
- Toast auto-dismiss/dismiss contract.
- Regression + exact-SHA CI النهائي.

لا تعتبر أي دفعة CLOSED قبل evidence الاختبارات وVisual QA.
