"""Environment-aware V2 media manifest/provider contract."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

from runtime_flags import trial_v2_preview_allowed


APPROVED_STATES = {"approved", "ready", "published"}
MISSING_STATES = {"missing", "missing_new"}


@dataclass(frozen=True)
class ResolvedMedia:
    asset_id: str
    kind: str
    state: str
    url: str | None
    test_only: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "kind": self.kind,
            "state": self.state,
            "url": self.url,
            "test_only": self.test_only,
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
        source_path = asset.get("source_path") or asset.get("v1_path")
        if status in APPROVED_STATES and source_path:
            return ResolvedMedia(asset_id, kind, "ready", f"/api/v2/media/{asset_id}", False)
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
