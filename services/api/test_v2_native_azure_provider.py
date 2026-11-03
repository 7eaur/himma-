"""Azure adapter contract: 100% offline, no live key or network requests."""
from __future__ import annotations

import asyncio
import base64
from io import BytesIO
import json
import wave

import httpx
import pytest

from v2_reading_engine.azure_provider import (
    AzureSpeechConfig, AzureSpeechProvider,
)


def wav16k() -> bytes:
    output = BytesIO()
    with wave.open(output, "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(16000)
        file.writeframes(b"\x00\x00" * 16000)
    return output.getvalue()


def provider(handler, *, hint=False):
    config = AzureSpeechConfig(
        endpoint="https://eastus.api.cognitive.microsoft.com",
        api_key="local-contract-placeholder",
        fast_reference_hint=hint,
    )
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return AzureSpeechProvider(config, client), client


def test_configuration_never_discloses_key_and_rejects_wrong_domain():
    config = AzureSpeechConfig(
        endpoint="https://eastus.api.cognitive.microsoft.com",
        api_key="private-test-placeholder",
    )
    assert "private-test-placeholder" not in repr(config)
    assert "ar-OM" in config.short_url("ar-OM")
    assert "ar-SA" in config.short_url("ar-SA")
    with pytest.raises(ValueError):
        AzureSpeechConfig(endpoint="https://attacker.example.com", api_key="x")


def test_configuration_missing_secret_fails_closed(monkeypatch):
    monkeypatch.delenv("HIMMA_AZURE_SPEECH_ENDPOINT", raising=False)
    monkeypatch.delenv("HIMMA_AZURE_SPEECH_API_KEY", raising=False)
    with pytest.raises(ValueError):
        AzureSpeechConfig.from_environment()


def test_short_audio_receives_pcm16_and_returns_usable_arabic():
    seen = []
    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={
            "RecognitionStatus": "Success",
            "NBest": [{"Display": "لا.", "Confidence": 0.91}],
        })

    engine, client = provider(handler)
    async def run():
        async with client:
            return await engine.transcribe(wav16k(), mime="audio/wav",
                                           reference="لَ", letter_mode=True)
    evidence = asyncio.run(run())
    assert evidence.provider_usable
    assert evidence.source == "short-audio"
    assert evidence.transcript == "لا."
    assert len(seen) == 1
    assert "language=ar-OM" in str(seen[0].url)
    assert seen[0].headers["ocp-apim-subscription-key"] == "local-contract-placeholder"


def test_webm_uses_fast_transcription_with_optional_reference_hint():
    seen = []
    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={
            "combinedPhrases": [{"text": "دخل نادر المكتبة"}],
            "phrases": [{"text": "دخل نادر المكتبة", "confidence": 0.85}],
        })

    engine, client = provider(handler, hint=True)
    async def run():
        async with client:
            return await engine.transcribe(
                b"test-webm-audio" * 120, mime="audio/webm",
                reference="دخل نادر المكتبة", letter_mode=False,
            )
    data = asyncio.run(run())
    assert data.source == "fast-transcription"
    assert data.provider_usable
    assert data.confidence == 0.85
    assert len(seen) == 1
    assert "transcriptions:transcribe" in str(seen[0].url)
    body = seen[0].read().decode("utf-8", errors="replace")
    assert '"locales": ["ar-OM"]' in body
    assert json.dumps("دخل نادر المكتبة", ensure_ascii=True)[1:-1] in body


def test_short_no_match_falls_back_to_fast_for_letter_chinese():
    urls = []
    def handler(request):
        urls.append(str(request.url))
        if "conversation/cognitiveservices" in str(request.url):
            return httpx.Response(200, json={"RecognitionStatus": "NoMatch"})
        return httpx.Response(200, json={
            "combinedPhrases": [{"text": "例"}],
        })

    engine, client = provider(handler)
    async def run():
        async with client:
            return await engine.transcribe(wav16k(), mime="audio/wav",
                                           reference="لِ", letter_mode=True)
    result = asyncio.run(run())
    assert result.provider_usable and result.transcript == "例"
    assert result.source == "fast-transcription"
    assert len(urls) == 2


