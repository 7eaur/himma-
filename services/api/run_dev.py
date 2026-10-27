import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

required = ("DATABASE_URL", "API_SECRET_KEY", "S3_ACCESS_KEY", "S3_SECRET_KEY")
missing = [name for name in required if not os.environ.get(name)]
if missing:
    raise RuntimeError(
        "Missing required local environment variables: " + ", ".join(missing)
    )

os.environ.setdefault("S3_ENDPOINT", "http://localhost:9000")
os.environ.setdefault("S3_BUCKET_NAME", "himma-audio")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENV", "development")

import uvicorn


CANONICAL_RUNTIME_COUNTS = {
    "total_items": 125,
    "canonical_release_items": 125,
    "db_runtime_items": 125,
    "pretest_experience_items": 30,
    "learning_experience_items": 65,
    "posttest_experience_items": 30,
}


def validate_local_runtime_content_result(result: dict) -> None:
    """Fail closed unless the canonical publisher returned the current contract.

    ``seed_all.run_seed_all`` is the only local content synchronization entrypoint.
    Historical correction/projection seeds deliberately are not consulted here.
    """
    mismatches = {
        key: (result.get(key), expected)
        for key, expected in CANONICAL_RUNTIME_COUNTS.items()
        if result.get(key) != expected
    }
    release_sha = str(result.get("canonical_release_sha256") or "")
    if len(release_sha) != 64:
        mismatches["canonical_release_sha256"] = (release_sha or None, "64-char sha256")
    if mismatches:
        details = ", ".join(
            f"{key}={actual!r} (expected {expected!r})"
            for key, (actual, expected) in sorted(mismatches.items())
        )
        raise RuntimeError(
            "Local Himma content synchronization did not reach the approved canonical runtime contract: "
            + details
        )


def sync_local_runtime_content() -> None:
    """Idempotently project the approved 125-item runtime into the existing DB.

    This updates content rows by their stable identifiers and does not drop the
    database, student accounts, attempts, mastery evidence, or history.
    Production/trial startup remains migration-driven and never auto-mutates
    content through this development helper.
    """
    from seed_all import run_seed_all

    result = run_seed_all()
    validate_local_runtime_content_result(result)


if __name__ == "__main__":
    sync_local_runtime_content()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
