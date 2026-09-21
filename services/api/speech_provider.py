"""Replaceable speech-provider boundary for Himma.

There are two deliberately separate factories:

* build_provider is the production worker boundary for stored student audio.
  It fails closed unless the provider is explicitly approved in code governance.
* build_evaluation_provider is supervisor-only Speech Lab evaluation. It may
  call a configured candidate provider, but its outputs are always non-academic.

This separation prevents credentials or environment variables from silently
turning an experimental vendor into production academic authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Any, Protocol

from asr_governance import runtime_provider_is_approved


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

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or "ASR provider is not configured"

    def transcribe_reference_guided(self, **_: Any) -> ProviderResult:
        raise ProviderNotConfigured(self.detail)


_PROVIDER_ALIASES = {
    "azure": "azure-speech",
    "azure-speech": "azure-speech",
    "azure_speech": "azure-speech",
    "google": "google-stt-v2",
    "google-stt-v2": "google-stt-v2",
    "google_cloud_stt_v2": "google-stt-v2",
}


def canonical_provider_name(value: str) -> str:
    normalized = (value or "").strip().lower()
    return _PROVIDER_ALIASES.get(normalized, normalized)


def _instantiate_provider(provider_name: str) -> SpeechProvider:
    provider_name = canonical_provider_name(provider_name)
    if provider_name == "azure-speech":
        try:
            from azure_speech_provider import AzureSpeechProvider

            return AzureSpeechProvider()
        except ProviderPermanentError as exc:
            raise ProviderNotConfigured(str(exc)) from exc
    if provider_name == "google-stt-v2":
        try:
            from google_speech_provider import GoogleSpeechV2Provider

            return GoogleSpeechV2Provider()
        except ProviderPermanentError as exc:
            raise ProviderNotConfigured(str(exc)) from exc
    raise ProviderNotConfigured(f"Unsupported speech provider {provider_name!r}")


def build_provider() -> SpeechProvider:
    """Build the production worker provider, failing closed by governance.

    The live project currently has no approved external runtime provider. Even if
    a deployment accidentally contains provider credentials, student recordings
    are not sent externally until APPROVED_ASR_RUNTIME_PROVIDERS is changed by a
    reviewed code/ADR decision.
    """

    configured = os.getenv("HIMMA_ASR_PROVIDER", "").strip()
    if not configured:
        return UnconfiguredSpeechProvider(
            "Production ASR provider is not approved/configured. Human review remains authoritative."
        )
    provider_name = canonical_provider_name(configured)
    if not runtime_provider_is_approved(provider_name):
        raise ProviderNotConfigured(
            f"Production provider {provider_name!r} is not approved for student-audio transfer"
        )
    return _instantiate_provider(provider_name)


def build_evaluation_provider() -> SpeechProvider:
    """Build a Speech Lab candidate provider without enabling student-audio ASR."""

    configured = os.getenv("HIMMA_SPEECH_LAB_PROVIDER", "").strip()
    if not configured:
        return UnconfiguredSpeechProvider(
            "Speech Lab provider is not configured. Set HIMMA_SPEECH_LAB_PROVIDER for evaluation."
        )
    return _instantiate_provider(configured)
