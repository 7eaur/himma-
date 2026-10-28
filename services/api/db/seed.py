"""Idempotent seed script — relies on Alembic migrations for schema."""

import os
import sys
import bcrypt

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.database import SessionLocal
from db.models import User


def seed():
    """Seed the initial supervisor account.

    IMPORTANT: Tables must already exist via `alembic upgrade head`.
    This script does NOT call Base.metadata.create_all().
    """
    db = SessionLocal()

    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        raise RuntimeError(
            "ADMIN_PASSWORD environment variable is required for seeding. "
            "Do not commit a default password."
        )

    admin_user = db.query(User).filter(User.username == admin_username).first()
    if not admin_user:
        hashed = bcrypt.hashpw(admin_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        db.add(User(username=admin_username, password_hash=hashed, role="researcher"))
    elif os.getenv("RESET_ADMIN_PASSWORD_ON_SEED", "false").lower() == "true":
        admin_user.password_hash = bcrypt.hashpw(
            admin_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        print("Admin password reset applied by explicit seed flag.")

    db.commit()
    db.close()
    print("Seeding completed successfully.")


if __name__ == "__main__":
    seed()
