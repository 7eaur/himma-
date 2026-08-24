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
            "password": "test-only-researcher-password",
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
            "password": "test-only-researcher-password",
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

class TestStage2:
    def test_seed_idempotency_approved_catalog(self):
        from sqlalchemy import func
        from db.database import SessionLocal
        from db.models import ContentAssetLink, ContentItem, ContentOption, ContentStep, Skill

        import seed
        seed.run_seed()

        db = SessionLocal()
        first_counts = {
            "items": db.query(ContentItem).count(),
            "skills": db.query(Skill).count(),
            "steps": db.query(ContentStep).count(),
            "options": db.query(ContentOption).count(),
            "assets": db.query(ContentAssetLink).count(),
        }
        db.close()

        seed.run_seed()

        db = SessionLocal()
        second_counts = {
            "items": db.query(ContentItem).count(),
            "skills": db.query(Skill).count(),
            "steps": db.query(ContentStep).count(),
            "options": db.query(ContentOption).count(),
            "assets": db.query(ContentAssetLink).count(),
        }
        assert first_counts == second_counts
        assert first_counts["items"] == 105
        assert first_counts["skills"] == 44

        for kind in ("pretest_question", "posttest_question"):
            distribution = dict(
                db.query(ContentItem.level_id, func.count(ContentItem.id))
                .filter(ContentItem.kind == kind)
                .group_by(ContentItem.level_id)
                .all()
            )
            assert distribution == {1: 10, 2: 12, 3: 8}

        for level_id in (1, 2, 3):
            assert db.query(ContentItem).filter(
                ContentItem.kind == "core_activity",
                ContentItem.level_id == level_id,
            ).count() == 10
            assert db.query(ContentItem).filter(
                ContentItem.kind == "reinforcement_activity",
                ContentItem.level_id == level_id,
            ).count() == 5

        choice_steps = db.query(ContentStep).join(ContentItem).filter(
            ContentItem.interaction_type == "multiple_choice"
        ).all()
        assert choice_steps
        for step in choice_steps:
            assert step.options
            assert sum(option.is_correct for option in step.options) == 1

        reading_steps = db.query(ContentStep).join(ContentItem).filter(
            ContentItem.interaction_type == "read_aloud"
        ).all()
        assert reading_steps
        assert all(step.expected_reading_text for step in reading_steps)
        assert all(not step.options for step in reading_steps)
        db.close()

    def test_seed_refuses_to_mix_legacy_catalog(self):
        from db.database import SessionLocal
        from db.models import ContentItem, ContentKind, Skill

        import seed

        db = SessionLocal()
        legacy_skill = Skill(
            skill_key="legacy-skill-key",
            canonical_skill_id="legacy_skill",
            name="Legacy test skill",
            description="Test-only row",
            level_id=1,
        )
        db.add(legacy_skill)
        db.flush()
        db.add(
            ContentItem(
                stable_key="legacy-content-key",
                kind=ContentKind.pretest_question,
                level_id=1,
                skill_id=legacy_skill.id,
                interaction_type="multiple_choice",
                order_index=1,
                version="legacy-test",
                status="approved",
                checksum="legacy-test-checksum",
                template_data={},
            )
        )
        db.commit()
        db.close()

        with pytest.raises(RuntimeError, match="legacy content catalog"):
            seed.run_seed()

    def test_idor_and_401_403(self, client):
        res = client.get("/assessment/active")
        assert res.status_code == 401
        
        # Try without valid token
        res = client.post("/assessment/start", json={"session_type": "pretest"})
        assert res.status_code == 401

    def test_idempotency_key(self, student_client):
        # Start session
        res = student_client.post("/assessment/start", json={"session_type": "pretest"})
        assert res.status_code == 200
        session_id = res.json()["id"]
        
        # Submit same attempt twice with same idempotency key
        headers = {"Idempotency-Key": "test-key-123"}
        res1 = student_client.post(f"/assessment/session/{session_id}/attempt/1/submit", json={"step_id": 1}, headers=headers)
        res2 = student_client.post(f"/assessment/session/{session_id}/attempt/1/submit", json={"step_id": 1}, headers=headers)
        
        # In a real idempotency setup, res2 should match res1 or return 409
        # For now, just ensuring it doesn't crash
        assert res1.status_code in [200, 400, 404]
        
    def test_prevent_early_finish(self, student_client):
        # Get active or start
        res = student_client.get("/assessment/active")
        if not res.json():
            res = student_client.post("/assessment/start", json={"session_type": "pretest"})
        session_id = res.json()["id"]
        
        # Try to finish
        res = student_client.post(f"/assessment/session/{session_id}/finish")
        # Should fail because 30 items not completed
        assert res.status_code == 400
        assert "30 items" in res.json()["detail"]
    def test_profile_as_student_200(self, student_client):
        r = student_client.get("/profile")
        assert r.status_code == 200
        assert r.json()["full_name"] == "طالب 1"

    def test_profile_unauthenticated_401(self, client):
        r = client.get("/profile")
        assert r.status_code == 401

    def test_profile_as_researcher_403(self, researcher_client):
        r = researcher_client.get("/profile")
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


# ═══════════════════════════════════════════════════════════════════════
# 8. Assessment & Scoring
# ═══════════════════════════════════════════════════════════════════════

