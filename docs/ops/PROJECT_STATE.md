# حالة مشروع هِمّة الحالية

**Current snapshot:** 2026-09-18

هذه الوثيقة حلت محل ملف "حالة المشروع عند بدء التطوير" القديم.

## المنتج الحالي

هِمّة منصة ويب عربية RTL تعمل بسطحين:
- طالب.
- مشرف.

المنصة لم تعد Prototype فقط؛ يوجد backend حقيقي، PostgreSQL migrations، auth، content runtime، student journeys، adaptation، audio review، reporting surfaces، CI release gates، وRailway production deployment.

## الحالة الهندسية

- Official branch: stage/02-content.
- Functional release: 512f0a550eb098f0ce904ec4ed526d9e28098a6a.
- QG/M04/M09: GREEN.
- Railway API/Web: SUCCESS.
- PostgreSQL/Redis/audio bucket: present.
- /ready healthcheck: 200 on deployed API.
- 15 Alembic migration files.
- canonical runtime: 125 items / 44 skills.

## الحالة الأكاديمية

- Placement <50 / 50..<80 / >=80.
- Activity 80/70 thresholds.
- 50/30/20 active-session evidence weighting.
- no automatic demotion.
- same-level targeted reinforcement.
- L3 terminal after 10 Core.
- posttest supervisor-enabled after learning completion.

## الصوت

- 54 static IDs / 108 binaries.
- Human Supervisor Review is authoritative.
- pending audio does not block remaining unanswered assessment questions.
- finalization waits for required reviews.
- rerecord explicit/history-preserving.
- no audio bypass.
- Production ASR is external/deferred.

## UX

آخر دفعة أعادت تنظيم:
- Student Dashboard/journey.
- question stimulus/options responsive rules.
- Audio Review.
- Admin Dashboard pending-audio aggregation.
- Student Profile.
- Add Student.
- Content Preview.
- feedback/toasts.
- responsive/mobile/RTL behavior.

## ما ليس جزءًا من الإغلاق

- Production ASR provider.
- manual human screen-reader acceptance.
- owner/ethics decisions الخاصة بالاحتفاظ والبروتوكول البحثي النهائي.