def test_nonarabic_recognized_transcript_reaches_policy_instead_of_forcing_rerecord():
    def handler(request):
        return httpx.Response(200, json={
            "combinedPhrases": [{"text": "Looks good."}],
        })
    engine, client = provider(handler)
    async def run():
        async with client:
            return await engine.transcribe(
                b"audio" * 250, mime="audio/webm",
                reference="دخل نادر", letter_mode=False)
    result = asyncio.run(run())
    assert result.provider_usable is True
    assert result.transcript == "Looks good."


def test_failed_provider_yields_no_automatic_grade_and_no_secret_in_error():
    def handler(request):
        return httpx.Response(401, text="Unauthorized")
    engine, client = provider(handler)
    async def run():
        async with client:
            return await engine.transcribe(
                b"audio" * 250, mime="audio/webm", reference="مَ", letter_mode=True)
    result = asyncio.run(run())
    assert result.provider_usable is False and result.transcript is None
    assert result.error_code == "fast_http_401"
    assert "local-contract-placeholder" not in repr(result)


def test_invalid_audio_does_not_call_provider():
    calls = []
    def handler(request):
        calls.append(request)
        raise AssertionError("No provider request is allowed for invalid audio")
    engine, client = provider(handler)
    async def run():
        async with client:
            corrupt = await engine.transcribe(
                b"not-wav" * 400, mime="audio/wav",
                reference="رَ", letter_mode=True)
            too_small = await engine.transcribe(
                b"abc", mime="audio/webm", reference="رَ", letter_mode=True)
            return corrupt, too_small
    corrupt, too_small = asyncio.run(run())
    assert corrupt.error_code == "wav_format_invalid"
    assert too_small.error_code == "audio_invalid"
    assert calls == []


def test_pronunciation_assessment_uses_reference_and_ar_sa():
    seen = []
    def handler(request):
        seen.append(request)
        payload = json.loads(base64.b64decode(
            request.headers["pronunciation-assessment"]).decode("utf-8"))
        assert payload["ReferenceText"] == "رَ"
        assert payload["Granularity"] == "Phoneme"
        return httpx.Response(200, json={
            "RecognitionStatus": "Success",
            "NBest": [{
                "Display": "راء",
                "PronScore": 93.0,
                "AccuracyScore": 92.0,
                "FluencyScore": 90.0,
                "CompletenessScore": 100.0,
            }],
        })
    engine, client = provider(handler)
    async def run():
        async with client:
            return await engine.assess_pronunciation(wav16k(), reference="رَ")
    result = asyncio.run(run())
    assert result.locale == "ar-SA"
    assert result.pronunciation_score == 93
    assert result.error_code is None
    assert len(seen) == 1
    assert "language=ar-SA" in str(seen[0].url)
    assert result.transcript == "راء"


def test_internal_worker_fails_closed_when_feature_disabled_or_secret_missing(monkeypatch):
    from v2_reading_engine.runtime import native_runtime_configuration
    monkeypatch.delenv("HIMMA_V2_NATIVE_READING_ENABLED", raising=False)
    assert native_runtime_configuration() is None
    monkeypatch.setenv("HIMMA_V2_NATIVE_READING_ENABLED", "1")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    with pytest.raises(ValueError, match="PostgreSQL"):
        native_runtime_configuration()
    monkeypatch.setenv("DATABASE_URL", "postgresql://redacted/internal")
    monkeypatch.delenv("HIMMA_AZURE_SPEECH_API_KEY", raising=False)
    with pytest.raises(ValueError, match="configuration is incomplete"):
        native_runtime_configuration()
    monkeypatch.setenv("HIMMA_V2_NATIVE_READING_ENABLED", "true")
    with pytest.raises(ValueError, match="must be 0 or 1"):
        native_runtime_configuration()