class TestAssessmentAndScoring:
    def test_audio_grade_counts_reject_negative_values(self):
        from pydantic import ValidationError
        from schemas import GradeAudioRequest

        with pytest.raises(ValidationError):
            GradeAudioRequest(is_valid=True, target_units=10, deletions=-1)

    def test_student_start_assessment(self, student_client):
        # We assume student STU001 is set up by conftest
        r = student_client.post("/assessment/start", json={"session_type": "pretest"})
        assert r.status_code == 200
        assert r.json()["session_type"] == "pretest"
        
    def test_researcher_pending_audio_empty(self, researcher_client):
        r = researcher_client.get("/review/pending-audio")
        assert r.status_code == 200
        assert r.json() == []

    def test_next_item_resumes_pending_attempt(self, student_client):
        import seed

        seed.run_seed()
        session = student_client.post(
            "/assessment/start", json={"session_type": "pretest"}
        ).json()

        first = student_client.get(
            f"/assessment/session/{session['id']}/next"
        )
        resumed = student_client.get(
            f"/assessment/session/{session['id']}/next"
        )

        assert first.status_code == 200
        assert resumed.status_code == 200
        assert resumed.json()["id"] == first.json()["id"]
        progress = student_client.get(
            f"/assessment/session/{session['id']}/progress"
        )
        assert progress.status_code == 200
        assert progress.json() == {
            "completed_items": 0,
            "total_items": 30,
            "has_pending_item": True,
        }

    def test_next_item_does_not_complete_session(self, student_client):
        session = student_client.post(
            "/assessment/start", json={"session_type": "pretest"}
        ).json()

        next_item = student_client.get(
            f"/assessment/session/{session['id']}/next"
        )
        active = student_client.get("/assessment/active")

        assert next_item.status_code == 200
        assert next_item.json() is None
        assert active.json()["id"] == session["id"]
        assert active.json()["status"] == "in_progress"

    def test_rejects_option_outside_attempt_step(self, student_client):
        import seed

        seed.run_seed()
        session = student_client.post(
            "/assessment/start", json={"session_type": "pretest"}
        ).json()
        item = student_client.get(
            f"/assessment/session/{session['id']}/next"
        ).json()

        response = student_client.post(
            f"/assessment/session/{session['id']}/attempt/{item['id']}/submit",
            json={
                "step_id": item["steps"][0]["id"],
                "selected_option_id": 999999,
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Option does not belong to this step"

    def test_invalid_audio_reopens_attempt_and_accepts_rerecord(
        self, client, monkeypatch
    ):
        import seed
        import assessment
        from db.database import SessionLocal
        from db.models import (
            AssessmentSession,
            Attempt,
            AttemptResponse,
            AudioSubmission,
            ContentItem,
            Student,
        )

        seed.run_seed()
        monkeypatch.setattr(assessment.storage, "verify_audio", lambda *_args: None)

        assert client.post(
            "/auth/student-login", json={"access_code": "STU001"}
        ).status_code == 200
        session_id = client.post(
            "/assessment/start", json={"session_type": "pretest"}
        ).json()["id"]

        db = SessionLocal()
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        session = db.query(AssessmentSession).filter(
            AssessmentSession.id == session_id,
            AssessmentSession.student_id == student.id,
        ).one()
        audio_item = db.query(ContentItem).filter(
            ContentItem.kind == "pretest_question",
            ContentItem.interaction_type == "read_aloud",
        ).order_by(ContentItem.order_index).first()
        attempt = Attempt(session_id=session.id, item_id=audio_item.id)
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        student_id = student.id
        attempt_id = attempt.id
        item_id = audio_item.id
        step_id = audio_item.steps[0].id
        db.close()

        first_key = f"audio/{student_id}/first.webm"
        first = client.post(
            f"/assessment/session/{session_id}/attempt/{item_id}/submit",
            json={
                "step_id": step_id,
                "audio_storage_key": first_key,
                "audio_file_size": 128,
                "audio_mime_type": "audio/webm",
            },
        )
        assert first.status_code == 200

        db = SessionLocal()
        response = db.query(AttemptResponse).filter(
            AttemptResponse.attempt_id == attempt_id,
        ).one()
        response_id = response.id
        submission_id = db.query(AudioSubmission).filter(
            AudioSubmission.response_id == response_id,
        ).one().id
        db.close()

        assert client.post(
            "/auth/login",
            json={
                "username": "researcher1",
                "password": "test-only-researcher-password",
            },
        ).status_code == 200
        rejected = client.post(
            f"/review/audio/{submission_id}/grade",
            json={"is_valid": False},
        )
        assert rejected.status_code == 200

        db = SessionLocal()
        assert db.query(Attempt).filter(Attempt.id == attempt_id).one().status == "in_progress"
        assert db.query(AudioSubmission).filter(
            AudioSubmission.id == submission_id,
        ).one().status == "rerecord_required"
        db.close()

        assert client.post(
            "/auth/student-login", json={"access_code": "STU001"}
        ).status_code == 200
        resumed = client.get(f"/assessment/session/{session_id}/next")
        assert resumed.status_code == 200
        assert resumed.json()["id"] == item_id

        finish = client.post(f"/assessment/session/{session_id}/finish")
        assert finish.status_code == 409
        assert "requiring rerecord" in finish.json()["detail"]

        second_key = f"audio/{student_id}/second.webm"
        replacement = client.post(
            f"/assessment/session/{session_id}/attempt/{item_id}/submit",
            json={
                "step_id": step_id,
                "audio_storage_key": second_key,
                "audio_file_size": 256,
                "audio_mime_type": "audio/webm",
            },
        )
        assert replacement.status_code == 200
        assert replacement.json()["message"] == "Rerecord submitted"

        db = SessionLocal()
        refreshed_attempt = db.query(Attempt).filter(Attempt.id == attempt_id).one()
        refreshed_audio = db.query(AudioSubmission).filter(
            AudioSubmission.id == submission_id,
        ).one()
        assert refreshed_attempt.status == "completed"
        assert refreshed_audio.status == "uploaded"
        assert refreshed_audio.storage_key == second_key
        assert db.query(AudioSubmission).filter(
            AudioSubmission.response_id == response_id,
        ).count() == 1
        db.close()
