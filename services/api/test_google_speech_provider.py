import pytest

from google_speech_provider import GoogleSpeechV2Provider
from speech_provider import ProviderNotConfigured, ProviderPermanentError, build_provider


def test_google_provider_requires_project_id(monkeypatch):
    monkeypatch.setenv("HIMMA_ASR_PROVIDER", "google-stt-v2")
    monkeypatch.delenv("HIMMA_GOOGLE_CLOUD_PROJECT", raising=False)

    with pytest.raises(ProviderPermanentError, match="HIMMA_GOOGLE_CLOUD_PROJECT"):
        GoogleSpeechV2Provider()

    with pytest.raises(ProviderNotConfigured, match="HIMMA_GOOGLE_CLOUD_PROJECT"):
        build_provider()


def test_google_provider_keeps_reference_boost_disabled_by_default(monkeypatch):
    monkeypatch.setenv("HIMMA_GOOGLE_CLOUD_PROJECT", "himma-test-project")
    monkeypatch.delenv("HIMMA_GOOGLE_STT_REFERENCE_BOOST", raising=False)

    provider = GoogleSpeechV2Provider()
    assert provider.location == "global"
    assert provider.model == "short"
    assert provider.reference_boost == 0
    assert provider.timeout_seconds == 30


def test_google_provider_rejects_out_of_range_reference_boost(monkeypatch):
    monkeypatch.setenv("HIMMA_GOOGLE_CLOUD_PROJECT", "himma-test-project")
    monkeypatch.setenv("HIMMA_GOOGLE_STT_REFERENCE_BOOST", "20.1")

    with pytest.raises(ProviderPermanentError, match="between 0 and 20"):
        GoogleSpeechV2Provider()


def test_google_provider_builds_reference_hint_only_when_explicitly_enabled(monkeypatch):
    from google.cloud import speech_v2
    from google.cloud.speech_v2.types import cloud_speech

    captured = {}

    class FakeSpeechClient:
        def recognize(self, *, request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return cloud_speech.RecognizeResponse(
                results=[
                    cloud_speech.SpeechRecognitionResult(
                        alternatives=[
                            cloud_speech.SpeechRecognitionAlternative(
                                transcript="ذهب سالم إلى المدرسة",
                                confidence=0.93,
                            )
                        ]
                    )
                ]
            )

    monkeypatch.setattr(speech_v2, "SpeechClient", FakeSpeechClient)
    monkeypatch.setenv("HIMMA_GOOGLE_CLOUD_PROJECT", "himma-test-project")
    monkeypatch.setenv("HIMMA_GOOGLE_STT_REFERENCE_BOOST", "5")
    monkeypatch.setenv("HIMMA_GOOGLE_STT_TIMEOUT_SECONDS", "12")

    provider = GoogleSpeechV2Provider()
    result = provider.transcribe_reference_guided(
        audio_bytes=b"test-audio",
        mime_type="audio/webm",
        reference_text="ذَهَبَ سَالِمٌ إِلَى الْمَدْرَسَةِ",
        language="ar-OM",
    )

    assert result.provider_name == "google-stt-v2"
    assert result.transcript == "ذهب سالم إلى المدرسة"
    assert result.confidence == pytest.approx(0.93)
    assert result.raw_metadata["reference_hint_used"] is True
    assert result.raw_metadata["reference_boost"] == 5
    assert result.raw_metadata["language"] == "ar-OM"
    assert captured["timeout"] == 12
    assert captured["request"].recognizer == "projects/himma-test-project/locations/global/recognizers/_"
    assert captured["request"].config.language_codes == ["ar-OM"]
    assert captured["request"].config.model == "short"


def test_google_provider_sends_no_reference_hint_at_zero_boost(monkeypatch):
    from google.cloud import speech_v2
    from google.cloud.speech_v2.types import cloud_speech

    class FakeSpeechClient:
        def recognize(self, *, request, timeout):
            return cloud_speech.RecognizeResponse()

    monkeypatch.setattr(speech_v2, "SpeechClient", FakeSpeechClient)
    monkeypatch.setenv("HIMMA_GOOGLE_CLOUD_PROJECT", "himma-test-project")
    monkeypatch.setenv("HIMMA_GOOGLE_STT_REFERENCE_BOOST", "0")

    provider = GoogleSpeechV2Provider()
    result = provider.transcribe_reference_guided(
        audio_bytes=b"test-audio",
        mime_type="audio/webm",
        reference_text="قَلَم",
        language="ar-OM",
    )

    assert result.raw_metadata["reference_hint_used"] is False
    assert result.raw_metadata["reference_boost"] == 0
