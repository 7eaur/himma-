# هِمّة — A02 Python Import Graph

**AST-based direct imports + workflow command references. No Docker.**

> عدم وجود direct import لا يعني أن الحذف آمن: قد يكون الملف CLI مستقلًا أو مرجع migration تاريخي. الهدف هو تقليل false positives من البحث النصي.

| candidate | prod importers | test importers | workflow refs | static class |
|---|---|---|---|---|
| `services/api/content_projection_digest.py` | `services/api/canonical_content_publisher.py`<br>`services/api/readiness.py`<br>`services/api/verify_canonical_seed_idempotency.py` | — | — | `DIRECT_PRODUCTION_IMPORT` |
| `services/api/db/seed.py` | — | — | `.github/workflows/audit-python-import-graph.yml`<br>`.github/workflows/ci.yml`<br>`.github/workflows/m09-release-readiness.yml` | `WORKFLOW_OR_COMMAND_REFERENCED` |
| `services/api/seed.py` | — | `services/api/test_activities.py`<br>`services/api/test_activities_v4.py`<br>`services/api/test_adaptation_recovery_regressions.py`<br>`services/api/test_adaptation_runtime_recovery.py`<br>`services/api/test_api.py`<br>`services/api/test_assessment_pending_audio_navigation.py`<br>`services/api/test_journey.py`<br>`services/api/test_manual_override_session_integrity.py`<br>`services/api/test_option_history_reconciliation.py`<br>`services/api/test_posttest_journey_gate.py`<br>`services/api/test_profile_audio_review_state.py`<br>`services/api/test_recovery_contracts.py`<br>`services/api/test_reinforcement_additions_seed.py`<br>`services/api/test_reinforcement_cycle_service.py`<br>`services/api/test_reinforcement_cycles.py`<br>`services/api/test_reinforcement_mapping_runtime.py`<br>`services/api/test_reinforcement_review.py`<br>`services/api/test_student_adaptation_scenario_matrix.py` | `.github/workflows/audit-python-import-graph.yml`<br>`.github/workflows/ci.yml`<br>`.github/workflows/m09-release-readiness.yml` | `WORKFLOW_OR_COMMAND_REFERENCED` |
| `services/api/seed_all.py` | `services/api/run_dev.py`<br>`services/api/verify_canonical_seed_idempotency.py` | `services/api/test_activity_audio_runtime.py`<br>`services/api/test_audio_adaptation_boundaries.py`<br>`services/api/test_content_runtime_additions.py`<br>`services/api/test_content_surface_parity.py`<br>`services/api/test_db_only_student_runtime.py`<br>`services/api/test_full_student_content_integrity.py`<br>`services/api/test_generated_sequence_assets.py`<br>`services/api/test_m03_reinforcement_end_to_end.py`<br>`services/api/test_m09_full_single_candidate_journey.py`<br>`services/api/test_onset_pair_student_surface.py`<br>`services/api/test_posttest_structured_presentation.py`<br>`services/api/test_readiness.py`<br>`services/api/test_seed_all.py`<br>`services/api/test_skill_reports_m07.py`<br>`services/api/test_structured_projection_runtime.py`<br>`services/api/test_student_experience_v2.py`<br>`services/api/test_student_presentation_order.py`<br>`services/api/test_student_question_experience.py` | `.github/workflows/audit-python-import-graph.yml`<br>`.github/workflows/ci.yml` | `ACTIVE_CANONICAL_ENTRYPOINT` |
| `services/api/seed_db_runtime_contract.py` | — | — | — | `NO_DIRECT_IMPORT_OR_WORKFLOW_REFERENCE` |
| `services/api/seed_l1_auditory_story_replacement.py` | — | — | — | `NO_DIRECT_IMPORT_OR_WORKFLOW_REFERENCE` |
| `services/api/seed_learning_posttest_experience_2026_09_01.py` | `services/api/seed_learning_posttest_projection_runtime.py` | — | — | `DIRECT_PRODUCTION_IMPORT` |
| `services/api/seed_learning_posttest_projection_runtime.py` | — | — | — | `NO_DIRECT_IMPORT_OR_WORKFLOW_REFERENCE` |
| `services/api/seed_pretest_experience_2026_09_01.py` | — | — | — | `NO_DIRECT_IMPORT_OR_WORKFLOW_REFERENCE` |
| `services/api/seed_reinforcement_additions.py` | — | `services/api/test_reinforcement_additions_seed.py` | — | `DIRECT_TEST_IMPORT_ONLY` |
| `services/api/seed_reinforcement_additions_v2.py` | — | — | — | `NO_DIRECT_IMPORT_OR_WORKFLOW_REFERENCE` |
| `services/api/seed_student_choice_corrections.py` | — | — | — | `NO_DIRECT_IMPORT_OR_WORKFLOW_REFERENCE` |
| `services/api/seed_student_experience_v2.py` | — | — | — | `NO_DIRECT_IMPORT_OR_WORKFLOW_REFERENCE` |
| `services/api/test_adaptation_recovery_regressions.py` | — | — | — | `NO_DIRECT_IMPORT_OR_WORKFLOW_REFERENCE` |
| `services/api/test_adaptation_runtime_recovery.py` | — | — | — | `NO_DIRECT_IMPORT_OR_WORKFLOW_REFERENCE` |
| `services/api/test_recovery_contracts.py` | — | — | — | `NO_DIRECT_IMPORT_OR_WORKFLOW_REFERENCE` |
| `services/api/test_reinforcement_additions_seed.py` | — | — | — | `NO_DIRECT_IMPORT_OR_WORKFLOW_REFERENCE` |
| `services/api/test_seed_all.py` | — | — | — | `NO_DIRECT_IMPORT_OR_WORKFLOW_REFERENCE` |
| `services/api/test_sep8_approval_projection.py` | — | — | — | `NO_DIRECT_IMPORT_OR_WORKFLOW_REFERENCE` |
| `services/api/test_structured_projection_runtime.py` | — | — | — | `NO_DIRECT_IMPORT_OR_WORKFLOW_REFERENCE` |
| `services/api/verify_canonical_seed_idempotency.py` | — | — | `.github/workflows/ci.yml`<br>`.github/workflows/m09-release-readiness.yml` | `WORKFLOW_OR_COMMAND_REFERENCED` |

## Runtime entrypoints checked

- `services/api/main.py` is the FastAPI runtime owner.
- `services/api/run_dev.py` is a local-development helper and imports `seed_all` lazily.
- Production release flows must remain migration/canonical-publication driven; legacy seed scripts are not assumed safe merely because they can be run manually.
