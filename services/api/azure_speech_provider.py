"""Azure Speech fast-transcription adapter for Himma.

The adapter is opt-in via HIMMA_ASR_PROVIDER=azure-speech. It sends only the
audio payload, Arabic locale and (optionally) the canonical reference as a
phrase-list hint. Student identity is never sent to Azure.

Azure's transcript remains evidence only. Himma's own reference-guided
alignment and calibration/review gates remain authoritative for academic use.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from speech_provider import (
    ProviderPermanentError,
    ProviderResult,
    ProviderTemporaryError,
    ProviderWord,
)


class AzureSpeechProvider:
    name = "azure-speech"
    api_version = "2025-10-15"

    def __init__(self) -> None:
        self.endpoint = os.getenv("HIMMA_AZURE_SPEECH_ENDPOINT", "").strip().rstrip("/")
        self.api_key = os.getenv("HIMMA_AZURE_SPEECH_API_KEY", "").strip()
        self.reference_hint = os.getenv(
            "HIMMA_AZURE_SPEECH_REFERENCE_HINT", "false"
        ).strip().lower() in {"1", "true", "yes", "on"}
        self.timeout_seconds = float(
            os.getenv("HIMMA_AZURE_SPEECH_TIMEOUT_SECONDS", "45") or 45
        )

        if not self.endpoint:
            raise ProviderPermanentError("HIMMA_AZURE_SPEECH_ENDPOINT is required for Azure Speech")
        if not self.api_key:
            raise ProviderPermanentError("HIMMA_AZURE_SPEECH_API_KEY is required for Azure Speech")
        if self.timeout_seconds <= 0:
            raise ProviderPermanentError("HIMMA_AZURE_SPEECH_TIMEOUT_SECONDS must be positive")

    @staticmethod
    def _filename_for_mime(mime_type: str) -> str:
        mime = (mime_type or "").lower()
        if "webm" in mime:
            return "recording.webm"
        if "ogg" in mime or "opus" in mime:
            return "recording.ogg"
        if "wav" in mime or "wave" in mime:
            return "recording.wav"
        if "mpeg" in mime or "mp3" in mime:
            return "recording.mp3"
        if "flac" in mime:
            return "recording.flac"
        return "recording.bin"

    def transcribe_reference_guided(
        self,
        *,
        audio_bytes: bytes,
        mime_type: str,
        reference_text: str,
        language: str = "ar-OM",
    ) -> ProviderResult:
        if not audio_bytes:
            raise ProviderPermanentError("audio payload is empty")

        locale = language or "ar-OM"
        definition: dict[str, Any] = {"locales": [locale]}
        reference = reference_text.strip()
        if self.reference_hint and reference:
            # Deliberately opt-in. During calibration we compare runs with and
            # without phrase-list bias so the hint cannot silently hide reading
            # errors.
            definition["phraseList"] = {"phrases": [reference]}

        url = (
            f"{self.endpoint}/speechtotext/transcriptions:transcribe"
            f"?api-version={self.api_version}"
        )
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        files = {
            "audio": (
                self._filename_for_mime(mime_type),
                audio_bytes,
                mime_type or "application/octet-stream",
            ),
            "definition": (
                None,
                json.dumps(definition, ensure_ascii=False),
                "application/json",
            ),
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(url, headers=headers, files=files)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise ProviderTemporaryError(str(exc)) from exc
        except httpx.HTTPError as exc:
            raise ProviderTemporaryError(str(exc)) from exc

        if response.status_code in {408, 425, 429} or response.status_code >= 500:
            raise ProviderTemporaryError(
                f"Azure Speech temporary failure ({response.status_code})"
            )
        if response.status_code >= 400:
            detail = response.text[:500].strip()
            raise ProviderPermanentError(
                f"Azure Speech rejected the request ({response.status_code}): {detail}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderPermanentError("Azure Speech returned invalid JSON") from exc

        combined = payload.get("combinedPhrases") or []
        transcript = " ".join(
            str(part.get("text") or "").strip()
            for part in combined
            if isinstance(part, dict) and str(part.get("text") or "").strip()
        ).strip()
        if not transcript:
            transcript = " ".join(
                str(part.get("text") or "").strip()
                for part in (payload.get("phrases") or [])
                if isinstance(part, dict) and str(part.get("text") or "").strip()
            ).strip()

        phrase_confidences: list[float] = []
        words: list[ProviderWord] = []
        for phrase in payload.get("phrases") or []:
            if not isinstance(phrase, dict):
                continue
            confidence = phrase.get("confidence")
            if isinstance(confidence, (int, float)):
                phrase_confidences.append(float(confidence))
            for word in phrase.get("words") or []:
                if not isinstance(word, dict):
                    continue
                offset_ms = word.get("offsetMilliseconds")
                duration_ms = word.get("durationMilliseconds")
                start = float(offset_ms) / 1000.0 if isinstance(offset_ms, (int, float)) else None
                duration = (
                    float(duration_ms) / 1000.0
                    if isinstance(duration_ms, (int, float))
                    else None
                )
                end = start + duration if start is not None and duration is not None else None
                words.append(
                    ProviderWord(
                        text=str(word.get("text") or ""),
                        start_seconds=start,
                        end_seconds=end,
                        confidence=None,
                    )
                )

        confidence = (
            sum(phrase_confidences) / len(phrase_confidences)
            if phrase_confidences
            else None
        )
        duration_ms = payload.get("durationMilliseconds")
        duration_seconds = (
            float(duration_ms) / 1000.0
            if isinstance(duration_ms, (int, float))
            else None
        )
        request_id = (
            response.headers.get("apim-request-id")
            or response.headers.get("x-ms-request-id")
            or response.headers.get("x-requestid")
        )

        return ProviderResult(
            provider_name=self.name,
            model="azure-fast-transcription",
            transcript=transcript,
            confidence=confidence,
            request_id=request_id,
            duration_seconds=duration_seconds,
            words=tuple(words),
            raw_metadata={
                "api_version": self.api_version,
                "locale": locale,
                "reference_hint_used": bool(self.reference_hint and reference),
                "mime_type": mime_type,
                "phrase_count": len(payload.get("phrases") or []),
            },
        )
