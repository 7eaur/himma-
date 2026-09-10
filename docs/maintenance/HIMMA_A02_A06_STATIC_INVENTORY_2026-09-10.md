# هِمّة — A02/A06 Static Inventory

**Generated from tracked files on the audit branch; no Docker and no runtime mutation.**

- Tracked files: **1075**
- Legacy-named Python candidates: **21**
- Admin page routes scanned: **11**
- `apps/web/public` files: **28**
- Public assets with zero direct source references: **17**
- Exact duplicate public SHA groups: **5**
- `assets/education` files: **208**
- Exact duplicate education SHA groups: **0**

> `UNREFERENCED_*` هنا لا يعني «احذف». يعني فقط أن الملف لا يملك مرجعًا نصيًا مباشرًا من ملف tracked آخر ويحتاج فهمًا يدويًا قبل القرار.

## 1. Legacy / Seed / Repair / Overlay / Projection candidates

| file | prod refs | test refs | docs refs | static hint |
|---|---:|---:|---:|---|
| `services/api/content_projection_digest.py` | 3 | 0 | 2 | `PRODUCTION_REFERENCED_REVIEW_REQUIRED` |
<!-- PROD services/api/content_projection_digest.py: services/api/canonical_content_publisher.py; services/api/readiness.py; services/api/verify_canonical_seed_idempotency.py -->
| `services/api/db/seed.py` | 25 | 36 | 35 | `PRODUCTION_REFERENCED_REVIEW_REQUIRED` |
<!-- PROD services/api/db/seed.py: .github/workflows/audit-static-inventory.yml; .github/workflows/ci.yml; .github/workflows/m09-release-readiness.yml; assets/education/ASSET_MANIFEST.json; assets/education/developer/asset-map.json; assets/education/developer/asset-map.ts; services/api/canonical_content_compiler.py; services/api/canonical_content_publisher.py; services/api/canonical_release.py; services/api/content_approval_contract_2026_09_08.py; services/api/learning_presentation_2026_09_01.py; services/api/reinforcement_mapping.py; services/api/run_dev.py; services/api/seed.py; services/api/seed_all.py; services/api/seed_db_runtime_contract.py; services/api/seed_l1_auditory_story_replacement.py; services/api/seed_learning_posttest_experience_2026_09_01.py; services/api/seed_learning_posttest_projection_runtime.py; services/api/seed_pretest_experience_2026_09_01.py; services/api/seed_reinforcement_additions.py; services/api/seed_reinforcement_additions_v2.py; services/api/seed_student_choice_corrections.py; services/api/seed_student_experience_v2.py; services/api/verify_canonical_seed_idempotency.py -->
<!-- TEST services/api/db/seed.py: services/api/test_activities.py; services/api/test_activities_v4.py; services/api/test_activity_audio_runtime.py; services/api/test_adaptation_recovery_regressions.py; services/api/test_adaptation_runtime_recovery.py; services/api/test_api.py; services/api/test_assessment_pending_audio_navigation.py; services/api/test_audio_adaptation_boundaries.py; services/api/test_content_runtime_additions.py; services/api/test_content_surface_parity.py; services/api/test_db_only_student_runtime.py; services/api/test_full_student_content_integrity.py; services/api/test_generated_sequence_assets.py; services/api/test_journey.py; services/api/test_m03_reinforcement_end_to_end.py; services/api/test_m09_full_single_candidate_journey.py; services/api/test_manual_override_session_integrity.py; services/api/test_onset_pair_student_surface.py; services/api/test_option_history_reconciliation.py; services/api/test_posttest_journey_gate.py; services/api/test_posttest_structured_presentation.py; services/api/test_profile_audio_review_state.py; services/api/test_readiness.py; services/api/test_recovery_contracts.py; services/api/test_reinforcement_additions_seed.py; services/api/test_reinforcement_cycle_service.py; services/api/test_reinforcement_cycles.py; services/api/test_reinforcement_mapping_runtime.py; services/api/test_reinforcement_review.py; services/api/test_seed_all.py; services/api/test_skill_reports_m07.py; services/api/test_structured_projection_runtime.py; services/api/test_student_adaptation_scenario_matrix.py; services/api/test_student_experience_v2.py; services/api/test_student_presentation_order.py; services/api/test_student_question_experience.py -->
| `services/api/seed.py` | 25 | 36 | 35 | `PRODUCTION_REFERENCED_REVIEW_REQUIRED` |
<!-- PROD services/api/seed.py: .github/workflows/audit-static-inventory.yml; .github/workflows/ci.yml; .github/workflows/m09-release-readiness.yml; assets/education/ASSET_MANIFEST.json; assets/education/developer/asset-map.json; assets/education/developer/asset-map.ts; services/api/canonical_content_compiler.py; services/api/canonical_content_publisher.py; services/api/canonical_release.py; services/api/content_approval_contract_2026_09_08.py; services/api/db/seed.py; services/api/learning_presentation_2026_09_01.py; services/api/reinforcement_mapping.py; services/api/run_dev.py; services/api/seed_all.py; services/api/seed_db_runtime_contract.py; services/api/seed_l1_auditory_story_replacement.py; services/api/seed_learning_posttest_experience_2026_09_01.py; services/api/seed_learning_posttest_projection_runtime.py; services/api/seed_pretest_experience_2026_09_01.py; services/api/seed_reinforcement_additions.py; services/api/seed_reinforcement_additions_v2.py; services/api/seed_student_choice_corrections.py; services/api/seed_student_experience_v2.py; services/api/verify_canonical_seed_idempotency.py -->
<!-- TEST services/api/seed.py: services/api/test_activities.py; services/api/test_activities_v4.py; services/api/test_activity_audio_runtime.py; services/api/test_adaptation_recovery_regressions.py; services/api/test_adaptation_runtime_recovery.py; services/api/test_api.py; services/api/test_assessment_pending_audio_navigation.py; services/api/test_audio_adaptation_boundaries.py; services/api/test_content_runtime_additions.py; services/api/test_content_surface_parity.py; services/api/test_db_only_student_runtime.py; services/api/test_full_student_content_integrity.py; services/api/test_generated_sequence_assets.py; services/api/test_journey.py; services/api/test_m03_reinforcement_end_to_end.py; services/api/test_m09_full_single_candidate_journey.py; services/api/test_manual_override_session_integrity.py; services/api/test_onset_pair_student_surface.py; services/api/test_option_history_reconciliation.py; services/api/test_posttest_journey_gate.py; services/api/test_posttest_structured_presentation.py; services/api/test_profile_audio_review_state.py; services/api/test_readiness.py; services/api/test_recovery_contracts.py; services/api/test_reinforcement_additions_seed.py; services/api/test_reinforcement_cycle_service.py; services/api/test_reinforcement_cycles.py; services/api/test_reinforcement_mapping_runtime.py; services/api/test_reinforcement_review.py; services/api/test_seed_all.py; services/api/test_skill_reports_m07.py; services/api/test_structured_projection_runtime.py; services/api/test_student_adaptation_scenario_matrix.py; services/api/test_student_experience_v2.py; services/api/test_student_presentation_order.py; services/api/test_student_question_experience.py -->
| `services/api/seed_all.py` | 4 | 18 | 8 | `ACTIVE_CANONICAL_ENTRYPOINT` |
<!-- PROD services/api/seed_all.py: .github/workflows/audit-static-inventory.yml; .github/workflows/ci.yml; services/api/run_dev.py; services/api/verify_canonical_seed_idempotency.py -->
<!-- TEST services/api/seed_all.py: services/api/test_activity_audio_runtime.py; services/api/test_audio_adaptation_boundaries.py; services/api/test_content_runtime_additions.py; services/api/test_content_surface_parity.py; services/api/test_db_only_student_runtime.py; services/api/test_full_student_content_integrity.py; services/api/test_generated_sequence_assets.py; services/api/test_m03_reinforcement_end_to_end.py; services/api/test_m09_full_single_candidate_journey.py; services/api/test_onset_pair_student_surface.py; services/api/test_posttest_structured_presentation.py; services/api/test_readiness.py; services/api/test_seed_all.py; services/api/test_skill_reports_m07.py; services/api/test_structured_projection_runtime.py; services/api/test_student_experience_v2.py; services/api/test_student_presentation_order.py; services/api/test_student_question_experience.py -->
| `services/api/seed_db_runtime_contract.py` | 1 | 0 | 1 | `PRODUCTION_REFERENCED_REVIEW_REQUIRED` |
<!-- PROD services/api/seed_db_runtime_contract.py: services/api/seed_l1_auditory_story_replacement.py -->
| `services/api/seed_l1_auditory_story_replacement.py` | 0 | 0 | 1 | `DOC_ONLY_OR_STANDALONE_CANDIDATE` |
| `services/api/seed_learning_posttest_experience_2026_09_01.py` | 1 | 0 | 0 | `PRODUCTION_REFERENCED_REVIEW_REQUIRED` |
<!-- PROD services/api/seed_learning_posttest_experience_2026_09_01.py: services/api/seed_learning_posttest_projection_runtime.py -->
| `services/api/seed_learning_posttest_projection_runtime.py` | 0 | 1 | 2 | `TEST_ONLY_REFERENCED_REVIEW_REQUIRED` |
<!-- TEST services/api/seed_learning_posttest_projection_runtime.py: services/api/test_structured_projection_runtime.py -->
| `services/api/seed_pretest_experience_2026_09_01.py` | 0 | 0 | 0 | `UNREFERENCED_STANDALONE_CANDIDATE` |
| `services/api/seed_reinforcement_additions.py` | 0 | 1 | 0 | `TEST_ONLY_REFERENCED_REVIEW_REQUIRED` |
<!-- TEST services/api/seed_reinforcement_additions.py: services/api/test_reinforcement_additions_seed.py -->
| `services/api/seed_reinforcement_additions_v2.py` | 0 | 0 | 0 | `UNREFERENCED_STANDALONE_CANDIDATE` |
| `services/api/seed_student_choice_corrections.py` | 1 | 0 | 1 | `PRODUCTION_REFERENCED_REVIEW_REQUIRED` |
<!-- PROD services/api/seed_student_choice_corrections.py: services/api/canonical_content_compiler.py -->
| `services/api/seed_student_experience_v2.py` | 0 | 0 | 2 | `DOC_ONLY_OR_STANDALONE_CANDIDATE` |
| `services/api/test_adaptation_recovery_regressions.py` | 0 | 0 | 0 | `UNREFERENCED_STANDALONE_CANDIDATE` |
| `services/api/test_adaptation_runtime_recovery.py` | 0 | 0 | 0 | `UNREFERENCED_STANDALONE_CANDIDATE` |
| `services/api/test_recovery_contracts.py` | 0 | 0 | 0 | `UNREFERENCED_STANDALONE_CANDIDATE` |
| `services/api/test_reinforcement_additions_seed.py` | 0 | 0 | 0 | `UNREFERENCED_STANDALONE_CANDIDATE` |
| `services/api/test_seed_all.py` | 0 | 0 | 2 | `DOC_ONLY_OR_STANDALONE_CANDIDATE` |
| `services/api/test_sep8_approval_projection.py` | 0 | 0 | 2 | `DOC_ONLY_OR_STANDALONE_CANDIDATE` |
| `services/api/test_structured_projection_runtime.py` | 0 | 0 | 0 | `UNREFERENCED_STANDALONE_CANDIDATE` |
| `services/api/verify_canonical_seed_idempotency.py` | 2 | 0 | 2 | `PRODUCTION_REFERENCED_REVIEW_REQUIRED` |
<!-- PROD services/api/verify_canonical_seed_idempotency.py: .github/workflows/ci.yml; .github/workflows/m09-release-readiness.yml -->

