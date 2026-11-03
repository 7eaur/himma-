"""Executable owner-policy contract for the replacement V2 speech engine."""
from decimal import Decimal
import pytest

from v2_reading_engine import (
    assessment_total, evaluate_reading, grade_words,
    load_alias_catalog, match_letter_transcript, training_hint,
)


def test_owner_catalog_is_local_and_complete():
    catalog = load_alias_catalog()
    assert catalog["runtimeDependency"] == "local_himma_repository_only"
    assert len(catalog["cases"]) == 10
    assert sum(len(entry["variants"]) for entry in catalog["cases"].values()) == 31
    assert catalog["rules"]["onValidApprovedAliasMatch"] == "correct_100_percent"


def test_every_approved_alias_including_chinese_returns_original():
    catalog = load_alias_catalog()
    for question_id, entry in catalog["cases"].items():
        ref = entry["reference"]
        for candidate in [ref, *(item["text"] for item in entry["variants"])]:
            result = evaluate_reading(
                kind="letter", mode="training", question_id=question_id,
                reference=ref, transcript=f" {candidate}。 ",
                audio_valid=True, provider_usable=True,
            )
            assert result.status == "correct", (question_id, candidate)
            assert result.fraction == Decimal("1")
            assert result.reference == ref
            assert result.alias is not None and result.alias.vowel_verified is False
            safe = result.student_payload(mode="training")
            assert safe["reference"] == ref
            assert safe["status"] == "correct"
            assert "alias" not in safe and "asr" not in safe
            assert "azure" not in str(safe).lower()
            assert safe == {
                "status": "correct",
                "message": "أحسنت! قراءتك صحيحة، هيا نكمل.",
                "reference": ref,
            }


@pytest.mark.parametrize("question_id,reference,bad", [
    ("V2-PRE-Q06", "لَ", "ل"),
    ("L1-04-GP-04", "قِ", "ق"),
    ("L1-04-IC-A01", "بُ", "ب"),
    ("L1-04-IC-A03", "مَ", "م"),
    ("SUP-03-GP-01", "سُ", "س"),
    ("SUP-03-SC-01", "دُ", "د"),
    ("SUP-03-GP-03", "لِ", "ل"),
    ("SUP-03-SC-03", "فِ", "ف"),
    ("V2-POST-Q06", "قُ", "ق"),
    ("V2-PRE-Q06", "لَ", "لِ"),
    ("SUP-03-GP-03", "لِ", "لا"),
    ("L1-04-GP-04", "قِ", "قو"),
    ("V2-POST-Q06", "قُ", "قي"),
    ("V2-POST-Q06", "قُ", "对"),
    ("SUP-03-GP-03", "لِ", "不"),
    ("L1-04-GP-02", "رَ", "好"),
])
def test_no_cross_question_or_unapproved_candidate(question_id, reference, bad):
    match = match_letter_transcript(
        question_id=question_id, reference=reference, transcript=bad)
    assert not match.matched


def test_only_intentionally_preserved_bare_ra():
    yes = match_letter_transcript(
        question_id="L1-04-GP-02", reference="رَ", transcript="ر.")
    assert yes.matched is True
    no = match_letter_transcript(
        question_id="L1-04-GP-02", reference="رِ", transcript="ر")
    assert no.matched is False


@pytest.mark.parametrize("reference,transcript,expected", [
    ("دخل نادر المكتبة", "دخل نادر المكتبة", Decimal("1.00000")),
    ("دخل نادر المكتبة", "دخل نادر", Decimal("0.66667")),
    ("دخل نادر المكتبة", "دخل نادر المكتبة اليوم", Decimal("0.66667")),
    ("دخل نادر المكتبة", "دخل نادر اليوم", Decimal("0.66667")),
    ("دخل نادر المكتبة", "دخل نادر المكتبة اليوم جدًا", Decimal("0.33333")),
    ("دخل نادر المكتبة", "اليوم وغدا", Decimal("0.00000")),
    ("دَخَلَ نَادِرٌ الْمَكْتَبَةَ.", "دخل نادر المكتبة.", Decimal("1.00000")),
])
def test_fractional_scoring(reference, transcript, expected):
    score = grade_words(reference, transcript)
    assert score.fraction == expected
    assert score.target_words == 3


def test_threshold_is_strictly_greater_than_85():
    seven = grade_words(" ".join("كلمة" for _ in range(7)),
                        " ".join("كلمة" for _ in range(6)))
    twenty = grade_words(" ".join("كلمة" for _ in range(20)),
                         " ".join("كلمة" for _ in range(17)))
    assert seven.fraction == Decimal("0.85714")
    assert seven.passed_assessment
    assert twenty.fraction == Decimal("0.85000")
    assert twenty.passed_assessment is False


def test_training_is_stricter_than_exam_and_gives_specific_hint():
    ref = " ".join("كلمة" for _ in range(7))
    spoken = " ".join("كلمة" for _ in range(6))
    common = dict(kind="sentence", reference=ref, transcript=spoken,
                  question_id="TEST", audio_valid=True, provider_usable=True,
                  alignment_reliable=True)
    training = evaluate_reading(**common, mode="training")
    exam = evaluate_reading(**common, mode="assessment")
    assert training.status == "incorrect"
    assert training.fraction == Decimal("0.85714")
    assert "نسيت" in training.student_payload(mode="training")["hint"]
    assert exam.status == "correct"
    assert exam.fraction == Decimal("0.85714")
    assert "hint" not in exam.student_payload(mode="assessment")
    assert "صحيحة" not in exam.student_payload(mode="assessment")["message"]


