# جرد الفروع الحالي — هِمّة

**Reviewed:** 2026-09-18  
**Official functional SHA:** 512f0a550eb098f0ce904ec4ed526d9e28098a6a  
**Scope:** كل الفروع ما عدا فروع مزود/مختبر الصوت، حسب طلب المالك.

## الحكم

لا يوجد non-audio branch يحمل feature حديثة مطلوبة ومفقودة من stage/02-content.

كل الفروع غير الصوتية إما:
- مطابقة للـofficial functional SHA،
- أو ancestor/contained داخل الرسمي،
- أو deployment/platform-sandbox المتشعب القديم والمستبعد عمدًا.

## الفروع المراجعة

| الفرع | HEAD عند المراجعة | العلاقة بالـofficial | القرار |
|---|---|---|---|
| stage/02-content | 512f0a5 | identical | OFFICIAL |
| fix/ux-polish-audit-2026-09-18 | 512f0a5 | identical | contained / no merge |
| integration/ux-polish-audit-20260918 | 512f0a5 | identical | contained / no merge |
| fix/ux-system-rebuild-2026-09-17 | ed4ee38 | ancestor; official ahead 16 | historical contained |
| stage/ux-system-rebuild-ci | ed4ee38 | ancestor; official ahead 16 | historical contained |
| integration/ux-system-rebuild-m09-20260917 | ed4ee38 | ancestor; official ahead 16 | historical contained |
| integration/ux-system-rebuild-m09-run | ed4ee38 | ancestor; official ahead 16 | historical contained |
| fix/ux-audio-review-flow-2026-09-17 | ce8a9e4 | ancestor; official ahead 57 | contained |
| integration/ux-audio-review-flow-2026-09-17 | 765c42d | ancestor; official ahead 56 | contained |
| release/2026-09-17-final | 11e45b7 | ancestor; official ahead 88 | contained |
| release/2026-09-17 | 5f30221 | ancestor; official ahead 91 | contained |
| audit/comprehensive-repository-review-2026-09-10 | 5f30221 | ancestor; official ahead 91 | contained |
| integration/a10-w6-release-readiness | 29469d0 | ancestor; official ahead 110 | contained |
| integration/a10-w6-readiness | 162e17a | ancestor; official ahead 112 | contained |
| stage/a10-w5-ci | 728025a | ancestor; official ahead 134 | contained |
| stage/a10-w4-ci | c26fc9f | ancestor; official ahead 159 | contained |
| stage/a10-w3-ci | 62e34b1 | ancestor; official ahead 228 | contained |
| stage/a10-w2-ci | 77ac721 | ancestor; official ahead 375 | contained |
| stage/a10-w1-ci | ea132c9 | ancestor; official ahead 422 | contained |
| audit-comprehensive-2026-09-10 | 7cb2192 | ancestor; official ahead 472 | contained |
| integration/canonical-content-2026-09-08 | 7cb2192 | ancestor; official ahead 472 | contained |
| integration/official-content-reconciliation-2026-09-08 | e27e20d | ancestor; official ahead 631 | contained |
| recovery/ui-media-admin-overhaul | e1cb0bb | ancestor; official ahead 634 | historical contained |
| b03/adaptive-learning-engine | 53666a0 | ancestor; official ahead 1139 | contained |
| b02/stage2-closure | 99a6dbd | ancestor; official ahead 1163 | contained |
| b02/student-assessment-lifecycle | 6a52938 | ancestor; official ahead 1190 | contained |
| b01/content-source-of-truth | 26d25e0 | ancestor; official ahead 1194 | contained |
| recovery/codex-baseline | e5fafe7 | ancestor; official ahead 1196 | historical contained |
| stage/04-production-slice | aa89aa8 | ancestor; official ahead 1201 | historical contained |
| stage/03-design-routes | 974598c | ancestor; official ahead 1205 | historical contained |
| recovery/p02-baseline | 41bc2af | ancestor; official ahead 1211 | historical contained |
| deployment/platform-sandbox | 4468575 | diverged: official unique 781 / branch unique 9 | DO NOT MERGE; obsolete deployment experiment |

## deployment/platform-sandbox

هذا الفرع الوحيد غير الصوتي الذي ليس ancestor كاملًا للرسمي. الـ9 commits الفريدة تخص تجربة نشر قديمة ومختلفة عن الحالة الحالية. Production الفعلي الآن Railway project friendly-dream بخدمات himma-api/himma-web/Postgres/Redis وbucket himma-audio؛ لذلك لا توجد حاجة لنقل topology التجريبية القديمة.

## فروع مزود/مختبر الصوت المستبعدة من هذه المصالحة

بناءً على طلب المالك لم تُعامل هذه الفروع كمصدر دمج للحالة الحالية:
- b04/asr-pipeline
- m08/speech-lab-google-stt
- b08/speech-lab-google-stt
- b08/arabic-pronunciation-lab
- b08/acoustic-pronunciation-evidence

وجودها لا يغير عقد Human Supervisor Review الحالي ولا يعني اعتماد Production ASR.

## قاعدة مستقبلية

قبل دمج أي فرع قديم:
1. compare against live stage/02-content.
2. افحص unique commits/files.
3. لا تعتمد اسم الفرع كدليل أهمية.
4. لا تعيد إدخال عقد superseded أو provider تجريبي.
