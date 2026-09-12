# NEXT CONVERSATION PROMPT — منصة هِمّة

استخدم هذا النص عند بدء محادثة جديدة لمتابعة التنفيذ دون إعادة العمل السابق:

---

أنت الآن المسؤول الهندسي الكامل عن **منصة هِمّة** في المستودع:

`7eaur/himma-`

فرع التنفيذ الحالي:

`audit/comprehensive-repository-review-2026-09-10`

ابدأ **فعليًا** بجلب HEAD الحالي للفرع، ولا تعتمد على SHA محفوظ دون التحقق منه.

بعدها اقرأ بالترتيب:

1. `docs/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-09-12_A10_W3_ACTIVE_AR.md`
2. `docs/maintenance/HIMMA_A10_W3_EXECUTION_CHECKPOINT_2026-09-12_AR.md`
3. `docs/ops/STATUS.md`
4. `docs/ops/progress.json`
5. `docs/maintenance/HIMMA_MASTER_GAP_REGISTER_2026-09-10_AR.md`
6. W1/W2 checkpoints عند الحاجة لإثبات التاريخ، ولا تعِد تنفيذهما.

اعتبر repository code + migrations + executable tests/CI + canonical content contracts هي Source of Truth التنفيذية.

## الحالة التي يجب أن تفهمها قبل أي تعديل

- A00–A09 = **CLOSED AUDIT**. لا تعِدها.
- A10/W1 = **CLOSED GREEN** على SHA `ea132c9afbe152d0afa5ae581c058ce3248a0c48`، Run ID `34467329988`, #813.
- A10/W2 = **CLOSED GREEN** على SHA `77ac72174a9e21163f6341ea8e0fcc172269eac3`، Run ID `34548388760`, #822.
- A10/W3 = **ACTIVE / NOT GREEN**.
- آخر code-bearing checkpoint الموثق قبل commits التوثيق = `3962d101b2c1ba4c5294235dfac797687209cbfb`.
- W3 CI #829 / Run ID `34703574228`: Security PASS، Backend PASS، TypeScript PASS، ESLint PASS، Frontend unit tests FAIL، Build skipped، Integration skipped.
- الفشل الحالي المثبت في BFF cache policy: upstream `private, no-store` لقراءة media يتم تحويله خطأ إلى `public, max-age=86400`.

## أول إجراء

تحقق هل يوجد commit أحدث من `3962...` أصلح هذا الخلل.

إذا لم يوجد، أصلح **root cause** في:

`apps/web/src/app/api/[...path]/cachePolicy.ts`

ولا تضعف الاختبار.

القاعدة الصحيحة:

- non-media / non-GET-HEAD / unsuccessful / Set-Cookie => `private, no-store`.
- upstream explicit `private` أو `no-store` => `private, no-store`.
- explicit safe public => preserve it.
- public 86400 fallback فقط عند غياب upstream cache header لقراءة approved media الناجحة.

بعد الإصلاح:

- commit على فرع audit.
- حرّك `stage/a10-w3-ci` إلى exact SHA الجديد فقط للتحقق.
- شغل Quality Gate كامل.
- لا تقل W3 Green حتى Security + Frontend + Backend + Integration/Playwright كلها PASS على SHA نفسه.

ثم أكمل **كل W3** وفق checkpoint/Gap Register، بما في ذلك AdminUI consistency، partial-source errors، canonical Journey، responsive matrix، dialogs/tabs accessibility، student-filtered audio review، local/build-time fonts، reduced motion، semantic contrast، progress semantics، وscenario integrity.

بعد W3 Green انتقل إلى W4 ثم W5 ثم W6. W4 يجب أن يغلق أيضًا ملاحظات الشارات/النجوم/الصور الموثقة: approved badge catalog، L3 `نجم الفهم` migration-compatible display، student/admin badge visuals، reward error state، stable asset/catalog identity، audio rerecord ضمن star retry semantics، وعدم منح pending audio reward مبكرًا.

## قيود ثابتة

- لا Docker.
- لا Merge أو Deploy أو Railway قبل W6 Green وحدود A11.
- لا fake ASR ولا Temporary Audio Skip.
- لا حذف academic/audio/reward history.
- لا دمج Speech/Pronunciation Lab branches؛ research only.
- `deployment/platform-sandbox` reference only.
- Production ASR غير معتمد؛ machine advisory وHuman Supervisor Review authority.
- لا تدّعي PASS دون exact-SHA evidence.
- لا تغيّر الاختبارات لإخفاء bug حقيقي؛ أصلح root cause.

لا تكتفِ بتقرير. أكمل التنفيذ من نقطة التوقف، وثّق كل batch وSHA وrun evidence داخل ملفات الاستمرارية.
