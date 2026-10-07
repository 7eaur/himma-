# البنود المفتوحة الحالية — هِمّة

**Updated:** 2026-10-07

## أعمال التحسين المصرح بها

| ID | البند | الحالة |
|---|---|---|
| CLN-01 | توحيد مصادر التوثيق الحالية وإلغاء التكرار المنطقي | COMPLETE — QG #1063 SUCCESS |
| CLN-02 | جرد الكود والمسارات والحزم والأصول غير المستخدمة | IN PROGRESS — inventory exists; worker/scripts/assets remain |
| CLN-03 | تنظيف تدريجي مبني على دليل مع اختبار كل دفعة | IN PROGRESS — BATCH 01/02 implemented |
| CLN-04 | مراجعة السيناريوهات والتعارضات والأداء | IN PROGRESS — CA-01..03/05..09 fixed; CA-04/10 open |
| CLN-05 | مراجعة بصرية شاملة للطالب والمشرف | PENDING FINAL REVIEW |
| CLN-06 | توثيق موحد نهائي وتجهيز مرشح دمج | IN PROGRESS — unified handoff created; archive/RC pending |
| CLN-07 | أرشفة تنظيمية للـhandoffs/checkpoints المؤرخة وإصلاح الروابط | PENDING |
| CLN-08 | حسم Worker وseed/repair scripts والأصول المرشحة | PENDING |

## قرارات تمنع الإغلاق النهائي

| ID | البند | الحالة |
|---|---|---|
| CA-04 | حسم التداخل الأكاديمي بين `L3-REIN-03` و`L3-REIN-12` | OWNER / ACADEMIC DECISION |
| CA-10 | قيود DB دفاعية إضافية | DEFERRED UNTIL BACKUP/RESTORE APPROVAL |

## بنود خارجية أو مؤجلة

| ID | البند | الحالة |
|---|---|---|
| OI-ASR | مزود ASR الإنتاجي والمعايرة والخصوصية | EXTERNAL / EXCLUDED |
| OI-RETENTION | سياسة الاحتفاظ بتسجيلات وبيانات الأطفال | OWNER / ETHICS DECISION |
| OI-STUDY | معلمات البروتوكول البحثي النهائي | OWNER / RESEARCH DECISION |
| OI-A11Y-HUMAN | قبول بشري يدوي لقارئ الشاشة | NOT CLAIMED |
| OI-DOMAIN | النطاق والهوية النهائية إن طُلبت | OPTIONAL |
| OI-BACKUP | جدولة Backup إنتاجي ونسخة مستقلة للصوت | DEFERRED BY OWNER |

لا يُعاد فتح عمل مغلق إلا بدليل regression جديد، ولا تُنفذ عملية حذف أو migration مدمرة ما دام النسخ الإنتاجي مؤجلًا.
