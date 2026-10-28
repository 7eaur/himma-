#!/usr/bin/env python3
"""Verify restored PostgreSQL rows, not only table counts, for the full V2 model.

Run after restoring a consistent backup into an isolated database. Source
writes must be paused, or a later source mutation can legitimately differ.
No student data, hashes, or credentials are printed.
"""

from __future__ import annotations

from hashlib import sha256
import json
import os
import sys

from sqlalchemy import create_engine, inspect, text


# All critical academic, review, reward and audio evidence survives a backup.
# Exclude retired V2 writing draft tables; they are removed by migration 0031.
TABLES = (
    "users",
    "students",
    "skills",
    "content_releases",
    "content_items",
    "content_steps",
    "content_options",
    "content_asset_links",
    "scoring_policies",
    "scoring_rules",
    "assessment_sessions",
    "assessment_retake_authorizations",
    "audit_logs",
    "audio_submissions",
    "student_journeys",
    "lesson_sessions",
    "lesson_progress_events",
    "lesson_question_responses",
    "support_assignments",
    "skill_evidence",
    "adaptation_decisions_v2",
    "assessment_question_responses",
    "placement_decisions_v2",
    "v2_lesson_review_actions",
    "v2_review_retry_tasks",
    "v2_review_claims",
    "v2_audio_rubrics",
    "v2_audio_upload_leases",
    "v2_audio_purge_tasks",
    "v2_reward_grants",
    "private_content_bank_snapshots",
)


def _fingerprints(url: str) -> dict[str, tuple[int, str]]:
    engine = create_engine(url)
    output: dict[str, tuple[int, str]] = {}
    try:
        schema = inspect(engine)
        existing = set(schema.get_table_names())
        missing = set(TABLES) - existing
        if missing:
            raise RuntimeError(f"Backup verification schema missing: {', '.join(sorted(missing))}")
        with engine.connect() as connection:
            for table in TABLES:
                columns = schema.get_pk_constraint(table).get("constrained_columns") or []
                if not columns:
                    raise RuntimeError(f"Cannot deterministically verify {table} without a primary key")
                quoted = connection.dialect.identifier_preparer.quote(table)
                order = ", ".join(connection.dialect.identifier_preparer.quote(c) for c in columns)
                digest = sha256()
                count = 0
                # Read in primary-key order to detect replaced or modified rows
                # even when the source and restore have exactly the same counts.
                statement = text(f"SELECT * FROM {quoted} ORDER BY {order}")
                for row in connection.execution_options(stream_results=True).execute(statement).mappings():
                    encoded = json.dumps(dict(row), sort_keys=True, default=str, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                    digest.update(len(encoded).to_bytes(8, "big"))
                    digest.update(encoded)
                    count += 1
                output[table] = (count, digest.hexdigest())
    finally:
        engine.dispose()
    return output


def main() -> int:
    source_url = os.getenv("DATABASE_URL", "").strip()
    restore_url = os.getenv("RESTORE_DATABASE_URL", "").strip()
    if not source_url or not restore_url:
        print("DATABASE_URL and RESTORE_DATABASE_URL are required", file=sys.stderr)
        return 2
    source = _fingerprints(source_url)
    restored = _fingerprints(restore_url)
    mismatch = [table for table in TABLES if source[table] != restored[table]]
    if mismatch:
        print(f"Backup/restore mismatch in tables: {', '.join(mismatch)}", file=sys.stderr)
        return 1
    print(f"PostgreSQL restore verified: {len(TABLES)} tables, identical ordered row digests.")
    print("No student data or private fingerprints disclosed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
