from __future__ import annotations

import base64
import json

import pytest

import azure_pronunciation_provider as module
from azure_pronunciation_provider import AzurePronunciationAssessmentProvider
from speech_provider import ProviderPermanentError, ProviderTemporaryError


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text="", headers=None):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.headers = headers or {}

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeClient:
    def __init__(self, response, capture, timeout=None):
        self.response = response
        self.capture = capture
        self.capture["timeout"] = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, *, headers, content):
        self.capture.update({"url": url, "headers": headers, "content": content})
        return self.response


def configure(monkeypatch, *, locale="ar-SA"):
    monkeypatch.setenv("HIMMA_AZURE_SPEECH_API_KEY", "test-key")
    monkeypatch.setenv("HIMMA_AZURE_SPEECH_REGION", "eastus")
    monkeypatch.setenv("HIMMA_AZURE_PRONUNCIATION_LOCALE", locale)
    monkeypatch.delenv("HIMMA_AZURE_PRONUNCIATION_ENDPOINT", raising=False)


def test_requires_key_and_region(monkeypatch):
    monkeypatch.delenv("HIMMA_AZURE_SPEECH_API_KEY", raising=False)
    monkeypatch.delenv("HIMMA_AZURE_SPEECH_REGION", raising=False)
    monkeypatch.delenv("HIMMA_AZURE_PRONUNCIATION_ENDPOINT", raising=False)
    with pytest.raises(ProviderPermanentError):
        AzurePronunciationAssessmentProvider()

    monkeypatch.setenv("HIMMA_AZURE_SPEECH_API_KEY", "test-key")
    with pytest.raises(ProviderPermanentError):
        AzurePronunciationAssessmentProvider()


def test_fails_closed_for_unsupported_arabic_pronunciation_locale(monkeypatch):
    configure(monkeypatch, locale="ar-OM")
    with pytest.raises(ProviderPermanentError, match="ar-EG"):
        AzurePronunciationAssessmentProvider()


@pytest.mark.parametrize("locale", ["ar-SA", "ar-EG"])
def test_accepts_only_documented_arabic_pronunciation_locales(monkeypatch, locale):
    configure(monkeypatch, locale=locale)
    provider = AzurePronunciationAssessmentProvider()
    assert provider.locale == locale


def test_rejects_webm_instead_of_silently_transcoding(monkeypatch):
    configure(monkeypatch)
    provider = AzurePronunciationAssessmentProvider()
    with pytest.raises(ProviderPermanentError, match="WAV or OGG"):
        provider.assess(audio_bytes=b"webm", mime_type="audio/webm", reference_text="كَتَبَ")


def test_builds_scripted_phoneme_request_without_pii(monkeypatch):
    configure(monkeypatch)
    capture = {}
    response = FakeResponse(
        payload={
            "RecognitionStatus": "Success",
            "DisplayText": "كتب",
            "SNR": 31.5,
            "NBest": [
                {
                    "Confidence": 0.91,
                    "Display": "كتب",
                    "AccuracyScore": 87.0,
                    "FluencyScore": 92.0,
                    "CompletenessScore": 100.0,
                    "PronScore": 90.0,
                    "Words": [
                        {
                            "Word": "كتب",
                            "Offset": 1_000_000,
                            "Duration": 5_000_000,
                            "AccuracyScore": 87.0,
                            "ErrorType": "None",
                            "Phonemes": [
                                {"AccuracyScore": 90.0},
                                {"AccuracyScore": 82.0},
                                {"AccuracyScore": 89.0},
                            ],
                        }
                    ],
                }
            ],
        },
        headers={"apim-request-id": "request-123"},
    )
    monkeypatch.setattr(
        module.httpx,
        "Client",
        lambda timeout: FakeClient(response, capture, timeout=timeout),
    )

    provider = AzurePronunciationAssessmentProvider()
    result = provider.assess(
        audio_bytes=b"RIFF-test",
        mime_type="audio/wav",
        reference_text="كَتَبَ",
    )

    assert capture["url"].startswith(
        "https://eastus.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
    )
    assert "language=ar-SA" in capture["url"]
    assert "format=detailed" in capture["url"]
    assert capture["headers"]["Content-Type"] == "audio/wav; codecs=audio/pcm; samplerate=16000"
    assert capture["content"] == b"RIFF-test"
    assert "student" not in json.dumps(capture, ensure_ascii=False).lower()

    config = json.loads(
        base64.b64decode(capture["headers"]["Pronunciation-Assessment"]).decode("utf-8")
    )
    assert config == {
        "ReferenceText": "كَتَبَ",
        "GradingSystem": "HundredMark",
        "Granularity": "Phoneme",
        "Dimension": "Comprehensive",
        "EnableMiscue": True,
    }

    assert result.locale == "ar-SA"
    assert result.transcript == "كتب"
    assert result.accuracy_score == 87.0
    assert result.pronunciation_score == 90.0
    assert result.request_id == "request-123"
    assert result.words[0].offset_seconds == pytest.approx(0.1)
    assert result.words[0].duration_seconds == pytest.approx(0.5)
    assert result.words[0].phoneme_scores == (90.0, 82.0, 89.0)
    assert result.raw_metadata["academic_effect"] == "none"
    assert result.raw_metadata["calibration_status"] == "not_calibrated"


def test_silence_and_nomatch_are_non_retryable_recording_quality_results(monkeypatch):
    configure(monkeypatch)
    for status in ["InitialSilenceTimeout", "BabbleTimeout", "NoMatch"]:
        response = FakeResponse(payload={"RecognitionStatus": status, "NBest": []})
        monkeypatch.setattr(
            module.httpx,
            "Client",
            lambda timeout, response=response: FakeClient(response, {}, timeout=timeout),
        )
        with pytest.raises(ProviderPermanentError, match=status):
            AzurePronunciationAssessmentProvider().assess(
                audio_bytes=b"RIFF-test",
                mime_type="audio/wav",
                reference_text="بَ",
            )


def test_retryable_http_statuses(monkeypatch):
    configure(monkeypatch)
    for status_code in [408, 429, 500, 503]:
        response = FakeResponse(status_code=status_code)
        monkeypatch.setattr(
            module.httpx,
            "Client",
            lambda timeout, response=response: FakeClient(response, {}, timeout=timeout),
        )
        with pytest.raises(ProviderTemporaryError):
            AzurePronunciationAssessmentProvider().assess(
                audio_bytes=b"RIFF-test",
                mime_type="audio/wav",
                reference_text="بَ",
            )


def test_auth_and_invalid_audio_http_errors_fail_permanently(monkeypatch):
    configure(monkeypatch)
    for status_code in [400, 401, 403]:
        response = FakeResponse(status_code=status_code, text="bad request")
        monkeypatch.setattr(
            module.httpx,
            "Client",
            lambda timeout, response=response: FakeClient(response, {}, timeout=timeout),
        )
        with pytest.raises(ProviderPermanentError):
            AzurePronunciationAssessmentProvider().assess(
                audio_bytes=b"RIFF-test",
                mime_type="audio/wav",
                reference_text="بَ",
            )
