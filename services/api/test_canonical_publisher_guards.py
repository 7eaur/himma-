"""Publisher boundary guards for the single approved canonical release."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy

import pytest

from canonical_content_publisher import publish_release
from canonical_release import build_canonical_release


def _rehash(release: dict) -> dict:
    value = deepcopy(release)
    value.pop("sha256", None)
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    value["sha256"] = hashlib.sha256(raw).hexdigest()
    return value


def test_publisher_rejects_a_rehashed_question_copy_variant_before_db_writes():
    release = deepcopy(build_canonical_release())
    pre_q01 = next(item for item in release["items"] if item["canonical_id"] == "PRE-Q01")
    pre_q01["rounds"][0]["question_text"] = "نص غير معتمد لا يجوز نشره"
    tampered = _rehash(release)

    with pytest.raises(RuntimeError, match="only accepts the exact release"):
        publish_release(tampered)


def test_publisher_rejects_a_rehashed_option_variant_before_db_writes():
    release = deepcopy(build_canonical_release())
    pre_q05 = next(item for item in release["items"] if item["canonical_id"] == "PRE-Q05")
    pre_q05["rounds"][0]["options"][0]["text"] = "خيار غير معتمد"
    tampered = _rehash(release)

    # The option mutation can also invalidate semantic media mapping. Either way,
    # publication must fail before a SessionLocal transaction is opened.
    with pytest.raises(RuntimeError):
        publish_release(tampered)
