"""Himma V2 native speech engine; isolated until full release acceptance."""
from .aliases import LetterMatch, load_alias_catalog, match_letter_transcript
from .policy import ReadingDecision, evaluate_reading
from .scoring import WordAlignment, WordScore, align_words, assessment_total, grade_words, training_hint

__all__ = [
    "LetterMatch", "load_alias_catalog", "match_letter_transcript",
    "ReadingDecision", "evaluate_reading",
    "WordAlignment", "WordScore", "align_words", "assessment_total",
    "grade_words", "training_hint",
]
