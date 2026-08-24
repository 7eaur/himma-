"""conftest.py — shared test fixtures with in-memory SQLite."""

import os
import sys

# Isolate tests from any developer or production database configuration.
# PostgreSQL integration can be requested explicitly with HIMMA_TEST_DATABASE_URL.
os.environ["API_SECRET_KEY"] = "test-only-api-secret-at-least-32-chars"
os.environ["DATABASE_URL"] = os.environ.get(
    "HIMMA_TEST_DATABASE_URL",
    "sqlite:///./.pytest-himma.db",
)
os.environ["S3_ACCESS_KEY"] = "test-only-access-key"
os.environ["S3_SECRET_KEY"] = "test-only-secret-key"

sys.path.insert(0, os.path.dirname(__file__))

import pytest
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from db.models import Base, User, Student
from dependencies import get_db
from main import app

TEST_DATABASE_URL = os.environ.get("DATABASE_URL")
if TEST_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Seed test data before each test."""
    if TEST_DATABASE_URL.startswith("sqlite"):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
    db = TestingSessionLocal()
    if not db.query(User).filter(User.username == "researcher1").first():
        hashed = bcrypt.hashpw(b"test-only-researcher-password", bcrypt.gensalt()).decode("utf-8")
        db.add(User(
            username="researcher1",
            password_hash=hashed,
            role="researcher",
        ))
    if not db.query(Student).filter(Student.access_code == "STU001").first():
        db.add(Student(access_code="STU001", name="طالب 1"))
    db.commit()
    db.close()
    yield
    # Clean up
    if TEST_DATABASE_URL.startswith("sqlite"):
        Base.metadata.drop_all(bind=engine)
    else:
        db = TestingSessionLocal()
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
        db.close()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def researcher_client(client):
    """A TestClient already logged in as researcher."""
    resp = client.post("/auth/login", json={
        "username": "researcher1",
        "password": "test-only-researcher-password",
    })
    assert resp.status_code == 200
    return client


@pytest.fixture
def student_client(client):
    """A TestClient already logged in as student."""
    resp = client.post("/auth/student-login", json={
        "access_code": "STU001",
    })
    assert resp.status_code == 200
    return client
