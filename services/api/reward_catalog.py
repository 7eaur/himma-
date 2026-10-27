"""Canonical reward presentation contract for Himma.

Persistence keeps immutable historical RewardEvent rows. This catalog owns the
current presentation identity (label + approved badge asset identity/path) so
API/UI consumers do not duplicate reward labels or infer assets from database
fields. Unknown historical reward keys remain readable and never receive a
fabricated asset identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


REWARD_CATALOG_VERSION = "HIMMA_REWARD_CATALOG_1.0.0"


@dataclass(frozen=True)
class RewardCatalogEntry:
    asset_id: str
    asset_slug: str
    asset_path: str
    label: str


_STARS_BY_COUNT = {
    1: RewardCatalogEntry("BDG-01", "star-one", "/assets/rewards/svg/hem-bdg-01-star-one.svg", "نجمة واحدة"),
    2: RewardCatalogEntry("BDG-02", "stars-two", "/assets/rewards/svg/hem-bdg-02-stars-two.svg", "نجمتان"),
    3: RewardCatalogEntry("BDG-03", "stars-three", "/assets/rewards/svg/hem-bdg-03-stars-three.svg", "ثلاث نجوم"),
}

_BADGES_BY_LEVEL = {
    1: RewardCatalogEntry("BDG-04", "letter-explorer", "/assets/rewards/svg/hem-bdg-04-letter-explorer.svg", "مستكشف الحروف"),
    2: RewardCatalogEntry("BDG-05", "word-hero", "/assets/rewards/svg/hem-bdg-05-word-hero.svg", "بطل الكلمات"),
    3: RewardCatalogEntry("BDG-06", "comprehension-star", "/assets/rewards/svg/hem-bdg-06-comprehension-star.svg", "نجم الفهم"),
}


def star_entry(stars: int) -> RewardCatalogEntry:
    try:
        return _STARS_BY_COUNT[int(stars)]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("stars must be one of 1, 2, 3") from exc


def badge_entry_for_level(level_id: int) -> RewardCatalogEntry:
    try:
        return _BADGES_BY_LEVEL[int(level_id)]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("level_id must be one of 1, 2, 3") from exc


def badge_levels() -> tuple[int, ...]:
    return tuple(_BADGES_BY_LEVEL)


def _catalog_row(*, catalog_key: str, reward_type: str, stars: int | None, reward_key: str | None, entry: RewardCatalogEntry, level_id: int | None = None) -> dict:
    row = {
        "catalog_key": catalog_key,
        "reward_type": reward_type,
        "stars": stars,
        "reward_key": reward_key,
        "label": entry.label,
        "asset_id": entry.asset_id,
        "asset_slug": entry.asset_slug,
        "asset_path": entry.asset_path,
    }
    if level_id is not None:
        row["level_id"] = level_id
    return row


def catalog_payload() -> dict:
    """Return the versioned public contract used by Student/Admin clients."""
    entries: list[dict] = []
    for stars, entry in _STARS_BY_COUNT.items():
        entries.append(_catalog_row(
            catalog_key=f"stars:{stars}",
            reward_type="stars",
            stars=stars,
            reward_key=None,
            entry=entry,
        ))
    for level_id, entry in _BADGES_BY_LEVEL.items():
        entries.append(_catalog_row(
            catalog_key=f"level:{level_id}:core-complete",
            reward_type="badge",
            stars=None,
            reward_key=f"level:{level_id}:core-complete",
            level_id=level_id,
            entry=entry,
        ))
    return {"version": REWARD_CATALOG_VERSION, "entries": entries}


def _entry_for_reward(reward: Any) -> RewardCatalogEntry | None:
    if str(getattr(reward, "reward_type", "")) == "stars":
        value = getattr(reward, "stars", None)
        try:
            return star_entry(int(value))
        except (TypeError, ValueError):
            return None

    if str(getattr(reward, "reward_type", "")) != "badge":
        return None

    key = str(getattr(reward, "reward_key", ""))
    prefix = "level:"
    suffix = ":core-complete"
    if not (key.startswith(prefix) and key.endswith(suffix)):
        return None
    raw_level = key[len(prefix) : -len(suffix)]
    try:
        return badge_entry_for_level(int(raw_level))
    except (TypeError, ValueError):
        return None


def present_reward(reward: Any) -> dict:
    """Serialize one persisted reward through the canonical presentation owner.

    ``recorded_label`` deliberately exposes the immutable persisted wording for
    audit/history compatibility. ``label`` is the current canonical UI label
    when the reward key resolves to a known catalog entry.
    """
    entry = _entry_for_reward(reward)
    recorded_label = str(getattr(reward, "label", ""))
    return {
        "id": getattr(reward, "id", None),
        "type": getattr(reward, "reward_type", None),
        "key": getattr(reward, "reward_key", None),
        "stars": getattr(reward, "stars", None),
        "label": entry.label if entry is not None else recorded_label,
        "recorded_label": recorded_label,
        "catalog_version": REWARD_CATALOG_VERSION,
        "asset_id": entry.asset_id if entry is not None else None,
        "asset_slug": entry.asset_slug if entry is not None else None,
        "asset_path": entry.asset_path if entry is not None else None,
        "details": getattr(reward, "details", None),
        "created_at": getattr(reward, "created_at", None),
    }
