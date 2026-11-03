"""Azure Speech adapter for the native V2 reading engine.

Backend-only implementation. No laboratory/Vercel/Supabase runtime imports.
Pure speech evidence; it must never write academic grades or return to a pupil.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from urllib.parse import urlparse
import base64
import json
import os
import wave
import unicodedata

import httpx


_SUPPORTED_MIME = {"audio/wav", "audio/webm", "audio/mp4", "audio/ogg", "audio/mpeg"}
_MAX_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True)
class AzureSpeechConfig:
    endpoint: str
    api_key: str = field(repr=False)
    region: str | None = None
    timeout_seconds: float = 45.0
    fast_reference_hint: bool = False
    lexical_locale: str = "ar-OM"
    pronunciation_locale: str = "ar-SA"

    @classmethod
    def from_environment(cls) -> "AzureSpeechConfig":
        endpoint = os.getenv("HIMMA_AZURE_SPEECH_ENDPOINT", "").strip().rstrip("/")
        key = os.getenv("HIMMA_AZURE_SPEECH_API_KEY", "").strip()
        if not endpoint or not key:
            raise ValueError("Azure Speech server-side configuration is incomplete")
        timeout = float(os.getenv("HIMMA_AZURE_SPEECH_TIMEOUT_SECONDS", "45"))
        if not 1 <= timeout <= 120:
            raise ValueError("Azure Speech timeout out of range")
        return cls(
            endpoint=endpoint,
            api_key=key,
            region=os.getenv("HIMMA_AZURE_SPEECH_REGION") or None,
            timeout_seconds=timeout,
            fast_reference_hint=os.getenv("HIMMA_AZURE_SPEECH_REFERENCE_HINT", "false").lower()
            in {"true", "yes", "on", "1"},
        )

    def __post_init__(self):
        parsed = urlparse(self.endpoint)
        host = parsed.hostname or ""
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Azure Speech endpoint must be a clean HTTPS URL")
        if not (host.endswith(".api.cognitive.microsoft.com")
                or host.endswith(".cognitiveservices.azure.com")):
            raise ValueError("Azure Speech endpoint hostname is not an approved Azure domain")
        if not self.api_key:
            raise ValueError("Azure Speech key is required")
        if not 1 <= self.timeout_seconds <= 120:
            raise ValueError("Azure Speech timeout out of range")

    def short_url(self, locale: str) -> str | None:
        host = urlparse(self.endpoint).hostname or ""
        region = self.region or (host.split(".")[0]
                                 if host.endswith(".api.cognitive.microsoft.com") else None)
        if region:
            if not all(ch.isalnum() or ch == "-" for ch in region):
                raise ValueError("Invalid Azure Speech region")
            return (f"https://{region}.stt.speech.microsoft.com/"
                    f"speech/recognition/conversation/cognitiveservices/v1"
                    f"?language={locale}&format=detailed")
        if host.endswith(".cognitiveservices.azure.com"):
            return (self.endpoint + "/speech/recognition/conversation/cognitiveservices/v1"
                    f"?language={locale}&format=detailed")
        return None

    @property
    def fast_url(self) -> str:
        return (self.endpoint +
                "/speechtotext/transcriptions:transcribe?api-version=2025-10-15")


@dataclass(frozen=True)
class SpeechEvidence:
    transcript: str | None
    source: str
    locale: str
    provider_usable: bool
    confidence: float | None = None
    recognition_status: str | None = None
    error_code: str | None = None
    request_id: str | None = None


@dataclass(frozen=True)
class PronunciationEvidence:
    transcript: str | None
    locale: str
    error_code: str | None
    accuracy_score: float | None = None
    fluency_score: float | None = None
    completeness_score: float | None = None
    pronunciation_score: float | None = None
    request_id: str | None = None


def _score(value: object) -> float | None:
    return float(value) if isinstance(value, (float, int)) and not isinstance(value, bool) else None


def _has_recognized_speech_text(text: object) -> bool:
    """A provider phrase must contain speech text, not punctuation alone.

    Do not guess a child's spoken language here. Arabic, Latin, Chinese,
    numerals and any other genuine letter/number remain usable recognition
    results for the academic comparator; only empty/symbol-only strings fail.
    """
    return (isinstance(text, str) and
            any(unicodedata.category(ch)[0] in {"L", "N"} for ch in text))


def _is_valid_pcm16_wav(audio: bytes) -> bool:
    try:
        with wave.open(BytesIO(audio), "rb") as wav:
            return (wav.getcomptype() == "NONE" and wav.getnchannels() == 1
                    and wav.getsampwidth() == 2 and wav.getframerate() == 16000
                    and wav.getnframes() > 0)
    except (wave.Error, EOFError, OSError):
        return False


class AzureSpeechProvider:
    def __init__(self, config: AzureSpeechConfig, http: httpx.AsyncClient):
        self.config = config
        self.http = http

    async def _short(self, audio: bytes, *, locale: str) -> SpeechEvidence:
        url = self.config.short_url(locale)
        if url is None:
            return SpeechEvidence(None, "short-audio", locale, False,
                                  error_code="short_endpoint_unavailable")
        try:
            r = await self.http.post(
                url, content=audio, timeout=self.config.timeout_seconds,
                headers={
                    "Ocp-Apim-Subscription-Key": self.config.api_key,
                    "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
                    "Accept": "application/json",
                },
            )
            request_id = r.headers.get("apim-request-id")
            if r.status_code != 200:
                return SpeechEvidence(None, "short-audio", locale, False,
                                      error_code=f"short_http_{r.status_code}",
                                      request_id=request_id)
            payload = r.json()
            best = (payload.get("NBest") or [{}])[0]
            transcript = (best.get("Display") or payload.get("DisplayText") or "").strip()
            status = payload.get("RecognitionStatus")
            usable = _has_recognized_speech_text(transcript) and status == "Success"
            return SpeechEvidence(
                transcript or None, "short-audio", locale, usable,
                confidence=_score(best.get("Confidence")), recognition_status=status,
                error_code=None if usable else "short_no_match",
                request_id=request_id,
            )
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError, AttributeError):
            return SpeechEvidence(None, "short-audio", locale, False,
                                  error_code="short_request_failed")

    async def _fast(self, audio: bytes, *, mime: str, reference: str,
                    locale: str) -> SpeechEvidence:
        definition: dict = {"locales": [locale]}
        if self.config.fast_reference_hint and reference.strip():
            definition["phraseList"] = {"phrases": [reference.strip()]}
        extension = {"audio/wav": "wav", "audio/webm": "webm", "audio/mp4": "m4a",
                     "audio/ogg": "ogg", "audio/mpeg": "mp3"}[mime]
        try:
            r = await self.http.post(
                self.config.fast_url, timeout=self.config.timeout_seconds,
                headers={"Ocp-Apim-Subscription-Key": self.config.api_key},
                files={
                    "audio": (f"reading.{extension}", audio, mime),
                    "definition": (None, json.dumps(definition), "application/json"),
                },
            )
            request_id = r.headers.get("apim-request-id")
            if r.status_code != 200:
                return SpeechEvidence(None, "fast-transcription", locale, False,
                                      error_code=f"fast_http_{r.status_code}",
                                      request_id=request_id)
            data = r.json()
            phrases = data.get("phrases") or []
            combined = data.get("combinedPhrases") or []
            transcript = (" ".join(str(part.get("text", "")).strip() for part in combined)
                          .strip()
                          or " ".join(str(part.get("text", "")).strip() for part in phrases).strip())
            confidences = [_score(p.get("confidence")) for p in phrases if isinstance(p, dict)]
            confidences = [n for n in confidences if n is not None]
            has_recognition = _has_recognized_speech_text(transcript)
            return SpeechEvidence(
                transcript if has_recognition else None, "fast-transcription", locale,
                has_recognition,
                confidence=sum(confidences) / len(confidences)
                if confidences else None,
                recognition_status="Success" if has_recognition else "NoMatch",
                error_code=None if has_recognition else "fast_no_match",
                request_id=request_id,
            )
        except (httpx.HTTPError, ValueError, TypeError, AttributeError, KeyError):
            return SpeechEvidence(None, "fast-transcription", locale, False,
                                  error_code="fast_request_failed")

    async def transcribe(self, audio: bytes, *, mime: str, reference: str,
                         letter_mode: bool) -> SpeechEvidence:
        if mime not in _SUPPORTED_MIME or len(audio) < 800 or len(audio) > _MAX_BYTES:
            return SpeechEvidence(None, "none", self.config.lexical_locale, False,
                                  error_code="audio_invalid")
        def acceptable(evidence: SpeechEvidence) -> bool:
            # A recognized non-Arabic token is still a recognition RESULT:
            # the reading policy decides correct/incorrect, not retry_audio.
            # letter_mode remains in this public adapter signature for callers.
            return bool(evidence.provider_usable
                        and _has_recognized_speech_text(evidence.transcript))
        if mime == "audio/wav":
            if not _is_valid_pcm16_wav(audio):
                return SpeechEvidence(None, "none", self.config.lexical_locale, False,
                                      error_code="wav_format_invalid")
            first = await self._short(audio, locale=self.config.lexical_locale)
            if acceptable(first):
                return first
        second = await self._fast(
            audio, mime=mime, reference=reference, locale=self.config.lexical_locale)
        if acceptable(second):
            return second
        return SpeechEvidence(
            None, second.source, self.config.lexical_locale, False,
            error_code=second.error_code or "transcript_not_usable",
            request_id=second.request_id,
        )

    async def assess_pronunciation(self, audio: bytes, *,
                                   reference: str) -> PronunciationEvidence:
        locale = self.config.pronunciation_locale
        if not _is_valid_pcm16_wav(audio):
            return PronunciationEvidence(None, locale, "wav_format_invalid")
        url = self.config.short_url(locale)
        if url is None:
            return PronunciationEvidence(None, locale, "pronunciation_endpoint_unavailable")
        assessment = {
            "ReferenceText": reference,
            "GradingSystem": "HundredMark",
            "Granularity": "Phoneme",
            "Dimension": "Comprehensive",
            "EnableMiscue": True,
        }
        encoded = base64.b64encode(json.dumps(
            assessment, ensure_ascii=False).encode("utf-8")).decode("ascii")
        try:
            r = await self.http.post(
                url, content=audio, timeout=self.config.timeout_seconds,
                headers={
                    "Ocp-Apim-Subscription-Key": self.config.api_key,
                    "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
                    "Pronunciation-Assessment": encoded,
                    "Accept": "application/json",
                },
            )
            request_id = r.headers.get("apim-request-id")
            if r.status_code != 200:
                return PronunciationEvidence(None, locale,
                                             f"pronunciation_http_{r.status_code}",
                                             request_id=request_id)
            data = r.json()
            best = (data.get("NBest") or [{}])[0]
            if data.get("RecognitionStatus") != "Success":
                return PronunciationEvidence(None, locale, "pronunciation_no_match",
                                             request_id=request_id)
            return PronunciationEvidence(
                best.get("Display") or data.get("DisplayText"), locale, None,
                accuracy_score=_score(best.get("AccuracyScore")),
                fluency_score=_score(best.get("FluencyScore")),
                completeness_score=_score(best.get("CompletenessScore")),
                pronunciation_score=_score(best.get("PronScore")),
                request_id=request_id,
            )
        except (httpx.HTTPError, ValueError, TypeError, IndexError, AttributeError):
            return PronunciationEvidence(None, locale, "pronunciation_request_failed")
