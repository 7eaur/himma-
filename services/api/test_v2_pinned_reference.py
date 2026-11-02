"""Pinned reading references are server-owned and mode comes from authoring."""
import pytest

from test_v2_reading_job_store import db, new_v2_assessment
from v2_reading_engine import pinned_reference as pinned
from v2_reading_engine.job_store import ReadingConflict


def question(*, qid="V2-PRE-Q06", role="pretest",
             kind="syllable_reading", reference="لَ", displayed="لَ"):
    return {
        "id": qid,
        "interaction": "read_aloud",
        "role": role,
        "evidence_type": kind,
        "reading_reference": reference,
        "stimulus": {"text": displayed, "media": []},
        "private_answer": {"rubric": {"reference_text": reference}},
    }


@pytest.mark.parametrize("evidence,expected", [
    ("syllable_reading", "letter"),
    ("sound_blending", "word"),
    ("simple_word_reading", "word"),
    ("long_word_reading", "word"),
    ("sentence_reading", "sentence"),
    ("connected_sentence_reading", "sentence"),
    ("short_text_reading", "text"),
])
def test_explicit_approved_evidence_type_derives_kind(monkeypatch, db, evidence, expected):
    monkeypatch.setattr(pinned, "_load_pinned_release",
                        lambda *_: {"questions": [question(kind=evidence)]})
    result = pinned.resolve_pinned_reading(db, content_release_id=1,
                                            question_id="V2-PRE-Q06")
    assert result.kind == expected
    assert result.reference == "لَ"


@pytest.mark.parametrize("role,mode", [
    ("pretest", "assessment"),
    ("posttest", "assessment"),
    ("independent_check", "assessment"),
    ("support_check", "assessment"),
    ("guided_practice", "training"),
])
def test_role_controls_feedback_visibility(monkeypatch, db, role, mode):
    monkeypatch.setattr(pinned, "_load_pinned_release",
                        lambda *_: {"questions": [question(role=role)]})
    result = pinned.resolve_pinned_reading(db, content_release_id=1,
                                            question_id="V2-PRE-Q06")
    assert result.mode == mode


def test_enqueue_uses_private_release_not_client_reference(monkeypatch, db):
    student, release, response, audio = new_v2_assessment(db)
    monkeypatch.setattr(pinned, "_load_pinned_release",
                        lambda *_: {"questions": [question()]})
    job = pinned.enqueue_pinned_reading(
        db, student_id=student.id, audio_submission_id=audio.id,
        content_release_id=release.id, question_id=response.question_id,
    )
    assert job.reference_text == "لَ"
    assert job.reading_kind == "letter"
    assert job.learning_mode == "assessment"


def test_unrecognized_question_cannot_infer_reference(monkeypatch, db):
    monkeypatch.setattr(pinned, "_load_pinned_release",
                        lambda *_: {"questions": [question(qid="OTHER")]})
    with pytest.raises(ReadingConflict, match="missing or duplicated"):
        pinned.resolve_pinned_reading(
            db, content_release_id=1, question_id="V2-PRE-Q06")


def test_question_reference_and_rubric_disagreement_is_rejected(monkeypatch, db):
    bad = question()
    bad["private_answer"]["rubric"]["reference_text"] = "لِ"
    monkeypatch.setattr(pinned, "_load_pinned_release",
                        lambda *_: {"questions": [bad]})
    with pytest.raises(ReadingConflict, match="disagree"):
        pinned.resolve_pinned_reading(
            db, content_release_id=1, question_id="V2-PRE-Q06")


def test_unapproved_reading_type_or_role_fails_closed(monkeypatch, db):
    for overrides in ({"evidence_type": "unsupported"},
                      {"role": "human_review"},
                      {"interaction": "choose_one"}):
        bad = question()
        bad.update(overrides)
        monkeypatch.setattr(pinned, "_load_pinned_release",
                            lambda *_, val=bad: {"questions": [val]})
        with pytest.raises(ReadingConflict):
            pinned.resolve_pinned_reading(
                db, content_release_id=1, question_id="V2-PRE-Q06")


def test_missing_private_reference_is_not_reconstructed_from_stimulus(monkeypatch, db):
    bad = question()
    bad.pop("reading_reference")
    bad["private_answer"]["rubric"].pop("reference_text")
    monkeypatch.setattr(pinned, "_load_pinned_release",
                        lambda *_: {"questions": [bad]})
    with pytest.raises(ReadingConflict, match="missing"):
        pinned.resolve_pinned_reading(
            db, content_release_id=1, question_id="V2-PRE-Q06")


def test_release_with_duplicate_question_fails_closed(monkeypatch, db):
    monkeypatch.setattr(pinned, "_load_pinned_release",
                        lambda *_: {"questions": [question(), question()]})
    with pytest.raises(ReadingConflict, match="duplicated"):
        pinned.resolve_pinned_reading(
            db, content_release_id=1, question_id="V2-PRE-Q06")


def test_displayed_unvowelled_text_never_overrides_private_reference(monkeypatch, db):
    question_row = question(
        qid="L2-04-GP-01", role="guided_practice", kind="sentence_reading",
        reference="ذَهَبَ سَامِي إِلَى الْمَدْرَسَةِ.",
        displayed="ذهب سامي إلى المدرسة.",
    )
    monkeypatch.setattr(pinned, "_load_pinned_release",
                        lambda *_: {"questions": [question_row]})
    result = pinned.resolve_pinned_reading(
        db, content_release_id=1, question_id="L2-04-GP-01")
    assert result.reference == question_row["reading_reference"]
    assert result.kind == "sentence"
