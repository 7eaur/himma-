"""Idempotent maintenance corrections for approved choice presentation.

These corrections repair import/runtime presentation gaps without rewriting the
immutable approved catalog. They keep each canonical item, correct answer,
scoring rule, skill, and activity order unchanged.

Covered source-grounded corrections:
- L1-CORE-03: the approved client content requires the correct connected letter
  form plus three forms of other letters in every round.
- L1-REIN-03: the approved client content says the learner HEARS one of five
  approved words and chooses its picture from THREE images in every round. The
  legacy parser persisted only the correct option and flattened the interaction
  to text choice, so this repair restores two same-activity distractors, the
  approved listen+image presentation, and manifest-backed image links.
"""

from __future__ import annotations

from db.database import SessionLocal
from db.models import ContentAssetLink, ContentItem, ContentOption

LETTER_FORM_ITEM = "L1-CORE-03"
LETTER_FORM_POOL = ["بـ", "مـ", "سـ", "كـ", "لـ"]

WORD_IMAGE_ITEM = "L1-REIN-03"
WORD_IMAGE_POOL = ["باب", "قلم", "شمس", "سمكة", "كرة"]
WORD_IMAGE_ASSETS = {
    "باب": "VOC-03",
    "قلم": "VOC-04",
    "سمكة": "VOC-05",
    "شمس": "VOC-06",
    "كرة": "VOC-10",
}


def _find_item(db, canonical: str) -> ContentItem | None:
    direct = db.query(ContentItem).filter(ContentItem.stable_key == canonical).first()
    if direct is not None:
        return direct
    return next(
        (
            item
            for item in db.query(ContentItem).all()
            if str((item.template_data or {}).get("canonical_id") or "") == canonical
        ),
        None,
    )


def _ensure_option_count(step, *, pool: list[str], total: int) -> int:
    existing = sorted(step.options, key=lambda value: value.order_index)
    if not existing:
        raise RuntimeError(f"Step {step.id} has no approved correct option")

    correct = next((option for option in existing if option.is_correct), existing[0])
    current_texts = {option.text for option in existing}
    distractors = [value for value in pool if value != correct.text]
    if len(distractors) < total - 1:
        raise RuntimeError(f"Not enough approved distractors for step {step.id}")

    offset = max(0, int(step.order_index) - 1) % len(distractors)
    rotated = distractors[offset:] + distractors[:offset]
    created = 0
    for value in rotated:
        if len(current_texts) >= total:
            break
        if value in current_texts:
            continue
        step.options.append(ContentOption(
            text=value,
            is_correct=False,
            order_index=len(current_texts) + 1,
        ))
        current_texts.add(value)
        created += 1
    return created


def _ensure_word_image_assets(step) -> int:
    created = 0
    existing_ids = {
        link.manifest_asset_id
        for link in step.assets
        if link.asset_type == "image" and link.usage_context == "choice"
    }
    for option in sorted(step.options, key=lambda value: value.order_index):
        asset_id = WORD_IMAGE_ASSETS.get(option.text)
        if not asset_id or asset_id in existing_ids:
            continue
        step.assets.append(ContentAssetLink(
            manifest_asset_id=asset_id,
            asset_type="image",
            usage_context="choice",
        ))
        existing_ids.add(asset_id)
        created += 1
    return created


def run_seed() -> int:
    db = SessionLocal()
    created = 0
    try:
        letter_forms = _find_item(db, LETTER_FORM_ITEM)
        if letter_forms is not None:
            for step in sorted(letter_forms.steps, key=lambda value: value.order_index):
                created += _ensure_option_count(step, pool=LETTER_FORM_POOL, total=4)

        word_images = _find_item(db, WORD_IMAGE_ITEM)
        if word_images is not None:
            data = dict(word_images.template_data or {})
            if data.get("canonical_interaction_type") != "listen_choose_image":
                data["canonical_interaction_type"] = "listen_choose_image"
                word_images.template_data = data
            for step in sorted(word_images.steps, key=lambda value: value.order_index):
                created += _ensure_option_count(step, pool=WORD_IMAGE_POOL, total=3)
                created += _ensure_word_image_assets(step)

        db.commit()
        return created
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(f"Created {run_seed()} approved choice-presentation corrections")