## 2. Admin page standardization static scan

| page | imports/uses AdminUI primitives? | local CSS modules |
|---|---|---|
| `apps/web/src/app/admin/(dashboard)/account/page.tsx` | no | `../admin.module.css` |
| `apps/web/src/app/admin/(dashboard)/audio-review/page.tsx` | yes | — |
| `apps/web/src/app/admin/(dashboard)/content-preview/page.tsx` | yes | — |
| `apps/web/src/app/admin/(dashboard)/page.tsx` | yes | `./admin.module.css` |
| `apps/web/src/app/admin/(dashboard)/reports/page.tsx` | yes | — |
| `apps/web/src/app/admin/(dashboard)/settings/page.tsx` | no | `./settings.module.css` |
| `apps/web/src/app/admin/(dashboard)/skill-reports/page.tsx` | yes | — |
| `apps/web/src/app/admin/(dashboard)/students/[id]/page.tsx` | no | `./student-detail.module.css` |
| `apps/web/src/app/admin/(dashboard)/students/new/page.tsx` | yes | — |
| `apps/web/src/app/admin/(dashboard)/students/page.tsx` | yes | — |
| `apps/web/src/app/admin/login/page.tsx` | no | — |

## 3. Public assets with zero direct references from `apps/web/src`

- `apps/web/public/audio/fb-complete.mp3` — 44973 bytes — sha `c50e0b6276da…`
- `apps/web/public/audio/fb-correct.mp3` — 25005 bytes — sha `bbef3a2864c9…`
- `apps/web/public/audio/fb-encourage.mp3` — 33837 bytes — sha `8b6d3a7f6797…`
- `apps/web/public/audio/fb-wrong.mp3` — 35373 bytes — sha `634d85e8fbf0…`
- `apps/web/public/brand/logo-flat.svg` — 8727 bytes — sha `195e949040ed…`
- `apps/web/public/characters/boy-encourage.png` — 136154 bytes — sha `d67ed19f2cd0…`
- `apps/web/public/characters/boy-explain.png` — 148188 bytes — sha `9ca9c95b7f90…`
- `apps/web/public/characters/boy-success.png` — 153165 bytes — sha `7cbf4ef2d929…`
- `apps/web/public/characters/boy-try-again.png` — 127660 bytes — sha `f14e6c87f511…`
- `apps/web/public/characters/boy-welcome.png` — 140633 bytes — sha `79fbcd53ce64…`
- `apps/web/public/characters/boy/try-again.png` — 127660 bytes — sha `f14e6c87f511…`
- `apps/web/public/characters/girl/try-again.png` — 127923 bytes — sha `4d2eb34f84b3…`
- `apps/web/public/file.svg` — 391 bytes — sha `2b67812c325c…`
- `apps/web/public/globe.svg` — 1035 bytes — sha `b614b9bf1839…`
- `apps/web/public/next.svg` — 1375 bytes — sha `55995dfad6ec…`
- `apps/web/public/vercel.svg` — 128 bytes — sha `f081337b2fee…`
- `apps/web/public/window.svg` — 385 bytes — sha `644768c4aaeb…`

