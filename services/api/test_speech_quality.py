import pytest

from speech_quality import RecordingQualityError, validate_provider_output, validate_recording_input


def test_recording_quality_accepts_supported_audio():
    result = validate_recording_input(
        audio_bytes=b"x" * 64,
        mime_type="audio/webm;codecs=opus",
        duration_seconds=1.2,
        max_bytes=1024,
    )
    assert result["status"] == "input_accepted"
    assert result["academic_effect"] == "none"


def test_recording_quality_rejects_too_short_audio():
    with pytest.raises(RecordingQualityError) as exc:
        validate_recording_input(audio_bytes=b"tiny", mime_type="audio/webm")
    assert exc.value.code == "audio_too_short"
    assert exc.value.rerecord_required is True


def test_recording_quality_rejects_unsupported_type():
    with pytest.raises(RecordingQualityError) as exc:
        validate_recording_input(audio_bytes=b"x" * 64, mime_type="text/plain")
    assert exc.value.code == "unsupported_audio_type"


def test_provider_output_rejects_no_speech():
    with pytest.raises(RecordingQualityError) as exc:
        validate_provider_output(transcript="   ", duration_seconds=1.0)
    assert exc.value.code == "no_speech_detected"


def test_provider_output_rejects_too_short_duration():
    with pytest.raises(RecordingQualityError) as exc:
        validate_provider_output(transcript="ب", duration_seconds=0.1)
    assert exc.value.code == "audio_too_short"


def test_provider_output_accepts_usable_transcript_without_academic_score():
    result = validate_provider_output(transcript="كَتَبَ", duration_seconds=0.8)
    assert result == {
        "status": "provider_output_accepted",
        "duration_seconds": 0.8,
        "academic_effect": "none",
    }
