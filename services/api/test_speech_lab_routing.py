import pytest
from fastapi import HTTPException

import speech_lab


def test_target_lookup_returns_classified_approved_target(monkeypatch):
    monkeypatch.setattr(
        speech_lab,
        "_targets",
        lambda _db: [
            {
                "target_id": "L2-CORE-10-R01",
                "canonical_id": "L2-CORE-10",
                "speech_mode": "lexical",
                "reference_text": "يقرأ سالم كتابا",
            }
        ],
    )

    target = speech_lab._target_for_id(object(), "L2-CORE-10-R01")
    assert target["speech_mode"] == "lexical"


def test_unknown_target_is_rejected(monkeypatch):
    monkeypatch.setattr(speech_lab, "_targets", lambda _db: [])

    with pytest.raises(HTTPException) as exc:
        speech_lab._target_for_id(object(), "UNKNOWN-R01")

    assert exc.value.status_code == 404


def test_new_unclassified_reading_content_fails_closed(monkeypatch):
    monkeypatch.setattr(
        speech_lab,
        "_targets",
        lambda _db: [
            {
                "target_id": "NEW-READ-R01",
                "canonical_id": "NEW-READ",
                "speech_mode": "unclassified",
                "reference_text": "نص جديد",
            }
        ],
    )

    with pytest.raises(HTTPException) as exc:
        speech_lab._target_for_id(object(), "NEW-READ-R01")

    assert exc.value.status_code == 409
    assert "Speech Profile" in str(exc.value.detail)
