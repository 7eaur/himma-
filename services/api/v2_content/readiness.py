"""P07 private supervisor-only media dependencies and approval blockers.

A candidate file or a TEST_ONLY preview is not an approved source.
No private answer keys or students' submitted evidence are included.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .compiler import REPO_ROOT
from .media import APPROVED_STATES, MISSING_STATES, MediaProvider, approved_asset_path


def usage_map(release: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    usages: dict[str, list[dict[str, str]]] = defaultdict(list)
    for lesson in release["lessons"]:
        usages[lesson["video_media_id"]].append({"owner_id": lesson["id"], "role": "teaching_video"})
    for support in release["supports"]:
        if support.get("video_media_id"):
            usages[support["video_media_id"]].append({"owner_id": support["id"], "role": "support_video"})
    for question in release["questions"]:
        for ref in (question.get("stimulus") or {}).get("media", []):
            usages[ref["media_id"]].append({"owner_id": question["id"], "role": "stimulus"})
        for option in question.get("options", []):
            for ref in option.get("media", []):
                usages[ref["media_id"]].append({"owner_id": question["id"], "role": "option"})
    return dict(usages)


def required_media_assets(release: dict[str, Any]) -> list[dict[str, Any]]:
    """Active lesson/question dependencies, excluding dormant authoring assets."""
    required = set(usage_map(release))
    return [asset for asset in release["media"] if asset["id"] in required]


def _candidate_path(asset: dict[str, Any]) -> Path | None:
    kind = str(asset.get("kind") or asset.get("type"))
    asset_id = str(asset.get("id") or "")
    if kind == "audio" and asset_id.startswith("AUD-") and "/" not in asset_id and "\\" not in asset_id:
        mp3 = REPO_ROOT / "assets/audio/HIMMA_AUDIO_V2/web_mp3" / f"{asset_id}.mp3"
        if mp3.is_file():
            return mp3
    source = asset.get("source_path") or asset.get("v1_path")
    if not isinstance(source, str) or not source.startswith("assets/"):
        return None
    root = (REPO_ROOT / "assets").resolve()
    path = (REPO_ROOT / source).resolve()
    return path if root in path.parents and path.is_file() else None


def media_readiness_contract(release: dict[str, Any], *, provider: MediaProvider | None = None) -> dict[str, Any]:
    provider = provider or MediaProvider()
    usages = usage_map(release)
    counts = {"ready": 0, "pending": 0, "missing": 0, "test_only": 0, "temporary": 0}
    by_kind: dict[str, int] = defaultdict(int)
    present = 0
    approved_count = 0
    required_total = 0
    unused_total = 0
    items = []
    for asset in release["media"]:
        resolved = provider.resolve(asset)
        kind = str(asset.get("kind") or asset.get("type"))
        source = str(asset.get("status") or "missing").lower()
        approved_file = approved_asset_path(asset)
        state = "ready" if source in APPROVED_STATES and approved_file else "missing" if source in MISSING_STATES else "pending"
        counts[state] += 1
        counts["test_only"] += int(resolved.test_only)
        counts["temporary"] += int(resolved.temporary)
        by_kind[kind] += 1
        candidate = _candidate_path(asset)
        present += int(candidate is not None)
        active = bool(usages.get(str(asset["id"])))
        required_total += int(active)
        unused_total += int(not active)
        approved_count += int(active and state == "ready" and not resolved.test_only)
        if resolved.temporary:
            preview_kind = "shared_approved_temporary_video"
        elif kind == "video" and resolved.test_only:
            preview_kind = "shared_test_only_video"
        elif kind == "audio" and str(asset["id"]).startswith("AUD-") and candidate is not None:
            preview_kind = "recorded_test_only_audio"
        else:
            preview_kind = f"generic_test_only_{kind}" if resolved.test_only else "no_preview"
        items.append({
            "asset_id": str(asset["id"]), "kind": kind,
            "preview_url": f'/api/v2/lessons/admin/media/{asset["id"]}' if resolved.state == "ready" else None,
            "state": state, "runtime_state": resolved.state, "test_only": resolved.test_only, "temporary": resolved.temporary,
            "source_status": source, "candidate_present": candidate is not None,
            "candidate_path": str(candidate.relative_to(REPO_ROOT)) if candidate else None,
            "uses": usages.get(str(asset["id"]), []),
            "preview_kind": preview_kind,
            "publication_blocker": active and (state != "ready" or resolved.test_only),
            "required_for_runtime": active,
            "rights_pending": bool(asset.get("rights_review_required")),
            "academic_qa_pending": state != "ready",
            "exact_spoken_text_private": asset.get("reference_spoken_private") if kind == "audio" else None,
            "required_format": {"video": "MP4 H.264/AAC + VTT", "audio": "MP3 (WAV master)", "image": "WebP/PNG + alt text"}[kind],
        })
    return {
        "mode": "read_only", "release_state": release["state"], "release_checksum": release["checksum"],
        "counts": counts, "items": items, "media_requirements": dict(sorted(by_kind.items())),
        "candidate_files_present": present, "published_assets": approved_count,
        "required_assets": required_total, "unused_assets": unused_total,
        "publishable": approved_count == required_total and bool(required_total),
        "test_only_warning": "TEST ONLY media never count as approved educational assets",
    }
