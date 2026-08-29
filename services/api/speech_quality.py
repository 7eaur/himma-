"""Conservative recording-quality gates for Himma speech analysis.

These gates protect the ASR pipeline from obviously unusable recordings. They do
not grade pronunciation and do not mutate academic state.
"""

from __future__ import annotations

from dataclasses import dataclass


_ALLOWED_AUDIO_MIME_TYPES = {
    "audio/webm",
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp4",
    "audio/ogg",
    "application/ogg",
}
MIN_AUDIO_BYTES = 16
MIN_DURATION_SECONDS = 0.20


@dataclass(frozen=True)
class RecordingQualityError(ValueError):
    code: str
    message: str
    rerecord_required: bool = True

    def __str__(self) -> str:
        return self.message


def validate_recording_input(
    *,
    audio_bytes: bytes,
    mime_type: str | None,
    duration_seconds: float | None = None,
    max_bytes: int | None = None,
) -> dict[str, object]:
    """Reject obviously unusable input before it reaches a paid ASR provider."""
    if not audio_bytes:
        raise RecordingQualityError("empty_audio", "ملف التسجيل فارغ")
    if max_bytes is not None and len(audio_bytes) > max_bytes:
        raise RecordingQualityError("audio_too_large", "ملف التسجيل أكبر من الحد المسموح")
    if len(audio_bytes) < MIN_AUDIO_BYTES:
        raise RecordingQualityError("audio_too_short", "التسجيل قصير جدًا؛ أعد التسجيل بصوت واضح")

    normalized_mime = (mime_type or "").split(";", 1)[0].strip().lower()
    if normalized_mime and normalized_mime not in _ALLOWED_AUDIO_MIME_TYPES:
        raise RecordingQualityError("unsupported_audio_type", "صيغة التسجيل غير مدعومة")

    if duration_seconds is not None and duration_seconds < MIN_DURATION_SECONDS:
        raise RecordingQualityError("audio_too_short", "التسجيل قصير جدًا؛ أعد التسجيل بصوت واضح")

    return {
        "status": "input_accepted",
        "bytes": len(audio_bytes),
        "mime_type": normalized_mime or None,
        "duration_seconds": duration_seconds,
        "academic_effect": "none",
    }


def validate_provider_output(*, transcript: str | None, duration_seconds: float | None = None) -> dict[str, object]:
    """Fail closed when the provider found no usable speech evidence."""
    if not (transcript or "").strip():
        raise RecordingQualityError("no_speech_detected", "لم يتم اكتشاف كلام واضح؛ أعد التسجيل")
    if duration_seconds is not None and duration_seconds < MIN_DURATION_SECONDS:
        raise RecordingQualityError("audio_too_short", "التسجيل قصير جدًا للتحليل؛ أعد التسجيل")
    return {
        "status": "provider_output_accepted",
        "duration_seconds": duration_seconds,
        "academic_effect": "none",
    }
