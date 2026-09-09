"""Build the single publishable Himma content release.

``canonical_content_compiler`` converts historical/approved content sources into
one structured academic release. This module is the final release boundary: it
projects the already-approved learner presentation, reapplies the newer
2026-09-08 academic overrides, verifies question coverage, resolves every
listening prompt against the approved audio manifest by semantic target,
re-hashes the result, and runs the fail-closed media inventory guard.

Nothing here writes to the database. The publisher receives only the returned
final object, so there is one canonical release and no post-publication repair
seed or positional media inference.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from canonical_content_compiler import compile_release
from canonical_media_guard import assert_media_contract, resolve_audio_asset
from content_approval_contract_2026_09_08 import (
    LEARNING_QUESTIONS,
    LEARNING_ROUND_QUESTIONS,
    POSTTEST_QUESTIONS,
    POSTTEST_STIMULUS_OVERRIDES,
    PRETEST_QUESTIONS,
)
from learning_presentation_2026_09_01 import apply_learning_presentation
from posttest_presentation_2026_09_01 import POSTTEST_PRESENTATION

ROOT = Path(__file__).resolve().parents[2]
BASELINE_SOURCE = ROOT / "packages" / "content" / "src" / "catalog.json"
ADDITION_SOURCES = (
    ROOT / "packages" / "content" / "src" / "reinforcement_additions_v1.json",
    ROOT / "packages" / "content" / "src" / "reinforcement_additions_v2.json",
)
READ = {"read_aloud", "timed_read_aloud"}

# These two story activities use their separately approved structured story
# sources/replacement rounds. They are intentionally not represented by one
# item-level question because every story round has its own question.
STRUCTURED_STORY_QUESTION_SOURCES = {"L1-CORE-09", "L1-REIN-11"}


def _rehash(release: dict[str, Any]) -> dict[str, Any]:
    value = deepcopy(release)
    value.pop("sha256", None)
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    value["sha256"] = hashlib.sha256(raw).hexdigest()
    return value


def _canonical_ids(release: dict[str, Any], kind: str) -> set[str]:
    return {
        str(item.get("canonical_id") or "").strip()
        for item in release.get("items") or []
        if str(item.get("kind") or "") == kind
    }


def _assert_exact_ids(label: str, actual: set[str], expected: set[str]) -> None:
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        raise RuntimeError(f"{label} structured question coverage mismatch: missing={missing} extra={extra}")


def assert_question_contract_coverage(release: dict[str, Any]) -> None:
    """Refuse publication if any learner question falls back to raw legacy copy.

    Historical sources remain legal migration inputs for durable IDs, criteria,
    and unchanged structural fields. Student-facing question copy, however, must
    be accounted for by the approved September contract or by one of the two
    explicitly approved structured story sources.
    """
    _assert_exact_ids(
        "pretest",
        _canonical_ids(release, "pretest_question"),
        set(PRETEST_QUESTIONS),
    )
    _assert_exact_ids(
        "posttest",
        _canonical_ids(release, "posttest_question"),
        set(POSTTEST_QUESTIONS),
    )

    learning_ids = _canonical_ids(release, "core_activity") | _canonical_ids(release, "reinforcement_activity")
    structured_learning = set(LEARNING_QUESTIONS) | set(LEARNING_ROUND_QUESTIONS) | STRUCTURED_STORY_QUESTION_SOURCES
    _assert_exact_ids("learning", learning_ids, structured_learning)

    # Round-specific contracts must cover every durable round of the item. The
    # compiler also checks this while applying them; keeping the invariant at the
    # release boundary prevents a future compiler refactor from weakening it.
    by_id = {str(item.get("canonical_id") or ""): item for item in release.get("items") or []}
    for canonical, questions in LEARNING_ROUND_QUESTIONS.items():
        rounds = list((by_id.get(canonical) or {}).get("rounds") or [])
        if len(rounds) != len(questions):
            raise RuntimeError(
                f"{canonical}: structured round-question count={len(questions)} but release rounds={len(rounds)}"
            )

    for canonical in STRUCTURED_STORY_QUESTION_SOURCES:
        rounds = list((by_id.get(canonical) or {}).get("rounds") or [])
        if not rounds or any(not str(step.get("question_text") or "").strip() for step in rounds):
            raise RuntimeError(f"{canonical}: approved story source has an empty question round")


def _apply_posttest_presentation(release: dict[str, Any]) -> None:
    """Project the structured Sep-01 posttest without reintroducing an overlay.

    The retired DB seeder used to own stimulus/instruction/encouragement for the
    posttest. Those values are now a pure source and are folded into the final
    in-memory release before publication. The newer Sep-08 stimulus corrections
    are applied last, so POST-Q11 remains ``مَ`` rather than the historical ``مِ``.
    """
    by_id = {
        str(item.get("canonical_id") or ""): item
        for item in release.get("items") or []
        if str(item.get("kind") or "") == "posttest_question"
    }
    if set(by_id) != set(POSTTEST_PRESENTATION):
        raise RuntimeError(
            "Structured posttest presentation coverage mismatch: "
            f"release={sorted(by_id)} source={sorted(POSTTEST_PRESENTATION)}"
        )

    for canonical, presentation in POSTTEST_PRESENTATION.items():
        item = by_id[canonical]
        rounds = list(item.get("rounds") or [])
        if len(rounds) != 1:
            raise RuntimeError(f"{canonical}: posttest presentation expects exactly one round")
        step = rounds[0]
        item["presentation_skill"] = str(presentation["skill"])
        step["instruction_text"] = str(presentation["instruction_text"])
        step["encouragement"] = str(presentation["encouragement"])
        step["stimulus"] = deepcopy(presentation["stimulus"])

        expected = presentation.get("expected_reading_text")
        if expected is not None:
            if str(item.get("interaction_type") or "") not in READ:
                raise RuntimeError(f"{canonical}: structured reading stimulus targets a non-reading interaction")
            step["expected_reading_text"] = str(expected)
            step["options"] = []

    # Sep-08 is newer and authoritative for changed stimulus semantics.
    for canonical, stimulus in POSTTEST_STIMULUS_OVERRIDES.items():
        by_id[canonical]["rounds"][0]["stimulus"] = deepcopy(stimulus)


def _baseline_audio_targets() -> dict[tuple[str, int], str]:
    """Freeze unchanged listening semantics before later image-media replacement.

    The September approval changes several image pools without changing the sound
    heard by the learner (for example L1-CORE-04, L1-REIN-02 and POST-Q05).
    Replacing the image contract must not erase that independent audio target.
    The legacy catalog is used here only as a compile-time migration input; the
    resolved target is written into the final canonical release and runtime never
    parses this file.
    """
    if not BASELINE_SOURCE.is_file():
        raise RuntimeError(f"Missing baseline source needed for audio resolution: {BASELINE_SOURCE}")
    payload = json.loads(BASELINE_SOURCE.read_text(encoding="utf-8"))
    result: dict[tuple[str, int], str] = {}
    for item in payload.get("items") or []:
        canonical = str(item.get("canonical_id") or "").strip()
        for index, raw in enumerate(item.get("rounds") or [], 1):
            targets = {
                str(asset.get("semantic_text") or "").strip()
                for asset in raw.get("media") or []
                if str(asset.get("asset_type") or "") == "audio"
                and str(asset.get("usage") or "") == "prompt"
                and str(asset.get("semantic_text") or "").strip()
            }
            if len(targets) > 1:
                raise RuntimeError(f"Conflicting baseline prompt audio targets for {canonical}/R{index:02d}: {sorted(targets)}")
            if targets:
                result[(canonical, index)] = next(iter(targets))
    return result


def _addition_audio_targets() -> dict[tuple[str, int], str]:
    """Read explicit ``audio_text`` from approved reinforcement source files."""
    result: dict[tuple[str, int], str] = {}
    for path in ADDITION_SOURCES:
        if not path.is_file():
            raise RuntimeError(f"Missing reinforcement source needed for audio resolution: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload.get("items") or []:
            canonical = str(item.get("canonical_id") or "").strip()
            for index, raw in enumerate(item.get("rounds") or [], 1):
                target = str(raw.get("audio_text") or "").strip()
                if not target:
                    continue
                key = (canonical, index)
                if key in result and result[key] != target:
                    raise RuntimeError(f"Conflicting reinforcement audio target for {canonical}/R{index:02d}")
                result[key] = target
    return result


def _existing_prompt_target(step: dict[str, Any]) -> str | None:
    values = {
        str(asset.get("semantic_text") or "").strip()
        for asset in step.get("media") or []
        if str(asset.get("asset_type") or "") == "audio"
        and str(asset.get("usage") or "") == "prompt"
        and str(asset.get("semantic_text") or "").strip()
    }
    if len(values) > 1:
        raise RuntimeError(f"Listening round has conflicting prompt audio semantics: {sorted(values)}")
    return next(iter(values), None)


def _target_for_round(
    canonical: str,
    round_number: int,
    step: dict[str, Any],
    baseline_targets: dict[tuple[str, int], str],
    addition_targets: dict[tuple[str, int], str],
) -> str:
    stimulus = step.get("stimulus") or {}
    explicit = str(stimulus.get("audio_target") or "").strip() if isinstance(stimulus, dict) else ""
    source_target = addition_targets.get((canonical, round_number), "")
    existing = _existing_prompt_target(step) or ""
    baseline = baseline_targets.get((canonical, round_number), "")

    declared = [value for value in (explicit, source_target, existing, baseline) if value]
    if not declared:
        raise RuntimeError(f"{canonical}/R{round_number:02d}: listen interaction has no approved audio target")

    # Latest structured stimulus wins. Approved reinforcement source wins next.
    # Existing compiled prompt media is preferred to the historical baseline;
    # the baseline is only a recovery source when an independent image contract
    # intentionally replaced the media list earlier in compilation.
    target = explicit or source_target or existing or baseline
    if explicit and source_target and explicit != source_target:
        raise RuntimeError(
            f"{canonical}/R{round_number:02d}: conflicting explicit/source audio targets "
            f"{explicit!r} != {source_target!r}"
        )
    return target


def _resolve_listening_audio(release: dict[str, Any]) -> None:
    """Resolve every listening round by target semantics, never by old asset ID."""
    baseline_targets = _baseline_audio_targets()
    addition_targets = _addition_audio_targets()
    seen_addition_targets: set[tuple[str, int]] = set()

    for item in release.get("items") or []:
        interaction = str(item.get("interaction_type") or "")
        if not interaction.startswith("listen_"):
            continue
        canonical = str(item.get("canonical_id") or "")
        for step in item.get("rounds") or []:
            round_number = int(step.get("order_index") or 0)
            target = _target_for_round(
                canonical,
                round_number,
                step,
                baseline_targets,
                addition_targets,
            )
            if (canonical, round_number) in addition_targets:
                seen_addition_targets.add((canonical, round_number))
            asset_id = resolve_audio_asset(target)

            preserved = [
                value
                for value in step.get("media") or []
                if not (
                    str(value.get("asset_type") or "") == "audio"
                    and str(value.get("usage") or "") == "prompt"
                )
            ]
            preserved.append({
                "asset_id": asset_id,
                "asset_type": "audio",
                "usage": "prompt",
                "semantic_text": target,
            })
            step["media"] = preserved
            step["stimulus"] = {"kind": "audio", "audio_target": target}

    # An approved addition that declares audio_text must actually be a listening
    # round in the final contract; otherwise a later interaction change silently
    # orphaned its required media and must be reviewed explicitly.
    orphaned = sorted(set(addition_targets) - seen_addition_targets)
    if orphaned:
        labels = [f"{canonical}/R{round_number:02d}" for canonical, round_number in orphaned]
        raise RuntimeError(f"Approved reinforcement audio targets are orphaned: {labels}")


def build_canonical_release() -> dict[str, Any]:
    release = deepcopy(compile_release())
    apply_learning_presentation(release)
    _apply_posttest_presentation(release)
    assert_question_contract_coverage(release)
    _resolve_listening_audio(release)
    release = _rehash(release)
    assert_media_contract(release)
    return release


if __name__ == "__main__":
    current = build_canonical_release()
    print(json.dumps({
        "release_version": current["release_version"],
        "items": len(current["items"]),
        "sha256": current["sha256"],
        "media": "verified",
    }, ensure_ascii=False, indent=2))
