"""Validate the complete final Himma media contract and real inventory."""
from __future__ import annotations

import json

from canonical_media_guard import validate_media_contract
from canonical_release import build_canonical_release


def validate() -> dict[str, list[str]]:
    # build_canonical_release is already fail-closed. Keeping this wrapper makes
    # the validator convenient for CI/manual use and returns the complete report.
    release = build_canonical_release()
    return validate_media_contract(release)


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if any(result.values()) else 0)
