"""Explicit, offline erasure of owner-declared disposable test accounts.

Not an API, seed, migration, scheduled job, or application startup hook.
Default mode is read-only. Execution requires an exact dry-run fingerprint,
the expected cohort size, and inactive accounts. Shared content/users survive.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import re

from sqlalchemy import MetaData, delete, func, or_, select, update


def erasure_plan(db, student_ids: list[int], expected_total: int, *, lock=False, list_audio=None) -> dict:
    metadata = MetaData()
    metadata.reflect(bind=db.get_bind())
    tables = metadata.tables
    students = tables["students"]
    total = db.scalar(select(func.count()).select_from(students))
    selected_query = select(students.c.id).where(students.c.id.in_(student_ids))
    selected = set(db.scalars(selected_query.with_for_update() if lock else selected_query))
    if not selected:
        # Absent IDs are not proof of erasure when the supposedly disposable
        # cohort was replaced by unrelated accounts, or private audio remains.
        # In either case refuse a misleading "already absent" result.
        if total >= expected_total:
            raise ValueError("Cohort changed: authorized IDs absent but an unexpected student cohort remains")
        if list_audio is not None:
            for student_id in student_ids:
                if any(True for _ in list_audio(student_id)):
                    raise ValueError("Private audio remains for an absent test student; reconcile storage first")
        return {"already_absent": True, "student_ids": student_ids, "counts": {}, "audio_objects": 0}
    if total != expected_total or selected != set(student_ids):
        raise ValueError("Cohort changed: exact IDs and total must match the owner's authorized scope")
    owned = {"students": selected}
    changed = True
    while changed:
        changed = False
        for table in tables.values():
            conditions = [fk.parent.in_(owned[fk.column.table.name]) for fk in table.foreign_keys
                          if fk.column.table.name in owned and fk.column.name == "id"]
            if not conditions:
                continue
            primary = list(table.primary_key.columns)
            if len(primary) != 1 or primary[0].name != "id":
                raise ValueError(f"Cannot safely scope dependent table {table.name}")
            found = set(db.scalars(select(table.c.id).where(or_(*conditions))))
            previous = owned.setdefault(table.name, set())
            if found - previous:
                previous.update(found); changed = True
    # These ownership fields are intentionally not foreign keys.
    for name, table in tables.items():
        if "actor_role" in table.c and "actor_id" in table.c:
            conditions = [(table.c.actor_role == "student") & table.c.actor_id.in_(student_ids)]
            if name == "audit_logs":
                conditions.append((table.c.entity_type == "student") & table.c.entity_id.in_([str(i) for i in student_ids]))
            owned[name] = set(db.scalars(select(table.c.id).where(or_(*conditions))))
    notifications = tables.get("researcher_notifications")
    if notifications is not None:
        entity_ids = {"audio_submission": owned.get("audio_submissions", set()),
                      "reinforcement_cycle": owned.get("reinforcement_cycles", set())}
        attention_ids = {f"{prefix}:{row_id}" for prefix, table_name in (
            ("assessment", "assessment_question_responses"), ("lesson", "lesson_question_responses"),
            ("placement", "assessment_sessions"), ("support", "support_assignments"),
        ) for row_id in owned.get(table_name, set())}
        conditions = [(notifications.c.entity_type == kind) & notifications.c.entity_id.in_([str(i) for i in ids])
                      for kind, ids in entity_ids.items() if ids]
        if attention_ids:
            conditions.append((notifications.c.entity_type == "v2_attention") & notifications.c.entity_id.in_(attention_ids))
        if conditions:
            owned[notifications.name] = set(db.scalars(select(notifications.c.id).where(or_(*conditions))))
    snapshot = {}
    audio = set()
    def collect(value):
        if isinstance(value, dict):
            for child in value.values(): collect(child)
        elif isinstance(value, list):
            for child in value: collect(child)
        elif isinstance(value, str) and re.match(r"^audio/[0-9]+/", value):
            if not any(value.startswith(f"audio/{i}/") for i in student_ids):
                raise ValueError("Cross-student audio ownership detected")
            audio.add(value)
    for name, ids in owned.items():
        if not ids:
            continue
        table = tables[name]
        query = select(table).where(table.c.id.in_(ids)).order_by(table.c.id)
        rows = [dict(row) for row in db.execute(query.with_for_update() if lock else query).mappings()]
        if name != "students" and "student_id" in table.c and any(row["student_id"] not in selected for row in rows):
            raise ValueError(f"Cross-student dependency in {name}")
        snapshot[name] = rows
        collect(rows)
    if list_audio is not None:
        for student_id in student_ids:
            for key in list_audio(student_id):
                if not key.startswith(f"audio/{student_id}/"):
                    raise ValueError("Object listing escaped the authorized student prefix")
                audio.add(key)
    encoded = json.dumps({"rows": snapshot, "audio": sorted(audio)}, sort_keys=True, default=str, separators=(",", ":")).encode()
    return {"already_absent": False, "student_ids": sorted(selected),
            "counts": {name: len(rows) for name, rows in sorted(snapshot.items())},
            "audio_objects": len(audio), "fingerprint": sha256(encoded).hexdigest(),
            "_metadata": metadata, "_owned": owned, "_snapshot": snapshot, "_audio": audio,
            "_expected_total": expected_total, "_list_audio": list_audio}


def _remove_owned_rows(db, metadata, owned: dict) -> None:
    """Delete only the precomputed student-owned closure in safe FK order.

    Used by both the transactional savepoint preflight and the real operation;
    they must execute the identical database changes.
    """
    for name, ids in owned.items():
        table = metadata.tables[name]
        nullable = {fk.parent.name: None for fk in table.foreign_keys
                    if fk.parent.nullable and fk.column.table.name == name}
        if nullable:
            db.execute(update(table).where(table.c.id.in_(ids)).values(**nullable))
    remaining = set(owned)
    while remaining:
        leaves = [name for name in remaining if not any(
            other != name and any(fk.column.table.name == name and fk.ondelete != "SET NULL"
                                  for fk in metadata.tables[other].foreign_keys)
            for other in remaining)]
        if not leaves:
            raise ValueError("Non-null dependency cycle: database deletion refused")
        for name in sorted(leaves):
            db.execute(delete(metadata.tables[name]).where(metadata.tables[name].c.id.in_(owned[name])))
            remaining.remove(name)


def execute_erasure(db, plan: dict, fingerprint: str, delete_audio) -> dict:
    if plan["already_absent"]:
        return public_plan(plan)
    if fingerprint != plan["fingerprint"]:
        raise ValueError("Dry-run fingerprint does not match; no data was deleted")
    fresh = erasure_plan(db, plan["student_ids"], plan["_expected_total"], lock=True, list_audio=plan["_list_audio"])
    if fresh.get("fingerprint") != fingerprint:
        raise ValueError("Data changed since dry-run; deletion refused")
    plan = fresh
    metadata = plan["_metadata"]
    accounts = plan["_snapshot"]["students"]
    if any(row["is_active"] for row in accounts):
        raise ValueError("Deactivate the selected accounts before erasure")
    owned = {name: ids for name, ids in plan["_owned"].items() if ids}

    # Complete one real, constraint-checked database erasure inside a
    # rollback-only savepoint BEFORE deleting any S3 object. This prevents a
    # predictable FK, ownership or SQL failure leaving audio missing while
    # its assessment row still exists. No DB changes survive the preview.
    preview = db.begin_nested()
    try:
        _remove_owned_rows(db, metadata, owned)
        if db.get_bind().dialect.name == "postgresql":
            from sqlalchemy import text
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    except BaseException:
        preview.rollback()
        raise
    preview.rollback()

    # Re-run the *identical* database operations after deleting exact scoped
    # object keys. Storage and SQL have no shared transaction; the savepoint
    # eliminates known SQL failures, not arbitrary concurrent infrastructure
    # failures. Keep the accounts inactive until post-delete verification.
    for key in sorted(plan["_audio"]):
        owner = int(key.split("/", 2)[1])
        delete_audio(key, owner)
    _remove_owned_rows(db, metadata, owned)
    db.commit()
    return {**public_plan(plan), "status": "deleted"}


def public_plan(plan):
    return {key: value for key, value in plan.items() if not key.startswith("_")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--student-ids", required=True)
    parser.add_argument("--expected-total", required=True, type=int)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--fingerprint", default="")
    args = parser.parse_args()
    ids = sorted({int(value) for value in args.student_ids.split(",")})
    if not ids or any(value <= 0 for value in ids):
        parser.error("positive explicit student IDs are required")
    from db.database import SessionLocal
    import storage
    def list_audio(student_id):
        paginator = storage.s3_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=storage.S3_BUCKET_NAME, Prefix=f"audio/{student_id}/"):
            for entry in page.get("Contents", []):
                yield entry["Key"]
    with SessionLocal() as db:
        plan = erasure_plan(db, ids, args.expected_total, list_audio=list_audio)
        result = execute_erasure(db, plan, args.fingerprint, storage.delete_superseded_audio) if args.execute else public_plan(plan)
        print("HIMMA_TEST_ACCOUNT_ERASURE " + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
