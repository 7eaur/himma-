"""Single evaluation policy for V2 letter, word, sentence and text readings.

Do not mount this into student endpoints until the native provider, DB job
lifecycle and release-gate tests are complete. This is an isolated pure core.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import unicodedata

from .aliases import LetterMatch, match_letter_transcript
from .scoring import WordScore, grade_words, training_hint


@dataclass(frozen=True)
class ReadingDecision:
    status: str
    reference: str
    fraction: Decimal | None
    passed_for_progress: bool | None
    hint: str | None
    reason: str
    alignment: WordScore | None = None
    alias: LetterMatch | None = None

    def student_payload(self, *, mode: str) -> dict:
        """No Azure metadata, ASR output, alias, confidence or debug code."""
        if mode not in {"training", "assessment"}:
            raise ValueError("Unknown activity mode")
        if self.status == "retry_audio":
            message = "ما فهمت قراءتك بوضوح. جرّب التسجيل مرة ثانية."
        elif mode == "assessment":
            message = "تم تسجيل قراءتك. نكمل السؤال التالي."
        elif self.status == "correct":
            message = "أحسنت! قراءتك صحيحة، هيا نكمل."
        else:
            message = self.hint or "انتبه للقراءة، ثم جرّب مرة ثانية."
        output = {"status": self.status, "message": message,
                  "reference": self.reference}
        if mode == "training" and self.status == "incorrect" and self.hint:
            output["hint"] = self.hint
        return output


def _contains_arabic(value: str) -> bool:
    return any("\u0600" <= char <= "\u06FF" and
               unicodedata.category(char).startswith("L") for char in value)


def evaluate_reading(
    *,
    kind: str,
    mode: str,
    reference: str,
    transcript: str | None,
    question_id: str,
    audio_valid: bool,
    provider_usable: bool,
    alignment_reliable: bool = False,
) -> ReadingDecision:
    """Owner policy with explicit provider failure and confidence boundaries.

    provider_usable must mean actual speech was recognized, not only that
    Azure returned HTTP 200. alignment_reliable is separately required to
    mark a *mismatch* wrong or to score multiple words from a transcript.
    """
    if kind not in {"letter", "word", "sentence", "text"}:
        raise ValueError("Unsupported reading task kind")
    if mode not in {"training", "assessment"}:
        raise ValueError("Unsupported reading task mode")
    if not isinstance(reference, str) or not reference.strip():
        raise ValueError("Reference is required")
    if not isinstance(question_id, str) or not question_id.strip():
        raise ValueError("Question ID is required")

    if not audio_valid:
        return ReadingDecision("retry_audio", reference, None, None, None, "audio_invalid")
    if not provider_usable or not isinstance(transcript, str) or not transcript.strip():
        return ReadingDecision("retry_audio", reference, None, None, None, "no_usable_transcript")

    if kind == "letter":
        alias = match_letter_transcript(question_id=question_id,
                                        reference=reference, transcript=transcript)
        if alias.matched:
            return ReadingDecision("correct", reference, Decimal("1"), True, None,
                                   "approved_letter_match", alias=alias)
        # A random Latin/Chinese transcript is a provider failure, not proof
        # that a child made an academic error.
        if not _contains_arabic(transcript) or not alignment_reliable:
            return ReadingDecision("retry_audio", reference, None, None, None,
                                   "unresolved_letter_transcript", alias=alias)
        return ReadingDecision("incorrect", reference, Decimal("0"), False,
                               "انتبه لحركة الحرف، ثم اقرأ مرة ثانية." if mode == "training" else None,
                               "confirmed_letter_mismatch", alias=alias)

    if not _contains_arabic(transcript):
        return ReadingDecision("retry_audio", reference, None, None, None,
                               "unrecognized_language")
    score = grade_words(reference, transcript)

    if kind == "word":
        if score.fully_correct:
            return ReadingDecision("correct", reference, Decimal("1"), True, None,
                                   "full_word_match", alignment=score)
        if not alignment_reliable:
            return ReadingDecision("retry_audio", reference, None, None, None,
                                   "word_mismatch_unconfirmed", alignment=score)
        return ReadingDecision("incorrect", reference, Decimal("0"), False,
                               training_hint(score) if mode == "training" else None,
                               "confirmed_word_mismatch", alignment=score)

    if not alignment_reliable:
        return ReadingDecision("retry_audio", reference, None, None, None,
                               "word_alignment_unconfirmed", alignment=score)
    passed = score.passed_assessment if mode == "assessment" else score.fully_correct
    return ReadingDecision(
        "correct" if passed else "incorrect",
        reference, score.fraction, passed,
        training_hint(score) if mode == "training" and not passed else None,
        "word_reading_scored",
        alignment=score,
    )
