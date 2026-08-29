from arabic_pronunciation import build_pronunciation_reference


def _unit(text: str):
    result = build_pronunciation_reference(text)
    assert len(result["units"]) == 1
    return result, result["units"][0]


def test_short_vowels_are_distinct():
    fatha, fatha_unit = _unit("بَ")
    kasra, kasra_unit = _unit("بِ")
    damma, damma_unit = _unit("بُ")

    assert fatha["target_type"] == "letter_with_haraka"
    assert fatha_unit["base"] == "ب"
    assert fatha_unit["vowel"] == "fatha"
    assert fatha_unit["vowel_name"] == "فتحة"
    assert "a" in fatha_unit["phonetic_hint"]

    assert kasra_unit["vowel"] == "kasra"
    assert kasra_unit["vowel_name"] == "كسرة"
    assert "i" in kasra_unit["phonetic_hint"]

    assert damma_unit["vowel"] == "damma"
    assert damma_unit["vowel_name"] == "ضمة"
    assert "u" in damma_unit["phonetic_hint"]

    assert {fatha_unit["vowel"], kasra_unit["vowel"], damma_unit["vowel"]} == {
        "fatha",
        "kasra",
        "damma",
    }


def test_sukun_is_an_explicit_letter_target():
    result, unit = _unit("بْ")
    assert result["target_type"] == "letter_with_haraka"
    assert unit["base"] == "ب"
    assert unit["sukun"] is True
    assert unit["vowel"] is None
    assert "∅" in unit["phonetic_hint"]


def test_shadda_and_fatha_survive_unicode_normalization():
    result, unit = _unit("بَّ")
    assert result["has_diacritics"] is True
    assert unit["geminated"] is True
    assert unit["vowel"] == "fatha"


def test_tanween_is_preserved_for_words():
    result = build_pronunciation_reference("قَلَمٌ")
    assert result["target_type"] == "word"
    final = result["units"][-1]
    assert final["base"] == "م"
    assert final["tanween"] == "dammatan"
    assert final["tanween_name"] == "تنوين ضم"
    assert "un" in final["phonetic_hint"]


def test_same_lexical_skeleton_can_have_different_vowel_reference():
    active = build_pronunciation_reference("كَتَبَ")
    passive = build_pronunciation_reference("كُتِبَ")
    active_vowels = [unit["vowel"] for unit in active["units"]]
    passive_vowels = [unit["vowel"] for unit in passive["units"]]
    assert active_vowels == ["fatha", "fatha", "fatha"]
    assert passive_vowels == ["damma", "kasra", "fatha"]
    assert active_vowels != passive_vowels


def test_target_type_word_sentence_and_passage():
    assert build_pronunciation_reference("كتب")["target_type"] == "word"
    assert build_pronunciation_reference("ذهب سالم")["target_type"] == "sentence"
    assert build_pronunciation_reference("ذهب سالم إلى المدرسة ثم عاد إلى البيت سعيدًا")["target_type"] == "passage"


def test_unmarked_word_does_not_invent_harakat():
    result = build_pronunciation_reference("كتب")
    assert result["has_diacritics"] is False
    assert all(unit["vowel"] is None for unit in result["units"])


def test_punctuation_does_not_create_fake_pronunciation_units():
    result = build_pronunciation_reference("كَتَبَ.")
    assert [unit["base"] for unit in result["units"]] == ["ك", "ت", "ب"]


def test_pronunciation_reference_is_explicitly_non_academic_until_calibrated():
    result = build_pronunciation_reference("بَ")
    assert result["acoustic_status"] == "not_calibrated"
    assert result["academic_effect"] == "none"
