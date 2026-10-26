# توجيهات ومراجعات المشرف C

**الإصدار الابتدائي:** bootstrap 2026-10-26 · **الحالة:** توجيهات أساسية، وليست اعتمادًا لأي عمل لاحق.

## تعليمات نافذة للعاملين
- `D-001 | BLOCKER`: لا دمج `main` أو تعديل `stage/02-content` أو حذف بيانات/ملفات تسجيلات V1 أو تغيير قواعد التسكين/المحتوى/AI دون إذن صاحب المشروع.
- `D-002 | BLOCKER`: لا اعتبار P0 أو P09.1 مغلقًا ما لم تنجح بوابات CI Integration وM09 المطلوبة أو يسجّل المشرف بنفسه سبب الاستثناء ويوافق المالك.
- `D-003 | QUALITY`: قدّم السبب الجذري وفحص الرجوع بعد الإصلاح. حافظ على `null` للنتائج غير الرسمية، ولا تضع رموز الدخول أو مفاتيح الإجابات أو بيانات طفل فعلية في تقرير GitHub.
- `D-004 | CONFLICT`: لا تتنافس مع مهمة إنتاج الوسائط الصوتية، واحترم Lease و`expected_sha` عند GitHub commit.

## سجل قرار المشرف (إضافة لا حذف)
| الوقت المحلي | run_id/commit | النطاق | القرار | الدليل/السبب | توجيه للدورة التالية |
|---|---|---|---|---|---|
| 2026-10-26 bootstrap | — | إعداد البروتوكول | PENDING_GATES | لم يبدأ عامل؛ لا يوجد تسليم للمراجعة بعد | أول عامل يقرأ HEAD وفحوصه ويبدأ HV2-001 |

| 2026-10-26 03:50 | `20261026-0301-A` / `9669964c` | HV2-001 — إصلاح اختبار أرشيف V1 | **ACCEPTED (patch only)** | [CI 40247457135](https://github.com/7eaur/himma-/actions/runs/40247457135), [M04 40247457202](https://github.com/7eaur/himma-/actions/runs/40247457202), [M09 40247457124](https://github.com/7eaur/himma-/actions/runs/40247457124) = SUCCESS على SHA نفسه؛ diff حصر شارات/مستويات V1 داخل تبويب الأرشيف. هذا لا يغلق HV2-001 على HEAD الجديد. | A يراجع فشل بوابات أحدث ويثبت عدم تراجع عزل V1/V2 |
| 2026-10-26 03:50 | `20261026-0330-B` / `125f1bd6` | HV2-002 — أول دخول/حفظ/استئناف | **PENDING_GATES** | [CI 40250140780](https://github.com/7eaur/himma-/actions/runs/40250140780): frontend/backend/security SUCCESS وintegration لا يزال in_progress وقت المراجعة؛ M04 [40250140772](https://github.com/7eaur/himma-/actions/runs/40250140772) SUCCESS. مصدر E2E فيه حفظ عبر زر فعلي و503/retry، لكن لا دليل PASS كامل على نفس SHA بعد. | A يتابع integration وM09 على SHA المعني؛ B لا يعلن إغلاق الاختبار |
| 2026-10-26 03:50 | `20261026-0335-B` / `ec537832` | HV2-003 — عزل هوية Student360 | **REWORK** | [CI 40250486652](https://github.com/7eaur/himma-/actions/runs/40250486652) frontend ESLint FAIL، [job 121341076809](https://github.com/7eaur/himma-/actions/runs/40250486652/job/121341076809): **5 errors** في `apps/web/src/app/admin/(dashboard)/students/[id]/page.tsx`، عند 204 `react-hooks/set-state-in-effect`، وعند 493/504/545/582 `react-hooks/refs`. [M04 40250486661](https://github.com/7eaur/himma-/actions/runs/40250486661) SUCCESS فقط، M09 [40250486638](https://github.com/7eaur/himma-/actions/runs/40250486638) لم ينتهِ؛ لا قبول. | **B أولوية عاجلة:** أصلح سبب lint جذريًا بدون تعطيل القواعد؛ اعزل بيانات كل طالب بمفتاح id أو مكوّن keyed، واجعل استدعاءات retry لا تمرر ref/closures غير آمنة أثناء render؛ أثبت التنقل client-side بين ملفين + إبطاء GET + إخفاء الرمز، ثم lint/typecheck/Playwright/CI/M09 |

### سياسة التصنيف
- **ACCEPTED** = مراجعة مشرف على SHA والملفات والأدلة، لا تعني موافقة المالك على النشر.
- **REWORK** = اكتشاف خلل وإرفاق الموضع وسبب الإخفاق واختبار يكشفه ثم إعادة المهمة.
- **PENDING_GATES** = لم يكتمل CI/Playwright/لقطات أو العامل لم ينتهِ، فلا قبول مبكر.
- **BLOCKED** = اعتماد خارجي/أصل ناقص/صلاحية/تعارض يتطلب خطوة محددة.
- **PAUSED** = خطر سلامة أو خصوصية؛ اضبط `CONTROL.json.mode` مع السبب ووقف التعديلات.
