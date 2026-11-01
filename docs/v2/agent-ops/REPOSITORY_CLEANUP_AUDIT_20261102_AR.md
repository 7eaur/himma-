# هِمّة V2 — سجل فحص وتنظيف المستودع والفروع

**تاريخ الفحص:** 2026-11-02 (Asia/Aden)  
**المستودع:** https://github.com/7eaur/himma-  
**الفرع الجاري:** `v2/01-learning-foundation-20261007`  
**بصمة شجرة الفحص البنيوي:** `9e4e07dc17fc7fd934c6854265c2acf98ba64539` (قبل تعديلات التنظيف)  
**الحالة:** تنظيف تنظيمي جزئي مثبت؛ الإغلاق الشامل مشروط باستكمال جرد الفروع والاعتماديات والاختبارات.

## 1. نطاق الفحص وأدلته

- تمت قراءة بيانات المستودع والفروع الـ63 ورؤوسها؛ **الفرع الافتراضي ما زال `stage/02-content`** عند بدء التدقيق، رغم أن V2 في `v2/01-learning-foundation-20261007`.
- شجرة V2: 1,854 عنصرًا، منها نحو 396 مستند Markdown و281 ملف Python و96 ملف TSX؛ الأعداد للمؤشرات والجرد لا تعني أن كل الملف مستخدم أو مهجور.
- ملفات رئيسية تم تفحصها: `AGENTS.md`، `START_HERE_AR.md`، `VERSION.md`، `NEXT_CONVERSATION_PROMPT.md`، `apps/web/package.json`، `services/api/main.py`، `services/api/v1_student_guard.py`، `services/worker/`، `deploy/railway-*.Dockerfile`، `docker-compose.yml`، `.github/workflows/ci.yml`، مسارات الطالب التاريخية، وسجل R11/R12 والخطة الموحدة.
- اكتملت مقارنة GitHub Commit Graph لكل الفروع الـ62 مقابل V2: **47 فرعًا هي أسلاف لتاريخ V2 ولا تحمل commits زائدة (behind=0)**، و**15 فرعًا متباعدًا له commits مستقلة (behind>0)**. لا يُعتمد حذف المتباعدة قبل تدقيق الفروق؛ الأسلاف تحتاج فقط فحص مراجع النشر والحماية والروابط قبل حذف refs.
- لم يُشغَّل بناء محلي أو اختبار قاعدة بيانات؛ التحقق من بوابات GitHub المطلوبة يُجرى على SHA النهائي بعد اكتمال الدفعة.

## 2. المشاكل الهندسية والتنظيمية المكتشفة

| الشدة | الموضوع | الدليل / القرار |
|---|---|---|
| P0 تنظيمي | فرع GitHub الافتراضي V1 | `stage/02-content` وليس V2. يجب تغييره عبر Settings قبل حذف/تحييد الفرع القديم؛ تأكد أولًا من إعدادات Railway وCI وأي قواعد حماية وفروع متعلقة |
| P1 | تعارض تعاريف مصادر الحقيقة | ملفات الدخول والإصدار كانت تعلن V1 وفرع سبتمبر؛ عُدّلت لتشير إلى مصدر V2 الحي |
| P1 | بعض Router الخاصة بالـAPI القديمة ما زالت مسجلة | `services/api/main.py` يجمع routers قديمة وV2؛ يجب تتبّع المستهلكين وحواجز الصلاحيات والعقود قبل إزالة أي مسار |
| P1 | الحراسة التاريخية تحمي الطالب الحالي | `services/api/v1_student_guard.py` يمنع دخول رحلات V2 إلى مسارات V1؛ لا تحذفه دون اختبارات بديلة |
| P1 | ملفات الوسائط المسماة V1 قد تكون مستخدمة في V2 | `assets/audio/HIMMA_AUDIO_V1` يحتوي صوتيات تستهلكها عقود V2 وفق جرد المصدر؛ لا تحذفها لمجرد اسم المجلد |
| P2 | مساران تاريخيان للطالب | `/student/activity/[id]` و`/student/session/[id]` يعيدان التوجيه إلى `/student`؛ يفحص استخدامهما في الروابط الخارجية أولًا |
| P2 | Worker تجريبي غير تشغيلي | `services/worker/main.py` كان حلقة heartbeat لا تنفذ مهام، ولا تظهر في Dockerfiles لنشر Web/API أو compose؛ أزيل مع `requirements.txt` الخاص به. هذا ليس `services/api/speech_worker.py` |
| P2 | تكرار الوثائق والسجلات | `docs/` يحوي وثائق تاريخية واسعة، و`docs/v2/agent-ops/README_AR.md` كان يصف نظام A/B/C المتوقف؛ حُوّل المدخل إلى المصدر الواحد، ولا تُحذف بقية المستندات دون تدقيق الروابط |
| P2 | فروع متكررة ومتباعدة | سبع مجموعات لها رؤوس متطابقة؛ بعض الفروع الأخرى متباعدة وتحتفظ بـcommits فريدة |
| P2 | CI يتضمن متتبعات فروع تاريخية | `.github/workflows/ci.yml` يستمع إلى فئات `stage/*` و`recovery/*` وغيرها؛ راجع الأنماط بعد التخلص من الفروع، دون تعطيل CI/M04/M09 في V2 |

