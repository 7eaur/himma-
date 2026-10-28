"""V2 persisted state must not advertise the abandoned free-writing workflow."""
import db.learning_models  # noqa: F401
from db.models import Base


def test_v2_metadata_does_not_contain_free_writing_tables_or_rewrite_tasks():
    assert "lesson_question_drafts" not in Base.metadata.tables
    assert "assessment_question_drafts" not in Base.metadata.tables
    table = Base.metadata.tables["v2_review_retry_tasks"]
    constraint = next(c for c in table.constraints if c.name == "ck_v2_retry_kind")
    assert "request_kind = 'rerecord'" in str(constraint.sqltext)
    assert "rewrite" not in str(constraint.sqltext)
