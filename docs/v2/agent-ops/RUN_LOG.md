# سجل تشغيل الوكلاء — فهرس فقط

السجلات التفصيلية في `runs/YYYY-MM-DD/`، و`LATEST_HANDOFF.md` يشير لأحدث سجل موثوق. هذا الفهرس يُحدث بالـCAS وتُحفظ جميع الصفوف القديمة.

| local_time | agent | run_id | task | base_head → final_head | outcome | evidence |
|---|---|---|---|---|---|---|
| 2026-10-26 bootstrap | SYSTEM | — | Protocol only | `6c04bf8a3f1d` | PREPARED_NOT_EXECUTED | README_AR.md |
| 2026-10-26 03:01–03:03 | A | 20261026-0301-A | HV2-001 | `79106bb66951` → `9669964cd438` | PENDING_GATES | `runs/2026-10-26/A-20261026-0301.md`; CI 40247457135, M09 40247457124 |

| 2026-10-26 03:30–03:34 | B | 20261026-0330-B | HV2-002 | `3ce39dd3fb75` → `6f860762c6d2` | PENDING_GATES | `runs/2026-10-26/B-20261026-0330.md`; latest functional `125f1bd6`; CI 40250140780 |

| 2026-10-26 03:35–03:40 | B | 20261026-0335-B | HV2-003 | `64765a41ae4e` → `ec537832fe2f` | PENDING_GATES | `runs/2026-10-26/B-20261026-0335.md`; CI 40250486652, M04 40250486661, M09 40250486638 |

| 2026-10-26 03:50 | C | 20261026-0350-C | HV2-001/002/003 | `d57cf40d5e5d` → supervisor docs commit | A patch ACCEPTED; B002 PENDING_GATES; B003 REWORK | `runs/2026-10-26/C-20261026-0350.md`; CI 40250486652 ESLint FAIL |

## ملاحظات تشغيل
- ترتيب التاريخ لا يغني عن HEAD؛ إذا حصل Run خارج الترتيب الزمني لا تستبدل latest handoff بآخر أقدم.
- إن فشل تحديث `RUN_LOG.md`، لا تُسقط نتيجة العمل: احفظ ملف run فريدًا ثم أعد بناء الفهرس على HEAD الأحدث.
