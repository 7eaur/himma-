"""Ownership gates for current content publication versus historical seed layers."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from run_dev import validate_local_runtime_content_result


ROOT = Path(__file__).resolve().parent
HISTORICAL_SEED_MODULES = {
    "seed",
    "seed_db_runtime_contract",
    "seed_l1_auditory_story_replacement",
    "seed_learning_posttest_experience_2026_09_01",
    "seed_learning_posttest_projection_runtime",
    "seed_pretest_experience_2026_09_01",
    "seed_reinforcement_additions",
    "seed_reinforcement_additions_v2",
    "seed_student_choice_corrections",
    "seed_student_experience_v2",
}


def _imports(filename: str) -> set[str]:
    tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"), filename=filename)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    return imports


def _current_result() -> dict:
    return {
        "total_items": 125,
        "canonical_release_items": 125,
        "db_runtime_items": 125,
        "pretest_experience_items": 30,
        "learning_experience_items": 65,
        "posttest_experience_items": 30,
        "canonical_release_sha256": "a" * 64,
    }


def test_canonical_publication_path_does_not_execute_historical_seed_chain():
    seed_all_imports = _imports("seed_all.py")
    publisher_imports = _imports("canonical_content_publisher.py")

    assert "canonical_content_publisher" in seed_all_imports
    assert "canonical_release" in seed_all_imports
    assert seed_all_imports.isdisjoint(HISTORICAL_SEED_MODULES)
    assert publisher_imports.isdisjoint(HISTORICAL_SEED_MODULES)


def test_recovery_contract_runs_against_current_canonical_publication_world():
    """Current recovery behavior must not silently recreate the historical 105 world."""
    imports = _imports("test_recovery_contracts.py")

    assert "seed_all" in imports
    assert imports.isdisjoint(HISTORICAL_SEED_MODULES)


def test_local_dev_sync_points_to_seed_all_not_historical_repairs():
    imports = _imports("run_dev.py")
    source = (ROOT / "run_dev.py").read_text(encoding="utf-8")

    assert "seed_all" in imports
    assert imports.isdisjoint(HISTORICAL_SEED_MODULES)
    assert "student_experience_v2_items" not in source


def test_local_dev_sync_accepts_current_canonical_result_contract():
    validate_local_runtime_content_result(_current_result())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("total_items", 124),
        ("canonical_release_items", 124),
        ("db_runtime_items", 124),
        ("pretest_experience_items", 29),
        ("learning_experience_items", 64),
        ("posttest_experience_items", 29),
        ("canonical_release_sha256", "not-a-sha"),
    ],
)
def test_local_dev_sync_fails_closed_on_stale_or_partial_projection(field: str, value):
    result = _current_result()
    result[field] = value
    with pytest.raises(RuntimeError, match="approved canonical runtime contract"):
        validate_local_runtime_content_result(result)
