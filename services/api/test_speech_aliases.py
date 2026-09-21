from speech_aliases import alias_evidence


def test_seeded_short_vowel_alias_prevents_asr_only_false_negative():
    evidence = alias_evidence("L1-REIN-05-R01", "ماء")
    assert evidence == {
        "matched": True,
        "effect": "do_not_fail_from_asr_only",
        "matched_alias": "ماء",
    }


def test_latin_provider_spelling_can_be_recognized_as_alias_evidence():
    evidence = alias_evidence("L1-REIN-05-R01", "MA")
    assert evidence["matched"] is True
    assert evidence["matched_alias"] == "ma"


def test_unknown_or_different_output_does_not_match():
    assert alias_evidence("L1-REIN-05-R01", "مي")["matched"] is False
    assert alias_evidence("UNKNOWN-R01", "ما")["matched"] is False
