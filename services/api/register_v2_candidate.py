"""Register the deterministic V2 candidate release; never activates/publishes it."""

import argparse
import json

from v2_content.compiler import compile_release


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="register the candidate in the configured database")
    args = parser.parse_args()
    release = compile_release()
    result = {"mode": "dry-run", "version": release["version"], "checksum": release["checksum"], "counts": release["counts"]}
    if args.write:
        from db.database import SessionLocal
        from v2_content.importer import register_candidate_release

        with SessionLocal() as db:
            row = register_candidate_release(db, release)
            db.commit()
            result.update({"mode": "registered", "database_id": row.id, "status": row.status, "is_active": row.is_active})
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
