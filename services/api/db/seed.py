"""Idempotent seed script — relies on Alembic migrations for schema."""

import os
import sys
import bcrypt

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.database import SessionLocal
from db.models import User, Student


def seed():
    """Seed admin researcher and 15 test students.

    IMPORTANT: Tables must already exist via `alembic upgrade head`.
    This script does NOT call Base.metadata.create_all().
    """
    db = SessionLocal()

    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        raise RuntimeError(
            "ADMIN_PASSWORD environment variable is required for seeding. "
            "Do not commit a default password."
        )
    if not db.query(User).filter(User.username == "admin").first():
        hashed = bcrypt.hashpw(admin_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        db.add(User(username="admin", password_hash=hashed, role="researcher"))

    for i in range(1, 16):
        code = f"STU{i:03d}"
        if not db.query(Student).filter(Student.access_code == code).first():
            db.add(Student(access_code=code, name=f"طالب {i}"))

    db.commit()
    db.close()
    print("Seeding completed successfully.")


if __name__ == "__main__":
    seed()
