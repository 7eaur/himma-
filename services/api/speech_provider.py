"""Replaceable ASR provider boundary for Himma speech analysis.

Runtime fails closed when no provider is configured. Tests may inject a
deterministic in-memory adapter explicitly; production never silently falls
back to fake recognition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Any, Protocol


class ProviderNotConfigured(RuntimeError):
    pass


class ProviderTemporaryError(RuntimeError):
    """Retryable provider/network failure."""


class ProviderPermanentError(RuntimeError):
    """Non-retryable provider/request failure."""


@dataclass(frozen=True)
class ProviderWord:
    text: str
    start_seconds: float | None = None
    end_seconds: float | None = None
    confidence: float | None = None


@dataclass(frozen=True)
class ProviderResult:
    provider_name: str
    model: str | None
    transcript: str
    confidence: float | None = None
    request_id: str | None = None
    duration_seconds: float | None = None
    words: tuple[ProviderWord, ...] = ()
    raw_metadata: dict[str, Any] = field(default_factory=dict)


class SpeechProvider(Protocol):
    name: str

    def transcribe_reference_guided(
        self,
        *,
        audio_bytes: bytes,
        mime_type: str,
        reference_text: str,
        language: str = "ar",
    ) -> ProviderResult:
        ...


class UnconfiguredSpeechProvider:
    name = "unconfigured"

    def transcribe_reference_guided(self, **_: Any) -> ProviderResult:
        raise ProviderNotConfigured(
            "ASR provider is not configured. Configure an approved provider before real speech scoring."
        )


def build_provider() -> SpeechProvider:
    """Build the explicitly configured production provider.

    Google STT V2 is an evaluation candidate for M08. Its presence here does not
    mean that automatic academic acceptance is calibrated; the existing
    calibration guard and supervisor review policy remain authoritative.
    """

    provider = os.getenv("HIMMA_ASR_PROVIDER", "").strip().lower()
    if not provider:
        return UnconfiguredSpeechProvider()
    if provider in {"google", "google-stt-v2", "google_cloud_stt_v2"}:
        try:
            from google_speech_provider import GoogleSpeechV2Provider

            return GoogleSpeechV2Provider()
        except ProviderPermanentError as exc:
            raise ProviderNotConfigured(str(exc)) from exc
    raise ProviderNotConfigured(f"Unsupported HIMMA_ASR_PROVIDER={provider!r}")