@pytest.mark.parametrize("reference,transcript,word", [
    ("دخل نادر المكتبة", "دخل المكتبة", "نادر"),
    ("دخل نادر المكتبة", "دخل نادر المكتبة اليوم", "اليوم"),
    ("دخل نادر المكتبة", "دخل زيد المكتبة", "نادر"),
])
def test_training_hints_are_grounded_in_alignment(reference, transcript, word):
    score = grade_words(reference, transcript)
    assert word in training_hint(score)


@pytest.mark.parametrize("kind,reference,transcript", [
    ("letter", "لَ", "لا"), ("word", "مَدْرَسَة", "مدرسة"),
    ("sentence", "دخل نادر المكتبة", "دخل نادر المكتبة"),
])
def test_provider_failure_never_becomes_wrong_or_score(kind, reference, transcript):
    for audio_ok, recognized in [(False, True), (True, False)]:
        result = evaluate_reading(
            kind=kind, mode="assessment", question_id="V2-PRE-Q06",
            reference=reference, transcript=transcript,
            audio_valid=audio_ok, provider_usable=recognized,
            alignment_reliable=True,
        )
        assert result.status == "retry_audio"
        assert result.fraction is None
        assert result.passed_for_progress is None


@pytest.mark.parametrize("heard", ["بَ", "لِ", "嗯", "No"])
def test_recognized_wrong_letter_is_incorrect_not_rerecord(heard):
    result = evaluate_reading(
        kind="letter", mode="training", question_id="V2-PRE-Q06",
        reference="لَ", transcript=heard,
        audio_valid=True, provider_usable=True,
    )
    assert result.status == "incorrect"
    assert result.fraction == Decimal("0")
    assert result.passed_for_progress is False
    assert result.hint == "اقرأ الحرف المعروض وحاول مرة ثانية."


@pytest.mark.parametrize("kind,reference,heard", [
    ("word", "قَلَم", "علم"),
    ("word", "كَتَبَ", "لَعِبَ"),
    ("sentence", "دخل نادر المكتبة", "دخل نادر"),
    ("text", "دخل نادر المكتبة", "دخل زيد المكتبة"),
])
def test_recognized_mismatch_is_graded_without_alignment_gate(kind, reference, heard):
    result = evaluate_reading(
        kind=kind, mode="training", question_id="TEST",
        reference=reference, transcript=heard,
        audio_valid=True, provider_usable=True,
        alignment_reliable=False,
    )
    assert result.status == "incorrect" and result.fraction is not None
    assert result.hint
    assert result.student_payload(mode="training")["hint"] == result.hint


def test_recognized_partial_sentence_is_scored_in_assessment():
    result = evaluate_reading(
        kind="sentence", mode="assessment", question_id="TEST",
        reference="دخل نادر المكتبة", transcript="دخل نادر",
        audio_valid=True, provider_usable=True,
    )
    assert result.status == "incorrect"
    assert result.fraction == Decimal("0.66667")
    assert result.student_payload(mode="assessment").get("hint") is None


def test_word_and_sentence_scoring_ignores_diacritics_by_owner_decision():
    for kind, expected, heard in [
        ("word", "كَتَبَ", "كتب"),
        ("sentence", "دَخَلَ نَادِرٌ الْمَكْتَبَةَ", "دخل نادر المكتبة"),
    ]:
        result = evaluate_reading(
            kind=kind, mode="assessment", question_id="TEST",
            reference=expected, transcript=heard,
            audio_valid=True, provider_usable=True,
        )
        assert result.status == "correct"
        assert result.fraction == Decimal("1")


def test_no_transcript_or_unusable_recognition_is_only_rerecord_reason():
    for transcript, usable in [(None, False), ("", True), ("  ", True), ("قلم", False)]:
        result = evaluate_reading(
            kind="word", mode="training", question_id="TEST",
            reference="قلم", transcript=transcript,
            audio_valid=True, provider_usable=usable,
        )
        assert result.status == "retry_audio"
        assert result.fraction is None


def test_30_question_score_is_fractional_not_binary_pass():
    points = [Decimal("1")] * 29 + [Decimal("0.85714")]
    assert assessment_total(points) == Decimal("99.5238")
    with pytest.raises(ValueError):
        assessment_total(points[:-1])
    with pytest.raises(ValueError):
        assessment_total([Decimal("1.2")] * 30)


def test_wrong_word_in_exam_does_not_reveal_the_answer():
    result = evaluate_reading(
        kind="word", mode="assessment", question_id="Q",
        reference="نَخْلَة", transcript="شجرة",
        audio_valid=True, provider_usable=True, alignment_reliable=True,
    )
    assert result.status == "incorrect"
    assert result.fraction == Decimal("0")
    assert "hint" not in result.student_payload(mode="assessment")


def test_unsupported_mode_or_kind_is_rejected():
    args = dict(kind="word", mode="training", reference="قلم",
                transcript="قلم", question_id="Q",
                audio_valid=True, provider_usable=True)
    with pytest.raises(ValueError):
        evaluate_reading(**{**args, "kind": "freeform"})
    with pytest.raises(ValueError):
        evaluate_reading(**{**args, "mode": "legacy_review"})
