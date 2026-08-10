"""conftest.py — shared test fixtures with in-memory SQLite."""

import os
import sys

# Set test secrets BEFORE importing anything that reads them
if "API_SECRET_KEY" not in os.environ:
    os.environ["API_SECRET_KEY"] = "test-secret-key-for-ci-only"
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"

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
        Base.metadata.create_all(bind=engine)
        
    db = TestingSessionLocal()
    if not db.query(User).filter(User.username == "researcher1").first():
        hashed = bcrypt.hashpw(b"securepass123", bcrypt.gensalt()).decode("utf-8")
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
    return TestClient(app)


@pytest.fixture
def researcher_client(client):
    """A TestClient already logged in as researcher."""
    resp = client.post("/auth/login", json={
        "username": "researcher1",
        "password": "securepass123",
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
