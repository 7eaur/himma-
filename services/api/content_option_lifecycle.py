"""Publish an exact option set without changing the meaning of historical IDs."""
import re
import unicodedata

from db.models import ContentOption


def visible_key(value: str) -> str:
    # Vowels and contextual forms (ب vs بـ) are academic content, not noise.
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2066-\u2069]", "", value)
    return re.sub(r"\s+", " ", value).strip()


def set_exact_current_options(db, step, desired, *, allow_repeated=False) -> dict[str, int]:
    desired = [(str(text), bool(correct)) for text, correct in desired]
    keys = [visible_key(text) for text, _ in desired]
    if any(not key for key in keys):
        raise ValueError("Empty option is not publishable")
    if not allow_repeated and len(set(keys)) != len(keys):
        raise ValueError("Duplicate visible options are not publishable")
    rows = db.query(ContentOption).filter(ContentOption.step_id == step.id).order_by(ContentOption.id).all()
    before = {row.id for row in rows if row.is_active}
    selected = set()
    created = 0
    for order, (text, correct) in enumerate(desired, 1):
        row = next((r for r in rows if r.id not in selected and (r.text, bool(r.is_correct), r.order_index) == (text, correct, order)), None)
        if row is None:
            row = ContentOption(step_id=step.id, text=text, is_correct=correct, order_index=order, is_active=True)
            db.add(row)
            db.flush()
            rows.append(row)
            created += 1
        selected.add(row.id)
    for row in rows:
        row.is_active = row.id in selected
    db.flush()
    db.expire(step, ["options"])
    return {"created": created, "retired": len(before - selected), "reactivated": len(selected - before) - created}
