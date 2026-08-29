"""Idempotent maintenance corrections for approved choice presentation.

The approved client content for L1 core activity 3 says each letter-form round
shows the correct connected form *alongside three forms of other letters*.
The V1 parser historically persisted only the correct form, producing a one-
option question in the UI. This additive runtime correction restores the three
required distractors without changing the canonical item, correct answer,
scoring, or the immutable 105-item catalog.
"""

from __future__ import annotations

from db.database import SessionLocal
from db.models import ContentItem, ContentOption

CANONICAL_ID = "L1-CORE-03"
# All values are letter forms already present as correct targets inside the same
# approved activity. Rotating them provides real alternatives without inventing
# a new skill or answer.
APPROVED_FORM_POOL = ["بـ", "مـ", "سـ", "كـ", "لـ"]


def run_seed() -> int:
    db = SessionLocal()
    created = 0
    try:
        item = db.query(ContentItem).filter(
            ContentItem.stable_key == CANONICAL_ID
        ).first()
        if item is None:
            item = next(
                (
                    candidate
                    for candidate in db.query(ContentItem).all()
                    if str((candidate.template_data or {}).get("canonical_id") or "") == CANONICAL_ID
                ),
                None,
            )
        if item is None:
            return 0

        for step in sorted(item.steps, key=lambda value: value.order_index):
            existing = sorted(step.options, key=lambda value: value.order_index)
            if not existing:
                raise RuntimeError(f"{CANONICAL_ID} round {step.order_index} has no approved correct form")
            correct = next((option for option in existing if option.is_correct), existing[0])
            current_texts = {option.text for option in existing}
            distractors = [value for value in APPROVED_FORM_POOL if value != correct.text]
            # Rotate by round so neighbouring rounds do not always show the same
            # alternatives. The pool itself comes from this approved activity.
            offset = max(0, step.order_index - 1) % len(distractors)
            ordered = distractors[offset:] + distractors[:offset]
            for value in ordered[:3]:
                if value in current_texts:
                    continue
                db.add(ContentOption(
                    step_id=step.id,
                    text=value,
                    is_correct=False,
                    order_index=len(current_texts) + 1,
                ))
                current_texts.add(value)
                created += 1

        db.commit()
        return created
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(f"Created {run_seed()} approved letter-form distractors")
