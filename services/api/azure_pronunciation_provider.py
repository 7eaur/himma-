"""Experimental Azure Pronunciation Assessment adapter for Himma Speech Lab.

This adapter is intentionally isolated from Himma's academic scoring path.
Lexical ASR continues to use the configured Azure fast-transcription locale
(currently ar-OM). Pronunciation Assessment uses a separately configured locale
because Azure currently supports Arabic pronunciation assessment only for
ar-SA and ar-EG.

The REST short-audio endpoint accepts PCM WAV (16 kHz) or OGG/Opus. Browser
WebM recordings must therefore be converted/recorded as a supported format
before calling this adapter. No student identity is sent to Azure.
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from typing import Any

import httpx

from speech_provider import ProviderPermanentError, ProviderTemporaryError

_SUPPORTED_LOCALES = {"ar-SA", "ar-EG"}
_SUPPORTED_MIME_TYPES = {
    "audio/wav": "audio/wav; codecs=audio/pcm; samplerate=16000",
    "audio/wave": "audio/wav; codecs=audio/pcm; samplerate=16000",
    "audio/x-wav": "audio/wav; codecs=audio/pcm; samplerate=16000",
    "audio/ogg": "audio/ogg; codecs=opus",
    "audio/ogg;codecs=opus": "audio/ogg; codecs=opus",
    "audio/ogg; codecs=opus": "audio/ogg; codecs=opus",
}


@dataclass(frozen=True)
class PronunciationWordScore:
    word: str
    accuracy_score: float | None
    error_type: str | None
    offset_seconds: float | None
    duration_seconds: float | None
    phoneme_scores: tuple[float, ...]


@dataclass(frozen=True)
class PronunciationAssessmentResult:
    provider_name: str
    locale: str
    transcript: str
    recognition_status: str
    confidence: float | None
    accuracy_score: float | None
    fluency_score: float | None
    completeness_score: float | None
    pronunciation_score: float | None
    words: tuple[PronunciationWordScore, ...]
    request_id: str | None
    raw_metadata: dict[str, Any]


class AzurePronunciationAssessmentProvider:
    """Azure scripted pronunciation assessment for supervisor calibration only."""

    name = "azure-pronunciation-assessment"

    def __init__(self) -> None:
        self.api_key = os.getenv("HIMMA_AZURE_SPEECH_API_KEY", "").strip()
        self.region = os.getenv("HIMMA_AZURE_SPEECH_REGION", "").strip().lower()
        self.locale = os.getenv("HIMMA_AZURE_PRONUNCIATION_LOCALE", "ar-SA").strip()
        self.endpoint = os.getenv("HIMMA_AZURE_PRONUNCIATION_ENDPOINT", "").strip().rstrip("/")
        self.timeout_seconds = float(os.getenv("HIMMA_AZURE_PRONUNCIATION_TIMEOUT_SECONDS", "30") or 30)

        if not self.api_key:
            raise ProviderPermanentError("HIMMA_AZURE_SPEECH_API_KEY is required for pronunciation assessment")
        if not self.endpoint and not self.region:
            raise ProviderPermanentError(
                "HIMMA_AZURE_SPEECH_REGION or HIMMA_AZURE_PRONUNCIATION_ENDPOINT is required"
            )
        if self.locale not in _SUPPORTED_LOCALES:
            raise ProviderPermanentError(
                f"Azure Arabic pronunciation assessment locale must be one of {sorted(_SUPPORTED_LOCALES)}"
            )
        if self.timeout_seconds <= 0:
            raise ProviderPermanentError("HIMMA_AZURE_PRONUNCIATION_TIMEOUT_SECONDS must be positive")

    @property
    def request_url(self) -> str:
        if self.endpoint:
            base = self.endpoint
            if "/speech/recognition/" in base:
                return f"{base}?language={self.locale}&format=detailed"
            return (
                f"{base}/speech/recognition/conversation/cognitiveservices/v1"
                f"?language={self.locale}&format=detailed"
            )
        return (
            f"https://{self.region}.stt.speech.microsoft.com"
            f"/speech/recognition/conversation/cognitiveservices/v1"
            f"?language={self.locale}&format=detailed"
        )

    @staticmethod
    def _content_type(mime_type: str) -> str:
        normalized = (mime_type or "").strip().lower()
        if normalized in _SUPPORTED_MIME_TYPES:
            return _SUPPORTED_MIME_TYPES[normalized]
        if normalized.startswith("audio/ogg") and "opus" in normalized:
            return "audio/ogg; codecs=opus"
        raise ProviderPermanentError(
            "Pronunciation assessment accepts only 16 kHz PCM WAV or OGG/Opus audio"
        )

    @staticmethod
    def _assessment_header(reference_text: str) -> str:
        config = {
            "ReferenceText": reference_text,
            "GradingSystem": "HundredMark",
            "Granularity": "Phoneme",
            "Dimension": "Comprehensive",
            "EnableMiscue": True,
        }
        payload = json.dumps(config, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return base64.b64encode(payload).decode("ascii")

    def assess(
        self,
        *,
        audio_bytes: bytes,
        mime_type: str,
        reference_text: str,
    ) -> PronunciationAssessmentResult:
        reference = reference_text.strip()
        if not reference:
            raise ProviderPermanentError("reference text is required")
        if not audio_bytes:
            raise ProviderPermanentError("audio payload is empty")

        content_type = self._content_type(mime_type)
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": content_type,
            "Accept": "application/json",
            "Pronunciation-Assessment": self._assessment_header(reference),
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(self.request_url, headers=headers, content=audio_bytes)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise ProviderTemporaryError(str(exc)) from exc
        except httpx.HTTPError as exc:
            raise ProviderTemporaryError(str(exc)) from exc

        if response.status_code in {408, 425, 429} or response.status_code >= 500:
            raise ProviderTemporaryError(
                f"Azure pronunciation assessment temporary failure ({response.status_code})"
            )
        if response.status_code >= 400:
            detail = response.text[:500].strip()
            raise ProviderPermanentError(
                f"Azure pronunciation assessment rejected the request ({response.status_code}): {detail}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderPermanentError("Azure pronunciation assessment returned invalid JSON") from exc

        recognition_status = str(payload.get("RecognitionStatus") or "")
        if recognition_status != "Success":
            if recognition_status in {"InitialSilenceTimeout", "BabbleTimeout", "NoMatch"}:
                raise ProviderPermanentError(f"Azure pronunciation assessment: {recognition_status}")
            raise ProviderTemporaryError(
                f"Azure pronunciation assessment did not succeed: {recognition_status or 'unknown'}"
            )

        nbest = payload.get("NBest") or []
        best = nbest[0] if nbest and isinstance(nbest[0], dict) else {}
        words: list[PronunciationWordScore] = []
        for word in best.get("Words") or []:
            if not isinstance(word, dict):
                continue
            offset = word.get("Offset")
            duration = word.get("Duration")
            phoneme_scores: list[float] = []
            for phoneme in word.get("Phonemes") or []:
                if not isinstance(phoneme, dict):
                    continue
                score = phoneme.get("AccuracyScore")
                if isinstance(score, (int, float)):
                    phoneme_scores.append(float(score))
            words.append(
                PronunciationWordScore(
                    word=str(word.get("Word") or ""),
                    accuracy_score=_float_or_none(word.get("AccuracyScore")),
                    error_type=str(word.get("ErrorType")) if word.get("ErrorType") is not None else None,
                    offset_seconds=(float(offset) / 10_000_000.0) if isinstance(offset, (int, float)) else None,
                    duration_seconds=(float(duration) / 10_000_000.0) if isinstance(duration, (int, float)) else None,
                    phoneme_scores=tuple(phoneme_scores),
                )
            )

        return PronunciationAssessmentResult(
            provider_name=self.name,
            locale=self.locale,
            transcript=str(best.get("Display") or payload.get("DisplayText") or ""),
            recognition_status=recognition_status,
            confidence=_float_or_none(best.get("Confidence")),
            accuracy_score=_float_or_none(best.get("AccuracyScore")),
            fluency_score=_float_or_none(best.get("FluencyScore")),
            completeness_score=_float_or_none(best.get("CompletenessScore")),
            pronunciation_score=_float_or_none(best.get("PronScore")),
            words=tuple(words),
            request_id=(
                response.headers.get("apim-request-id")
                or response.headers.get("x-ms-request-id")
                or response.headers.get("x-requestid")
            ),
            raw_metadata={
                "locale": self.locale,
                "granularity": "Phoneme",
                "dimension": "Comprehensive",
                "miscue_enabled": True,
                "content_type": content_type,
                "snr": payload.get("SNR"),
                "phoneme_names_expected": False,
                "academic_effect": "none",
                "calibration_status": "not_calibrated",
            },
        )


def _float_or_none(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None
