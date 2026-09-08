"""Explicit media reconciliations for the Sep-8 canonical Himma release.

This file is data, not a runtime patch.  It exists because the immutable 105-item
client catalog predates the final approved audio package.  The canonical release
builder applies these reconciliations before hashing/publishing, so PostgreSQL
still receives one final release object and runtime never consults this module.

Only source-supported corrections belong here.  In particular, the approved
Level-2 changeset defines L2-CORE-01 round 2 as the short-vowel target ``مِ``.
The final audio manifest publishes that syllable as ``SYL-05``.  The historical
catalog linked the round to ``LET-01``; that stable letter-sound ID now contains
``مَ`` and is therefore not semantically valid for this vocalized target.
"""
from __future__ import annotations

# (canonical_id, round_number) -> exact final audio media specs.
# Spec shape matches compiled media: asset_id/type/usage/semantic_text.
ROUND_AUDIO_OVERRIDES: dict[tuple[str, int], list[dict[str, str]]] = {
    ("L2-CORE-01", 2): [
        {
            "asset_id": "SYL-05",
            "asset_type": "audio",
            "usage": "prompt",
            "semantic_text": "مِ",
        }
    ],
}