## 4. Exact duplicate public binaries

- `apps/web/public/characters/boy-encourage.png` == `apps/web/public/characters/boy/encourage.png`
- `apps/web/public/characters/boy-explain.png` == `apps/web/public/characters/boy/explain.png`
- `apps/web/public/characters/boy-success.png` == `apps/web/public/characters/boy/success.png`
- `apps/web/public/characters/boy-try-again.png` == `apps/web/public/characters/boy/try-again.png`
- `apps/web/public/characters/boy-welcome.png` == `apps/web/public/characters/boy/welcome.png`

## 5. Referenced public assets

| asset | source files referencing it |
|---|---:|
| `apps/web/public/brand/logo-gradient.svg` | 3 |
<!-- REF apps/web/public/brand/logo-gradient.svg: apps/web/src/app/page.tsx; apps/web/src/app/student/login/page.tsx; apps/web/src/app/student/page.tsx -->
| `apps/web/public/brand/logo-navy.svg` | 6 |
<!-- REF apps/web/public/brand/logo-navy.svg: apps/web/src/app/admin/(dashboard)/layout.tsx; apps/web/src/app/admin/login/page.tsx; apps/web/src/app/page.tsx; apps/web/src/app/student/activity/[id]/page.tsx; apps/web/src/app/student/session/[id]/page.tsx; apps/web/src/components/StudentActivityStateBoundary.tsx -->
| `apps/web/public/brand/logo-white.svg` | 1 |
<!-- REF apps/web/public/brand/logo-white.svg: apps/web/src/app/admin/login/page.tsx -->
| `apps/web/public/characters/boy/encourage.png` | 5 |
<!-- REF apps/web/public/characters/boy/encourage.png: apps/web/src/app/student/activity/[id]/page.tsx; apps/web/src/app/student/page.tsx; apps/web/src/app/student/session/[id]/page.tsx; apps/web/src/components/StudentAdaptiveHoldOverlay.tsx; apps/web/src/components/StudentAudioReviewOverlay.tsx -->
| `apps/web/public/characters/boy/explain.png` | 3 |
<!-- REF apps/web/public/characters/boy/explain.png: apps/web/src/app/student/activity/[id]/page.tsx; apps/web/src/app/student/page.tsx; apps/web/src/app/student/session/[id]/page.tsx -->
| `apps/web/public/characters/boy/success.png` | 3 |
<!-- REF apps/web/public/characters/boy/success.png: apps/web/src/app/student/activity/[id]/page.tsx; apps/web/src/app/student/page.tsx; apps/web/src/app/student/session/[id]/page.tsx -->
| `apps/web/public/characters/boy/welcome.png` | 5 |
<!-- REF apps/web/public/characters/boy/welcome.png: apps/web/src/app/admin/login/page.tsx; apps/web/src/app/characters/girl/idle.png/route.ts; apps/web/src/app/page.tsx; apps/web/src/app/student/login/page.tsx; apps/web/src/app/student/page.tsx -->
| `apps/web/public/characters/girl/encourage.png` | 5 |
<!-- REF apps/web/public/characters/girl/encourage.png: apps/web/src/app/student/activity/[id]/page.tsx; apps/web/src/app/student/page.tsx; apps/web/src/app/student/session/[id]/page.tsx; apps/web/src/components/StudentAdaptiveHoldOverlay.tsx; apps/web/src/components/StudentAudioReviewOverlay.tsx -->
| `apps/web/public/characters/girl/explain.png` | 3 |
<!-- REF apps/web/public/characters/girl/explain.png: apps/web/src/app/student/activity/[id]/page.tsx; apps/web/src/app/student/page.tsx; apps/web/src/app/student/session/[id]/page.tsx -->
| `apps/web/public/characters/girl/success.png` | 3 |
<!-- REF apps/web/public/characters/girl/success.png: apps/web/src/app/student/activity/[id]/page.tsx; apps/web/src/app/student/page.tsx; apps/web/src/app/student/session/[id]/page.tsx -->
| `apps/web/public/characters/girl/welcome.png` | 5 |
<!-- REF apps/web/public/characters/girl/welcome.png: apps/web/src/app/admin/login/page.tsx; apps/web/src/app/characters/girl/idle.png/route.ts; apps/web/src/app/page.tsx; apps/web/src/app/student/login/page.tsx; apps/web/src/app/student/page.tsx -->

## 6. Exact duplicate binaries under `assets/education`

- None

## 7. Interpretation rules

1. لا يحذف أي Legacy candidate اعتمادًا على هذا التقرير وحده.
2. المرجع النصي المباشر لا يثبت أن المسار يُنفذ Runtime؛ يجب متابعة call graph والـentrypoints.
3. asset غير المشار إليه مباشرة قد يُستخدم عبر manifest/runtime mapping؛ لذلك A06 اليدوي يراجع manifests قبل وصفه orphan.
4. SHA duplicate يثبت تطابق bytes فقط، وليس أن حذف نسخة آمن؛ يجب فحص URLs/contracts أولًا.
5. AdminUI scan ثابت/تقريبي ويستخدم لتوجيه المراجعة اليدوية، لا كحكم UX نهائي.
