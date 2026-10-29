"""Environment-aware V2 media manifest/provider contract."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import os
from pathlib import Path
from typing import Any

from .compiler import REPO_ROOT

from runtime_flags import trial_v2_preview_allowed


APPROVED_STATES = {"approved", "ready", "published", "approved_temporary"}
MISSING_STATES = {"missing", "missing_new"}
_ALLOWED_SUFFIXES = {"audio": {".mp3", ".wav", ".ogg", ".m4a"}, "image": {".webp", ".png", ".jpg", ".jpeg"}, "video": {".mp4", ".webm"}}
TEMPORARY_VIDEO = "assets/video/HIMMA_V2_DEMO/gemini_generated_video_72256b30.mp4"


@lru_cache(maxsize=16)
def _file_sha256(path: Path, size: int, mtime_ns: int, ctime_ns: int) -> str:
    """Hash a deployed binary once per file version, not once per lesson alias."""
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def approved_asset_path(asset: dict[str, Any]) -> Path | None:
    """Return only approved, present and safely rooted educational binaries."""
    status = str(asset.get("status") or "").lower()
    kind = str(asset.get("kind") or asset.get("type") or "")
    source = asset.get("source_path") or asset.get("v1_path")
    if status not in APPROVED_STATES or kind not in _ALLOWED_SUFFIXES or not isinstance(source, str) or not source.startswith("assets/"):
        return None
    root = (REPO_ROOT / "assets").resolve()
    path = (REPO_ROOT / source).resolve()
    if root not in path.parents or path.suffix.lower() not in _ALLOWED_SUFFIXES[kind] or not path.is_file():
        return None
    if path.stat().st_size == 0:
        return None
    if status == "approved_temporary":
        if kind != "video" or not str(asset.get("id", "")).startswith("VID-L") or source != TEMPORARY_VIDEO or asset.get("shared_temporary_video") is not True:
            return None
        digest = asset.get("source_sha256")
        file_stat = path.stat()
        if not isinstance(digest, str) or _file_sha256(path, file_stat.st_size, file_stat.st_mtime_ns, file_stat.st_ctime_ns) != digest:
            return None
    return path



@dataclass(frozen=True)
class ResolvedMedia:
    asset_id: str
    kind: str
    state: str
    url: str | None
    test_only: bool
    temporary: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "kind": self.kind,
            "state": self.state,
            "url": self.url,
            "test_only": self.test_only,
            "temporary": self.temporary,
        }


class MediaProvider:
    def __init__(self, *, environment: str | None = None, fixture_enabled: bool | None = None):
        self.environment = (environment or os.getenv("ENV", "development")).strip().lower()
        raw_setting = os.getenv("V2_FIXTURE_MEDIA_ENABLED")
        configured = self.environment != "production" if raw_setting is None else raw_setting.strip().lower() == "true"
        self.fixture_enabled = configured if fixture_enabled is None else fixture_enabled
        if self.environment == "production" and self.fixture_enabled:
            raise RuntimeError("V2 fixture media must never be enabled in production")

    def resolve(self, asset: dict[str, Any]) -> ResolvedMedia:
        asset_id = str(asset["id"])
        kind = str(asset.get("kind") or asset.get("type"))
        status = str(asset.get("status") or "missing").lower()
        if approved_asset_path(asset) is not None:
            return ResolvedMedia(asset_id, kind, "ready", f"/api/v2/content/media/{asset_id}", False, status == "approved_temporary")
        if self.fixture_enabled and (
            self.environment in {"development", "test", "staging"}
            or (self.environment == "trial" and trial_v2_preview_allowed())
        ):
            return ResolvedMedia(
                asset_id,
                kind,
                "ready",
                f"/api/v2/lessons/test-fixtures/{kind}/{asset_id}",
                True,
            )
        state = "missing" if status in MISSING_STATES else "pending"
        return ResolvedMedia(asset_id, kind, state, None, False)

    def assert_publishable(self, assets: list[dict[str, Any]]) -> None:
        unresolved = [
            result.asset_id
            for result in (self.resolve(asset) for asset in assets)
            if result.state != "ready" or result.test_only
        ]
        if unresolved:
            raise RuntimeError(f"release contains unresolved or TEST_ONLY media: {len(unresolved)}")
