"""Approved multi-audio listening sequences that are not single prompt sounds.

Student Experience v2 replaced L1-CORE-06 with comparison of the beginnings of
two *heard words*.  The old runtime overlay removed the obsolete one-sound prompt
and stored the two-word sequence structurally.  This pure contract carries that
approved semantic data into the canonical release; no DB overlay is required.
"""
from __future__ import annotations

LISTENING_AUDIO_SEQUENCES: dict[str, tuple[tuple[str, ...], ...]] = {
    "L1-CORE-06": (
        ("موز", "ماء"),
        ("باب", "بطة"),
        ("قلم", "كرة"),
        ("سمك", "شمس"),
        ("نور", "نخلة"),
    ),
}