## 3. تغييرات نفذت فعليًا

1. إغلاق [PR #7](https://github.com/7eaur/himma-/pull/7) و[PR #8](https://github.com/7eaur/himma-/pull/8) باعتبارهما طلبين قديمين موجّهين لـV1؛ أضيف لكل منهما تفسير. **PR #7 متباعد ولم يُدمج حرفيًا، وما زالت commits في فرعه**.
2. تحديث `AGENTS.md`، `START_HERE_AR.md`، `VERSION.md`، `NEXT_CONVERSATION_PROMPT.md` على V2 لإزالة توجيه العمل الافتراضي إلى V1.
3. تحديث `docs/v2/agent-ops/README_AR.md`؛ نظام الوكلاء A/B/C السابق غير ساري و`CONTROL.json` يثبت تعطيله.
4. حذف الملفين غير المستخدمين لـ`services/worker/` دون تغيير عامل الصوت في API أو أي موارد قاعدة بيانات.
5. لم يُنفذ حذف أي فرع GitHub، ولا تغيير الفرع الافتراضي، ولا عملية على قاعدة بيانات الإنتاج، ولا نشر Railway؛ هذه أعمال مستقلة تحتاج دليلًا وصلاحية إجراء مناسبة.

## 4. علاقات الفروع المؤكدة بالمقارنة

`ahead` هو مقدار تقدم **V2 على الفرع المقارن**، و`behind` هو عدد commits الفريدة على الفرع المقارن بالنسبة إلى V2.

| الفرع | ahead | behind | القرار الأولي |
|---|---:|---:|---|
| `stage/02-content` | 1397 | 0 | سلف V2؛ احفظه حتى تغيير default وفحص الروابط |
| `archive/production-baseline-20260921` | 1397 | 0 | نفس SHA للـdefault، زائد تنظيميًا |
| `improvement/himma-unified-v2-20260921` | 1379 | 0 | سلف V2؛ PR #8 مغلق |
| `v2/work-owner-staging-20261027` | 587 | 0 | سلف V2 |
| `stage/04-production-slice` | 2672 | 0 | سلف V2 |
| `integration/a10-w6-readiness` | 1583 | 0 | سلف V2 |
| `stage/l1-mobile-learning-audit-20260921` | 1397 | 11 | متباعد؛ PR #7 مغلق لكن الكود الفريد لا يزال بحاجة تقويم |
| `cleanup/v2-only-20261027` | 614 | 16 | متباعد؛ يلزم تدقيق قبل الحذف |
| `video-production/gemini-handoff-20261018` | 1153 | 12 | متباعد؛ يلزم التحقق من أصول الوسائط |
| `b08/speech-lab-google-stt` | 2362 | 29 | متباعد وتجريبي؛ لا تدمج خدمات ASR أو API دون اعتماد منفصل |

### نتيجة المقارنة لجميع الفروع — 2026-11-02

- **47 فرعًا سلف لـV2**؛ يمكن إدراجها في قائمة حذف refs بعد نقل default والتحقق من الارتباطات، دون الحاجة لدمجها مجددًا.
- **15 فرعًا متباعدًا**؛ لا تُدمج أو تُحذف عشوائيًا؛ بعضها تجارب ASR/صوت وبعضها مراجعات UI قديمة، وتحتاج حسم وجود أي ميزة مطلوبة غير موجودة في V2.

| الفرع المتباعد | commits فريدة خارج V2 (behind) |
|---|---:|
| `audit/full-repository-review-20260921` | 12 |
| `b04/asr-pipeline` | 3 |
| `b08/acoustic-pronunciation-evidence` | 48 |
| `b08/arabic-pronunciation-lab` | 42 |
| `b08/speech-lab-google-stt` | 29 |
| `cleanup/v2-only-20261027` | 16 |
| `deployment/platform-sandbox` | 9 |
| `integration/audio-review-compact-20260920` | 8 |
| `m08/speech-lab-google-stt` | 9 |
| `redesign/audio-review-compact-20260920` | 5 |
| `stage/l1-mobile-learning-audit-20260921` | 11 |
| `stage/mobile-content-navigator-20260921` | 6 |
| `stage/speech-model-completion-20260921` | 39 |
| `ux/admin-content-library-20260921` | 5 |
| `video-production/gemini-handoff-20261018` | 12 |

## 5. فروع تشترك في SHA واحد (تكرار مثبت)

- SHA `4ecb27590f`: `archive/production-baseline-20260921`، `stage/02-content`.
- SHA `5f30221dd2`: `audit/comprehensive-repository-review-2026-09-10`، `release/2026-09-17`.
- SHA `7cb2192b0c`: `audit-comprehensive-2026-09-10`، `integration/canonical-content-2026-09-08`.
- SHA `512f0a550e`: `docs/current-state-2026-09-18`، `fix/ux-polish-audit-2026-09-18`، `integration/ux-polish-audit-20260918`.
- SHA `d15284d869`: `fix/audio-review-compact-workspace-20260920`، `integration/audio-review-compact-workspace-20260920`.
- SHA `658f7fc2d2`: `fix/student-dashboard-focus-20260920`، `integration/student-dashboard-focus-20260920`.
- SHA `ed4ee385bc`: `fix/ux-system-rebuild-2026-09-17`، `integration/ux-system-rebuild-m09-20260917`، `integration/ux-system-rebuild-m09-run`، `stage/ux-system-rebuild-ci`.

هذه مجموعات رؤوس متطابقة، وليست دليلًا وحده على عدم وجود مراجع خارج GitHub أو متطلبات حفظ.

## 6. السجل الكامل للفروع عند الجرد (63)

| الفرع | SHA مختصر | نتيجة المقارنة |
|---|---|---|
| `archive/production-baseline-20260921` | `4ecb2759` | سلف V2 — behind 0 |
| `audit/comprehensive-repository-review-2026-09-10` | `5f30221d` | سلف V2 — behind 0 |
| `audit/full-repository-review-20260921` | `6059ed39` | متباعد — behind 12 |
| `audit-comprehensive-2026-09-10` | `7cb2192b` | سلف V2 — behind 0 |
| `b01/content-source-of-truth` | `26d25e08` | سلف V2 — behind 0 |
| `b02/stage2-closure` | `99a6dbd6` | سلف V2 — behind 0 |
| `b02/student-assessment-lifecycle` | `6a529387` | سلف V2 — behind 0 |
| `b03/adaptive-learning-engine` | `53666a0a` | سلف V2 — behind 0 |
| `b04/asr-pipeline` | `46eb03c8` | متباعد — behind 3 |
| `b08/acoustic-pronunciation-evidence` | `a144a717` | متباعد — behind 48 |
| `b08/arabic-pronunciation-lab` | `4290ba9d` | متباعد — behind 42 |
| `b08/speech-lab-google-stt` | `4603d16e` | متباعد — behind 29 |
| `cleanup/v2-only-20261027` | `a0790ffa` | متباعد — behind 16 |
| `deployment/platform-sandbox` | `44685754` | متباعد — behind 9 |
| `docs/current-state-2026-09-18` | `512f0a55` | سلف V2 — behind 0 |
| `docs/final-production-closure-20260919` | `0b2fe96c` | سلف V2 — behind 0 |
| `fix/admin-audio-media-performance-20260919` | `c4b8e651` | سلف V2 — behind 0 |
| `fix/audio-review-compact-workspace-20260920` | `d15284d8` | سلف V2 — behind 0 |
| `fix/student-dashboard-focus-20260920` | `658f7fc2` | سلف V2 — behind 0 |
| `fix/ux-audio-review-flow-2026-09-17` | `ce8a9e4e` | سلف V2 — behind 0 |
| `fix/ux-polish-audit-2026-09-18` | `512f0a55` | سلف V2 — behind 0 |
| `fix/ux-system-rebuild-2026-09-17` | `ed4ee385` | سلف V2 — behind 0 |
| `improvement/himma-unified-v2-20260921` | `3eb97fd2` | سلف V2 — behind 0 |
| `integration/a10-w6-readiness` | `162e17a1` | سلف V2 — behind 0 |
| `integration/a10-w6-release-readiness` | `29469d00` | سلف V2 — behind 0 |
| `integration/admin-audio-media-performance-20260919` | `a261ef77` | سلف V2 — behind 0 |
| `integration/audio-review-compact-20260920` | `c602b67e` | متباعد — behind 8 |
| `integration/audio-review-compact-workspace-20260920` | `d15284d8` | سلف V2 — behind 0 |
| `integration/canonical-content-2026-09-08` | `7cb2192b` | سلف V2 — behind 0 |
| `integration/current-state-20260918` | `81006dcf` | سلف V2 — behind 0 |
| `integration/official-content-reconciliation-2026-09-08` | `e27e20d3` | سلف V2 — behind 0 |
| `integration/student-dashboard-focus-20260920` | `658f7fc2` | سلف V2 — behind 0 |
| `integration/ux-audio-review-flow-2026-09-17` | `765c42d7` | سلف V2 — behind 0 |
| `integration/ux-polish-audit-20260918` | `512f0a55` | سلف V2 — behind 0 |
| `integration/ux-system-rebuild-m09-20260917` | `ed4ee385` | سلف V2 — behind 0 |
| `integration/ux-system-rebuild-m09-run` | `ed4ee385` | سلف V2 — behind 0 |
| `m08/speech-lab-google-stt` | `85d93110` | متباعد — behind 9 |
| `recovery/codex-baseline` | `e5fafe75` | سلف V2 — behind 0 |
| `recovery/p02-baseline` | `41bc2af8` | سلف V2 — behind 0 |
| `recovery/ui-media-admin-overhaul` | `e1cb0bb3` | سلف V2 — behind 0 |
| `redesign/audio-review-compact-20260920` | `0cf65b0d` | متباعد — behind 5 |
| `release/2026-09-17-final` | `11e45b75` | سلف V2 — behind 0 |
| `release/2026-09-17` | `5f30221d` | سلف V2 — behind 0 |
| `stage/a10-w1-ci` | `ea132c9a` | سلف V2 — behind 0 |
| `stage/a10-w2-ci` | `77ac7217` | سلف V2 — behind 0 |
| `stage/a10-w3-ci` | `62e34b15` | سلف V2 — behind 0 |
| `stage/a10-w4-ci` | `c26fc9f9` | سلف V2 — behind 0 |
| `stage/a10-w5-ci` | `728025a8` | سلف V2 — behind 0 |
| `stage/admin-review-combined-20260921` | `23ce81bb` | سلف V2 — behind 0 |
| `stage/audio-review-playback-20260921` | `957b50f4` | سلف V2 — behind 0 |
| `stage/content-review-readonly-20260921` | `2981b534` | سلف V2 — behind 0 |
| `stage/l1-mobile-learning-audit-20260921` | `7008b34c` | متباعد — behind 11 |
| `stage/mobile-content-navigator-20260921` | `fe1a7287` | متباعد — behind 6 |
| `stage/speech-model-completion-20260921` | `7ce95c7d` | متباعد — behind 39 |
| `stage/ux-system-rebuild-ci` | `ed4ee385` | سلف V2 — behind 0 |
| `stage/02-content` | `4ecb2759` | سلف V2 — behind 0 |
| `stage/03-design-routes` | `974598c7` | سلف V2 — behind 0 |
| `stage/04-production-slice` | `aa89aa8e` | سلف V2 — behind 0 |
| `ux/admin-content-library-20260921` | `31f3c5e5` | متباعد — behind 5 |
| `ux/content-review-readonly-20260921` | `45cf678e` | سلف V2 — behind 0 |
| `v2/work-owner-staging-20261027` | `ad024302` | سلف V2 — behind 0 |
| `v2/01-learning-foundation-20261007` | `fdd05fc4` | V2 المعتمد |
| `video-production/gemini-handoff-20261018` | `d9843175` | متباعد — behind 12 |

## 7. إجراءات لازمة قبل إعلان مستودع موحد نظيف

1. **تثبيت المصدر الافتراضي:** بعد التأكد من إعدادات الإنتاج، تغيير Default branch إلى `v2/01-learning-foundation-20261007` في إعدادات GitHub. إجراء تغيير default branch **غير متاح من إجراءات GitHub المتصلة في هذه الجلسة**؛ لا يُقال إنه نُفّذ.
2. **تصنيف كل فرع:** تمت مقارنة الـ62 فرعًا جميعًا؛ تُراجع فروق الـ15 فرعًا المتباعدًا وتُحسم مطابقتها الوظيفية وتُفحص إعدادات النشر والـPRs والتوثيق قبل حذف الـ47 فرعًا التي لا تحمل commits فريدة؛ ثم إزالة الفروع الزائدة فقط بعد التأكد من عدم احتياج Railway/PRs/CI/tags إليها. حذف فروع GitHub **غير متاح عبر الإجراءات المتصلة حاليًا**.
3. **R12 ثم R13:** لا تخلط تنظيف البنية مع ادعاء إغلاق واجهات الطالب. اختبر رحلات الدخول والتسكين والتقوية والصوت والمراجعة والتقارير والخصوصية والتحميل قبل فصل Routers القديمة وإزالة التوافق أو seed/migration قديم.
4. **الاعتماديات والوسائط:** تحليل imports/references للـAPI وWeb وscripts، وتحديد ملفات `packages/content/src/*_v1.json` والوسائط المستخدمة فعليًا؛ ترحيل الأصول المستعملة بشكل منظم قبل حذف/إعادة تسمية أي ملف.
5. **تنظيف الوثائق:** الاحتفاظ بأقل عدد من أدلة التشغيل الحالية داخل working tree، وحفظ التاريخ في Git، بعد فحص روابط Markdown الداخلية التي تشير إلى الملفات المراد حذفها.
6. **اختبارات ونشر:** نجاح Frontend وBackend وSecurity وIntegration وM04 وM09 على SHA نهائي واحد، ثم إثبات وضع Web/API على Railway وفحص المستخدم والصلاحيات. التعديلات التنظيمية وحدها ليست اعتماد إصدار.
7. **فحص أخير:** ضمان عدم ظهور نصوص تطوير أو JSON/SQL، أو روابط V1، أو تداخل رسائل وأزرار وواجهات؛ وأن حذف الملفات لم يكسر استيرادًا أو اختبارًا أو نشرًا.

## 8. قاعدة سلامة الحذف

**يُحذف فقط** ما ثبت أنه غير مستورد وغير مرتبط بخدمة أو بيانات أو مسار مستخدم أو اختبار مرجعي لازم. الملفات الأصلية للصوت والبيانات الأكاديمية المحمية وحواجز V1→V2 ليست ملفات قابلة للحذف بمجرد وجود تسميات تاريخية.

هذا السجل **يوثق جرد رؤوس ومقارنة Commit Graph لجميع الفروع الـ63**، لكنه لا يساوي إتمام حذف الفروع أو تدقيق استخدام جميع 1,854 عنصرًا أو اعتماد نسخة إنتاجية نهائية دون الاختبارات وفحص الاستعمال والتشغيل.
