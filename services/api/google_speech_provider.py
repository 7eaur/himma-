"""Google Cloud Speech-to-Text V2 adapter for Himma's speech provider boundary.

The adapter is opt-in via HIMMA_ASR_PROVIDER=google-stt-v2 and uses Application
Default Credentials on the server. It never receives or sends student identity;
only audio bytes, the Arabic locale and (optionally) the canonical reference
phrase used as a bounded recognition hint.

The reference is a recognition hint only. The raw transcript is preserved and
Himma's own reference-guided alignment remains the decision evidence layer.
"""

from __future__ import annotations

import os
from typing import Any

from speech_provider import (
    ProviderPermanentError,
    ProviderResult,
    ProviderTemporaryError,
    ProviderWord,
)


class GoogleSpeechV2Provider:
    name = "google-stt-v2"

    def __init__(self) -> None:
        self.project_id = os.getenv("HIMMA_GOOGLE_CLOUD_PROJECT", "").strip()
        self.location = os.getenv("HIMMA_GOOGLE_STT_LOCATION", "global").strip() or "global"
        self.model = os.getenv("HIMMA_GOOGLE_STT_MODEL", "short").strip() or "short"
        self.reference_boost = float(os.getenv("HIMMA_GOOGLE_STT_REFERENCE_BOOST", "0") or 0)
        self.timeout_seconds = float(os.getenv("HIMMA_GOOGLE_STT_TIMEOUT_SECONDS", "30") or 30)
        if not self.project_id:
            raise ProviderPermanentError("HIMMA_GOOGLE_CLOUD_PROJECT is required for Google STT V2")
        if not 0 <= self.reference_boost <= 20:
            raise ProviderPermanentError("HIMMA_GOOGLE_STT_REFERENCE_BOOST must be between 0 and 20")

    @staticmethod
    def _duration_seconds(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value.total_seconds())
        except (AttributeError, TypeError, ValueError):
            seconds = getattr(value, "seconds", None)
            nanos = getattr(value, "nanos", None)
            if seconds is None:
                return None
            return float(seconds) + float(nanos or 0) / 1_000_000_000

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

        try:
            from google.api_core import exceptions as google_exceptions
            from google.cloud.speech_v2 import SpeechClient
            from google.cloud.speech_v2.types import cloud_speech
        except ImportError as exc:
            raise ProviderPermanentError("google-cloud-speech dependency is not installed") from exc

        adaptation = None
        # Start unboosted by default. A positive boost is only enabled explicitly
        # during lab calibration because over-biasing can hide real reading errors.
        if reference_text.strip() and self.reference_boost > 0:
            phrase = cloud_speech.PhraseSet.Phrase(
                value=reference_text.strip(),
                boost=self.reference_boost,
            )
            phrase_set = cloud_speech.PhraseSet(phrases=[phrase])
            adaptation = cloud_speech.SpeechAdaptation(
                phrase_sets=[
                    cloud_speech.SpeechAdaptation.AdaptationPhraseSet(
                        inline_phrase_set=phrase_set
                    )
                ]
            )

        features = cloud_speech.RecognitionFeatures(
            enable_word_time_offsets=True,
            enable_word_confidence=True,
            enable_automatic_punctuation=False,
        )
        config_kwargs: dict[str, Any] = {
            "auto_decoding_config": cloud_speech.AutoDetectDecodingConfig(),
            "language_codes": [language or "ar-OM"],
            "model": self.model,
            "features": features,
        }
        if adaptation is not None:
            config_kwargs["adaptation"] = adaptation
        config = cloud_speech.RecognitionConfig(**config_kwargs)

        request = cloud_speech.RecognizeRequest(
            recognizer=(
                f"projects/{self.project_id}/locations/{self.location}/recognizers/_"
            ),
            config=config,
            content=audio_bytes,
        )

        try:
            client = SpeechClient()
            response = client.recognize(request=request, timeout=self.timeout_seconds)
        except (
            google_exceptions.DeadlineExceeded,
            google_exceptions.ServiceUnavailable,
            google_exceptions.TooManyRequests,
            google_exceptions.ResourceExhausted,
            google_exceptions.InternalServerError,
        ) as exc:
            raise ProviderTemporaryError(str(exc)) from exc
        except google_exceptions.GoogleAPICallError as exc:
            raise ProviderPermanentError(str(exc)) from exc
        except Exception as exc:  # credential/configuration errors fail closed
            raise ProviderPermanentError(str(exc)) from exc

        transcripts: list[str] = []
        words: list[ProviderWord] = []
        result_confidences: list[float] = []
        for result in response.results:
            if not result.alternatives:
                continue
            alternative = result.alternatives[0]
            if alternative.transcript:
                transcripts.append(alternative.transcript.strip())
            confidence = float(alternative.confidence or 0)
            if confidence > 0:
                result_confidences.append(confidence)
            for word in alternative.words:
                word_confidence = float(word.confidence or 0)
                words.append(
                    ProviderWord(
                        text=word.word,
                        start_seconds=self._duration_seconds(word.start_offset),
                        end_seconds=self._duration_seconds(word.end_offset),
                        confidence=word_confidence if word_confidence > 0 else None,
                    )
                )

        transcript = " ".join(part for part in transcripts if part).strip()
        confidence = (
            sum(result_confidences) / len(result_confidences)
            if result_confidences
            else None
        )
        request_id = getattr(getattr(response, "metadata", None), "request_id", None)

        return ProviderResult(
            provider_name=self.name,
            model=self.model,
            transcript=transcript,
            confidence=confidence,
            request_id=str(request_id) if request_id is not None else None,
            words=tuple(words),
            raw_metadata={
                "language": language or "ar-OM",
                "location": self.location,
                "reference_hint_used": adaptation is not None,
                "reference_boost": self.reference_boost if adaptation is not None else 0,
                "mime_type": mime_type,
            },
        )
