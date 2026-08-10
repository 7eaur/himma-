"""Comprehensive backend tests — health, auth, permissions, cookies, audit."""

import pytest


# ═══════════════════════════════════════════════════════════════════════
# 1. Health endpoint
# ═══════════════════════════════════════════════════════════════════════

class TestHealth:
    def test_health_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ═══════════════════════════════════════════════════════════════════════
# 2. Researcher authentication
# ═══════════════════════════════════════════════════════════════════════

class TestResearcherAuth:
    def test_login_success(self, client):
        r = client.post("/auth/login", json={
            "username": "researcher1",
            "password": "securepass123",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["role"] == "researcher"
        # Cookie must be set
        assert "access_token" in r.cookies

    def test_login_wrong_password_401(self, client):
        r = client.post("/auth/login", json={
            "username": "researcher1",
            "password": "wrong",
        })
        assert r.status_code == 401

    def test_login_nonexistent_user_401(self, client):
        r = client.post("/auth/login", json={
            "username": "nobody",
            "password": "whatever",
        })
        assert r.status_code == 401

    def test_cookie_httponly_samesite(self, client):
        r = client.post("/auth/login", json={
            "username": "researcher1",
            "password": "securepass123",
        })
        cookie_header = r.headers.get("set-cookie", "")
        assert "httponly" in cookie_header.lower()
        assert "samesite=lax" in cookie_header.lower()


# ═══════════════════════════════════════════════════════════════════════
# 3. Student authentication
# ═══════════════════════════════════════════════════════════════════════

class TestStudentAuth:
    def test_student_login_success(self, client):
        r = client.post("/auth/student-login", json={"access_code": "STU001"})
        assert r.status_code == 200
        assert r.json()["role"] == "student"
        assert "access_token" in r.cookies

    def test_student_login_invalid_code_401(self, client):
        r = client.post("/auth/student-login", json={"access_code": "INVALID"})
        assert r.status_code == 401


# ═══════════════════════════════════════════════════════════════════════
# 4. /auth/me
# ═══════════════════════════════════════════════════════════════════════

class TestMe:
    def test_me_researcher(self, researcher_client):
        r = researcher_client.get("/auth/me")
        assert r.status_code == 200
        body = r.json()
        assert body["role"] == "researcher"
        assert body["display_name"] == "researcher1"

    def test_me_student(self, student_client):
        r = student_client.get("/auth/me")
        assert r.status_code == 200
        body = r.json()
        assert body["role"] == "student"
        assert body["display_name"] == "طالب 1"

    def test_me_unauthenticated_401(self, client):
        r = client.get("/auth/me")
        assert r.status_code == 401


# ═══════════════════════════════════════════════════════════════════════
# 5. Researcher-only endpoints → 200 / 401 / 403
# ═══════════════════════════════════════════════════════════════════════

class TestResearcherProtected:
    def test_dashboard_as_researcher_200(self, researcher_client):
        r = researcher_client.get("/researcher/dashboard")
        assert r.status_code == 200

    def test_dashboard_unauthenticated_401(self, client):
        r = client.get("/researcher/dashboard")
        assert r.status_code == 401

    def test_dashboard_as_student_403(self, student_client):
        r = student_client.get("/researcher/dashboard")
        assert r.status_code == 403

    def test_list_students_as_researcher_200(self, researcher_client):
        r = researcher_client.get("/researcher/students")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_students_as_student_403(self, student_client):
        r = student_client.get("/researcher/students")
        assert r.status_code == 403


# ═══════════════════════════════════════════════════════════════════════
# 6. Student-only endpoints → 200 / 401 / 403
# ═══════════════════════════════════════════════════════════════════════

class TestStudentProtected:
    def test_profile_as_student_200(self, student_client):
        r = student_client.get("/student/profile")
        assert r.status_code == 200
        assert r.json()["name"] == "طالب 1"

    def test_profile_unauthenticated_401(self, client):
        r = client.get("/student/profile")
        assert r.status_code == 401

    def test_profile_as_researcher_403(self, researcher_client):
        r = researcher_client.get("/student/profile")
        assert r.status_code == 403


# ═══════════════════════════════════════════════════════════════════════
# 7. Logout
# ═══════════════════════════════════════════════════════════════════════

class TestLogout:
    def test_logout_clears_cookie(self, researcher_client):
        r = researcher_client.post("/auth/logout")
        assert r.status_code == 200
        # After logout, /auth/me must fail
        r2 = researcher_client.get("/auth/me")
        assert r2.status_code == 401
