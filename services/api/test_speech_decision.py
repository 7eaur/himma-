from speech_decision import preview_speech_decision


def test_lexical_exact_match_is_correct():
    decision = preview_speech_decision(
        mode="lexical",
        counts={"correct": 4, "deletion": 0, "insertion": 0, "substitution": 0},
    )
    assert decision.state == "correct"
    assert decision.reason == "exact_lexical_match"


def test_lexical_word_error_is_incorrect():
    decision = preview_speech_decision(
        mode="lexical",
        counts={"correct": 3, "deletion": 1, "insertion": 0, "substitution": 0},
    )
    assert decision.state == "incorrect"
    assert decision.reason == "lexical_mismatch"


def test_targeted_alias_never_grants_correct_by_itself():
    decision = preview_speech_decision(
        mode="targeted_pronunciation",
        counts={"correct": 0, "deletion": 0, "insertion": 0, "substitution": 1},
        alias_matched=True,
    )
    assert decision.state == "retry_required"
    assert decision.reason == "asr_alias_requires_pronunciation_evidence"


def test_fluency_waits_for_timing_policy():
    decision = preview_speech_decision(
        mode="fluency",
        counts={"correct": 10, "deletion": 0, "insertion": 0, "substitution": 0},
    )
    assert decision.state == "retry_required"
    assert decision.reason == "fluency_timing_policy_pending"
