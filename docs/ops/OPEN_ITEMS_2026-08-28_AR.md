# البنود المفتوحة — هِمّة — تحديث بعد إغلاق M06 / بدء M07

هذا الملف أحدث من `OPEN_ITEMS.md` القديم عند التعارض الزمني.

| ID | البند | الحالة/الأثر | نقطة الحسم |
|---|---|---|---|
| OI-02 | مزود ASR/العقد/الكلفة/نقل التسجيلات | يوقف Real Speech adapter النهائي | M08 قبل real provider |
| OI-03 | Confidence threshold/version | يوقف decision الآلي الموثوق للصوت | بعد تسجيلات ممثلة ومعايرة |
| OI-04 | مدة التدخل وعدد/مدة الجلسات البحثية | إعداد بحثي خارجي | قبل بدء الدراسة الفعلية |
| OI-05 | سياسة الاحتفاظ بتسجيلات الأطفال | يوقف production child audio | قبل real child audio |
| OI-06 | domain/hosting/HTTPS النهائي | يوقف النشر | M09 |
| OI-07 | بيانات/شعارات الجهة المشرفة للتقارير النهائية إن طلبت | يؤثر على تسليم PDF النهائي | M07/M09 |
| OI-08 | تدوير أي أسرار استخدمت تاريخيًا والتحقق من production secrets | أمان إنتاجي | M09 |
| OI-10 | صوت «موز» | gap ثابت معلن؛ لا يُستبدل بـ«موزة» | قبل اكتمال الصوت الثابت |
| OI-11 | صوت «سَا» | gap ثابت معلن | قبل اكتمال الصوت الثابت |
| OI-12 | Automatic Demotion: هل يلغى من normal journey؟ | policy أكاديمية/منتجية غير محسومة؛ لا حذف صامت | قبل final adaptation sign-off/UAT |
| OI-13 | بوابة دقة القراءة/النص اللازمة للـL3 إذا كانت ستعتمد على الصوت الحقيقي | لا يجوز اختراع threshold | M08 calibration / academic approval |
| OI-M03-01 | L2: تقوية قراءة كلمات السكون | لا يوجد علاج مباشر approved؛ Safe Hold للمشرف | اعتماد mapping أو micro-reinforcement |
| OI-M03-02 | L3: تقوية الفهم المباشر | لا يوجد علاج مباشر approved | اعتماد mapping أو micro-reinforcement |
| OI-M03-03 | L3: تقوية بناء الجملة | لا يوجد علاج مباشر approved | اعتماد mapping أو micro-reinforcement |
| OI-15 | صور تقويات التسلسل/الإضافات التي لا توجد في الأصول الحالية | لا توقف المنطق؛ توقف اكتمال visual content | ستُولد داخليًا قبل UAT النهائي |
| OI-17 | Research reports Excel/PDF النهائية | **ACTIVE**؛ M07 بدأ بعد إغلاق M06 | M07 |
| OI-18 | Backup/restore + UAT + deployment/monitoring | يوقف release | M09 |

## بنود أُغلقت

- OI-M00: Run #206 الأحمر — **مغلق**؛ M00 أُنجز.
- Placement equal-weight scoring — **مغلق** عبر M01؛ 20/40/40 + readiness gate.
- M02 state machine الأساسي — **مغلق**.
- Skill-family mapping للـ33 تقوية — **نُفذ**؛ الباقي فقط الفجوات الثلاث أعلاه.
- Student Profile الطويل — **أعيد بناؤه Tabs** في M05.
- Settings الطويلة — **قُسمت Account/Security/Supervisors** في M05.
- OI-M06-01 — mobile supervisor selector/touch-target regression — **مغلق**. Main Quality Gate #314 (`33211325199`) على `cdb02c75...` أخضر بالكامل، والاختبار النهائي يستخدم semantic role/name مع الحفاظ على >=44px.
- OI-M06-02 — M06 screenshot review — **مغلق**. Responsive Visual Gate #22 (`33211325207`) أخضر، وتمت مراجعة responsive evidence ولقطة `18-mobile-supervisor-menu.png`.
- Responsive acceptance الأساسية على mobile/tablet/desktop — **مغلقة ضمن M06** للمصفوفة 360×800، 390×844، 768×1024، 1024×768، 1440×900.

## قرارات محسومة ولا تعاد مناقشتها بلا سبب جديد

- الواجهة تستخدم «المشرف».
- الطالب يدخل بكود رقمي 6 أرقام.
- لا Docker محليًا لهِمّة.
- no random reinforcement / no cross-level random fallback.
- 18 reinforcement additions معتمدة فوق 15 الأصلية.
- الصور الناقصة للإضافات سيتم توليدها داخليًا لاحقًا.
- TEMP_AUDIO_SKIP مؤقت ومحايد أكاديميًا.
- Reference-Guided Arabic Reading Analysis هو المعمار المستهدف للصوت.
- الصوت الثابت الحالي 50؛ المستهدف 52 بعد «موز» و«سَا».
- Placement يحدد نقطة البداية، ثم المسار يصعد إلى L3 قبل Posttest.
- >=80 pass، 70–<80 guided retry، <70 reinforcement path.
- لا ترقية مستوى قبل 10/10 core وعدم وجود فجوة علاجية غير محسومة.

## أول إجراء

M06 مغلق. أول إجراء حالي هو **M07 Research Reports**: تدقيق report API/UI/models/exports مقابل عقد M07 قبل إضافة أي منطق جديد، مع منع اختراع قياسات أو أخطاء صوتية غير موجودة في evidence الفعلية.
