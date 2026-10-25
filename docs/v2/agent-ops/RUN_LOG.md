# سجل تشغيل الوكلاء — فهرس فقط

السجلات التفصيلية في `runs/YYYY-MM-DD/`، و`LATEST_HANDOFF.md` يشير لأحدث سجل موثوق. هذا الفهرس يُحدث بالـCAS وتُحفظ جميع الصفوف القديمة.

| local_time | agent | run_id | task | base_head → final_head | outcome | evidence |
|---|---|---|---|---|---|---|
| 2026-10-26 bootstrap | SYSTEM | — | Protocol only | `6c04bf8a3f1d` | PREPARED_NOT_EXECUTED | README_AR.md |

## ملاحظات تشغيل
- ترتيب التاريخ لا يغني عن HEAD؛ إذا حصل Run خارج الترتيب الزمني لا تستبدل latest handoff بآخر أقدم.
- إن فشل تحديث `RUN_LOG.md`، لا تُسقط نتيجة العمل: احفظ ملف run فريدًا ثم أعد بناء الفهرس على HEAD الأحدث.
