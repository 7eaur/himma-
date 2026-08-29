from pronunciation_evidence import build_acoustic_evidence_plan


def _unit(reference: str):
    return build_acoustic_evidence_plan(reference)["units"][0]


def test_short_vowels_get_explicit_contrast_classes_without_scores():
    cases = {
        "بَ": ("fatha", ["kasra", "damma", "sukun"]),
        "بِ": ("kasra", ["fatha", "damma", "sukun"]),
        "بُ": ("damma", ["fatha", "kasra", "sukun"]),
        "بْ": ("sukun", ["fatha", "kasra", "damma"]),
    }
    for reference, (expected, contrasts) in cases.items():
        unit = _unit(reference)
        assert unit["expected_vowel_class"] == expected
        assert unit["contrast_vowel_classes"] == contrasts
        assert unit["acoustic_score"] is None
        assert unit["acoustic_label"] is None
        assert unit["evidence_status"] == "pending_calibration"


def test_shadda_and_tanween_are_separate_evidence_expectations():
    shadda = _unit("بَّ")
    assert shadda["expects_gemination"] is True
    assert shadda["expected_vowel_class"] == "fatha"

    plan = build_acoustic_evidence_plan("قَلَمٌ")
    assert plan["units"][-1]["expects_tanween"] == "dammatan"


def test_plan_is_collection_only_and_academically_neutral():
    plan = build_acoustic_evidence_plan("كَتَبَ")
    assert plan["status"] == "collection_required"
    assert plan["requires_ground_truth"] is True
    assert plan["direct_haraka_judgement"] is False
    assert plan["calibration_version"] is None
    assert plan["academic_effect"] == "none"
    assert plan["stt_locale"] == "ar-OM"
    assert plan["azure_pronunciation_assessment"]["enabled_for_judgement"] is False
    assert plan["azure_pronunciation_assessment"]["candidate_locales"] == ["ar-SA", "ar-EG"]
    assert "ar-OM" not in plan["azure_pronunciation_assessment"]["candidate_locales"]


def test_plan_never_synthesizes_provider_or_asr_confidence_as_acoustic_score():
    plan = build_acoustic_evidence_plan("بُ")
    assert "provider_confidence" not in plan
    assert "asr_confidence" not in plan
    assert all(unit["acoustic_score"] is None for unit in plan["units"])
