# Railway Production — Himma Current Release

**Verified:** 2026-09-24

## النسخة المنشورة

- Repository: `7eaur/himma-`.
- Branch: `stage/02-content`.
- SHA: `4ecb27590f7c19cbe7823804b9919d91000415ef`.
- Archive branch: `archive/production-baseline-20260921`.

## Railway

- Project: `friendly-dream`.
- Environment: `production`.
- Backend service deployment: `e9ae4753-bff0-46ce-8133-a330b18b0b34` — `SUCCESS`.
- Web service deployment: `55dff3b1-a2e3-41de-9416-edc9bc7757b0` — `SUCCESS`.
- PostgreSQL: `SUCCESS`.
- Redis: `SUCCESS`.
- Bucket: `himma-audio` موجود.

## الأدلة المرتبطة بالنسخة

- M04 #403 / Run `35551846252`: `SUCCESS`.
- M09 #268 / Run `35551846250`: `SUCCESS`.
- Full improvement gate after the documentation scanner fix: QG #1062 / Run `35660961118`: `SUCCESS`.

## قاعدة النشر

فرع التحسين غير مربوط بالإنتاج. لا يُدمج أو يُنشر إلا بعد اكتمال دفعة مترابطة، نجاح البوابات المطلوبة، ومراجعة سيناريوهات الاستخدام. لا تُنفذ migrations مدمرة خلال التنظيف الحالي.
