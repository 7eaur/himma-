# جرد التنظيف المؤكد — 2026-09-24

هذا الجرد خاص بفرع `improvement/himma-unified-v2-20260921`. لا يغيّر الإنتاج ولا يصرّح بالحذف تلقائيًا. التصنيف مبني على قراءة الكود والبحث عن الاستدعاءات وربط المسارات، وليس على أسماء الملفات فقط.

## النتيجة المختصرة

- جميع Routers الفعلية في `services/api/main.py` مركبة؛ لم يظهر Router إنتاجي يتيم.
- ظهر كود واجهة غير موصول، واعتماد npm مرتبط به فقط.
- ظهرت أصول افتراضية ومكررة بلا استدعاء إنتاجي مباشر، بحجم يقارب `1.4 MiB`.
- خدمة Worker الحالية مجرد heartbeat من 12 سطرًا، وليست مهيأة ضمن خدمات Railway الحالية.
- توجد Seed/repair scripts تاريخية؛ لا تُحذف كدفعة واحدة لأنها قد تكون أدوات صيانة أو أدلة ترحيل.
- التوثيق يحتوي 167 ملفًا، منها 40 ملف handoff، بحجم Markdown يقارب `0.93 MiB`. أصبحت حالته الحالية موحدة، أما نقله إلى أرشيف منظم فيكون كدفعة مستقلة.

## مرشحون مؤكدون لدفعة تنظيف أولى

| العنصر | الدليل | الإجراء المقترح | الخطر |
|---|---|---|---|
| `apps/web/src/components/StudentAudioReviewOverlay.tsx` | لا يوجد import أو render له في كود الإنتاج أو الاختبارات | حذف المكوّن بعد اختبار السيناريو الذي يغطيه `StudentAdaptiveHoldOverlay` | منخفض إلى متوسط |
| `apps/web/src/hooks/useAudioRecorder.ts` | لا يوجد استدعاء؛ صفحات النشاط والجلسة تنفذ التسجيل داخليًا | حذف الملف فقط بعد مقارنة سلوك التسجيل الحالي | منخفض |
| `apps/web/src/lib/idb.ts` | لا يوجد مستهلك لدواله | حذف الملف ثم حذف اعتماد `idb` وتحديث lockfile | منخفض |
| `apps/web/public/{file,globe,next,vercel,window}.svg` | قوالب Next الافتراضية؛ لا توجد إحالة من `apps/web/src` | حذف | منخفض جدًا |
| `apps/web/public/brand/logo-flat.svg` | لا توجد إحالة إنتاجية، وموسوم قديمًا unused | حذف بعد فحص بصري سريع للشعار المستخدم | منخفض |
| `apps/web/public/characters/boy-*.png` | نسخ مطابقة للنسخ داخل `characters/boy/` ولا تستدعيها الواجهة | حذف النسخ الخمس المكررة ذات الاسم المسطح | منخفض جدًا |
| صور الشخصيات غير المستدعاة | لا توجد إحالة إنتاجية مباشرة إلى `boy/{encourage,explain,success,try-again}.png` أو `girl/try-again.png` | حذف في دفعة أصول مستقلة بعد فحص المسارات الديناميكية | منخفض |
| `services/worker/main.py` | heartbeat فقط؛ لا استيراد ولا Docker/Workflow/Railway service يشغله | حذف مجلد Worker أو تحويله إلى خدمة حقيقية، ولا يُترك كميزة وهمية | منخفض حاليًا |

## عناصر يجب إبقاؤها الآن

| العنصر | السبب |
|---|---|
| `apps/web/src/app/characters/girl/idle.png/route.ts` | Redirect توافق محتمل لمسار قديم؛ يحتاج access-log evidence قبل الإزالة |
| `python-multipart` | قد يستخدمه FastAPI داخليًا لمعالجة upload/form حتى من دون import مباشر |
| `httpx` | مستخدم ضمن بيئة الاختبارات؛ الأفضل لاحقًا فصل متطلبات الإنتاج عن الاختبار بدل حذفه |
| `postcss`, `tailwindcss`, `@tailwindcss/postcss` | مستخدمة في pipeline البناء وملفات CSS/config |
| `verify_canonical_seed_idempotency.py` | مستدعى صراحة في CI وM09 |
| `seed.py`, `seed_all.py`, `db/seed.py` | مستدعاة في الاختبارات أو predeploy أو تشغيل التطوير |

## عناصر تحتاج قرارًا قبل الحذف

هذه الملفات بلا inbound production import ظاهر، لكن أسماءها وسياقها يبينان أنها أدوات ترحيل أو repair تاريخية، لذلك تُراجع كل واحدة مقابل Git history وعقود المحتوى قبل الأرشفة:

- `seed_db_runtime_contract.py`
- `seed_l1_auditory_story_replacement.py`
- `seed_learning_posttest_projection_runtime.py`
- `seed_pretest_experience_2026_09_01.py`
- `seed_reinforcement_additions_v2.py`
- `seed_student_choice_corrections.py`
- `seed_student_experience_v2.py`
- `validate_content_media_contract.py`
- `create_db.py`
- `speech_worker.py`

`learning_state_machine.py` ليس ميتًا بالكامل: يُستدعى من اختبارين حتى لو لم يكن على مسار runtime الحالي. يجب تحديد هل هو عقد domain مقصود أم بقايا قبل حذفه.

## ترتيب التنفيذ المقترح

1. حذف قوالب Next والنسخ الصورية المتطابقة فقط، ثم build وPlaywright.
2. حذف `idb.ts` و`idb` و`useAudioRecorder.ts` والمكوّن غير الموصول، ثم تشغيل الفحوص كاملة.
3. إزالة Worker الوهمي أو توثيق قرار تحويله إلى queue worker حقيقي.
4. نقل handoffs والتقارير المؤرخة إلى مسار أرشيف واضح من دون إعادة كتابة Git history.
5. مراجعة repair/seed scripts واحدًا واحدًا، مع اختبار canonical seed بعد كل دفعة.

## شروط قبول كل دفعة

- لا تغيير في `stage/02-content` أو Railway production.
- `git diff --check` وsecret scan ناجحان.
- frontend typecheck/lint/unit/build ناجحة.
- backend + migration drift + seed idempotency ناجحة.
- Playwright ناجح عند مس الملفات أو السيناريوهات التي يراها المستخدم.
- الالتزام صغير وقابل للتراجع، ودليله يضاف إلى `docs/ops/EVIDENCE_INDEX.md`.
