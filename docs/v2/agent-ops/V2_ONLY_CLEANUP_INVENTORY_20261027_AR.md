# جرد تنظيف Himma V2 — 2026-10-27

الحالة: فحص مصدر جزئي؛ لا حذف بيانات، لا اعتماد نهائي، لا نشر. فرع العمل cleanup/v2-only-20261027.

## ثبت إمكان إزالته من واجهة V2
- apps/web/src/app/admin/(dashboard)/content-preview/page.tsx: أزيل زر ومكوّن أرشيف بنك V1، مع إبقاء بنك V2.
- apps/web/src/app/admin/(dashboard)/layout.tsx: أزيل رابط أرشيف V1 والمكوّن العام ReinforcementReviewPanel. لا يزال الملف الأصلي موجودًا إلى حين فحص جميع مستهلكيه.

## مرشح للحذف بعد تتبع الاستيرادات والمسارات واختبارات بدائل V2
- apps/web/src/app/admin/(dashboard)/content-preview/LegacyContentPreview.tsx (1040 سطر): يجب إثبات عدم وجود مستهلكين آخرين.
- apps/web/src/app/admin/(dashboard)/students/[id]/page.tsx: يجب إعادة بناء الصفحة وليس حذفها؛ تبويبات الأرشيف والتقدم والمكافآت التاريخية V1 مختلطة مع صفحة V2.
- apps/web/src/app/admin/(dashboard)/audio-review/**: لا تُحذف قبل إثبات تغطية v2-reviewed-recordings ومراجعة صلاحياتها.
- apps/web/src/app/student/activity/[id]/page.tsx و student/session/[id]/page.tsx: مسارات V1؛ لا تُحذف قبل إثبات اكتمال lesson/assessment V2 وفحص الروابط المباشرة.
- apps/web/src/components/ReinforcementReviewPanel.tsx: أزيل من التخطيط العام، ولكن يجب جرد الاستيرادات الأخرى.
- admin/reports و admin/skill-reports: صفحات يجب إعادة ربطها بمصادر V2 لا حذف وظائف التقارير.
- AdminNotifications: يعتمد على مصدر إشعارات V1؛ يجب بناء بديل V2 قبل الحذف.
- services/api/main.py: ما زال يسجل routers قديمة: assessment, activities, journey, adaptation, reports, skill_reports, review, recordings, reward_catalog وغيرها. ممنوع حذف routers دفعة واحدة لأن auth/protected وبعض الاعتمادات مشتركة.
- apps/web/src/app/student/learning-v2/page.tsx و V2StudentDashboard.tsx: رسائل TEST ONLY؛ لا تُخفى قبل إثبات تشغيل وسائط الدروس وإتمام المكافآت.
- services/api/v2_student_readmodel.py: يعيد test_only=true و rewards.state=not_implemented_v2؛ يلزم عقد إنتاجي جديد.
- services/api/v2_assessment_runtime.py: الاختبار البعدي يتحقق من student.posttest_enabled بالإضافة إلى journey.placement_state. يجب فك الاعتماد على صلاحية V1 قبل حذف الحقول أو السجلات.
- services/api/v2_adaptation_runtime.py: ينتقل إلى posttest_ready بعد الدرس الأخير؛ اختبر اكتمال الرحلة ثم بدء الاختبار البعدي.

## البيانات
لم يُجرَ جرد SQL للجداول والعلاقات والأعداد ولا نسخة احتياطية بعد. ممنوع أي DROP/TRUNCATE/DELETE أو migration مدمرة. قبل الموافقة النهائية يجب استخراج مخطط العلاقات وعدد الصفوف والمراجع إلى V2، وإنشاء نسخة احتياطية مستقلة واختبار استعادتها.

## معايير إثبات الاستغناء
1. تحليل كل استيراد ورابط وendpoint وجداول FK وأعمال الخلفية لكل مرشح.
2. اختبارات طالب جديد: قبلي -> تسكين -> 19 درسًا وتدريبًا واختبارًا ودعمًا عند الحاجة -> بعدي.
3. فحص بنك 300 سؤال والأصول الفعلية، صور وصوت وفيديو، وعدم ظهور نصوص تطويرية.
4. فحص كل وظائف المشرف وتقارير ومراجعات V2 وصلاحياتها.
5. اختبارات البناء وAPI وE2E على معاينة معزولة؛ عدم المساس بالإنتاج.
6. تقرير حذف مفصل لكل ملف/جدول/سجل وتأكيد المستخدم قبل حذف البيانات.
