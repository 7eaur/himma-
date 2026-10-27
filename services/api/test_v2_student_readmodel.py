"""P09.1-B source-of-truth projections. No V1 counts or child secrets."""
from conftest import TestingSessionLocal
from db.learning_models import LessonSession, StudentJourney
from db.models import AssessmentSession, Student
from v2_content.importer import register_candidate_release


def test_legacy_student_v2_home_is_non_mutating_and_never_claims_v1_rewards(student_client):
    result = student_client.get("/v2/student/home")
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["mode"] == "v2"
    assert data["journey"] is None
    assert data["progress"]["assigned_lessons"] is None
    assert data["progress"]["display_percent"] is None
    assert data["rewards"] == {"state": "not_implemented_v2"}
    assert data["current_action"]["action"] == "start_pretest"
    assert "access_code" not in result.text and "private_answer" not in result.text
    with TestingSessionLocal() as db:
        assert db.query(StudentJourney).count() == 0
        assert db.query(AssessmentSession).count() == 0


def test_active_pretest_home_never_invents_score_or_completed_lesson(student_client):
    response = student_client.post("/v2/assessments/pretest/start")
    assert response.status_code == 200, response.text
    data = student_client.get("/v2/student/home").json()
    assert data["mode"] == "v2"
    assert data["current_action"]["action"] == "assessment"
    assert data["current_action"]["kind"] == "pretest"
    assert data["assessments"]["pretest"]["score_percent"] is None
    assert data["progress"]["completed_lessons"] == 0
    assert data["progress"]["display_percent"] is None
    assert data["progress"]["skipped_by_placement"] == 0
    assert data["journey"]["placement_state"] == "in_progress"
    assert data["journey"]["content_release_version"]


def test_pinned_placement_counts_assigned_and_skipped_not_legacy_activities(student_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(
            student_id=student.id, content_release_id=release.id, current_level=2,
            current_lesson_id="L2-01", placement_state="placed",
        ))
        db.commit()
    result = student_client.get("/v2/student/home")
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["journey"]["current_level"] == 2
    assert data["current_action"]["action"] == "lesson_catalog"
    assert data["progress"]["skipped_by_placement"] > 0
    assert data["progress"]["assigned_lessons"] + data["progress"]["skipped_by_placement"] == 19
    assert data["progress"]["display_percent"] == 0.0
    assert data["progress"]["completed_lessons"] == 0
    assert data["rewards"]["state"] == "not_implemented_v2"
    assert "private_answer" not in result.text and "access_code" not in result.text


def test_progress_ignores_duplicate_completed_sessions_and_pending_review(student_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(
            student_id=student.id, content_release_id=release.id, current_level=1,
            current_lesson_id="L1-03", placement_state="placed",
        ))
        db.flush()
        db.add_all([
            LessonSession(student_id=student.id, content_release_id=release.id, lesson_id="L1-01",
                          status="completed", stage="complete"),
            LessonSession(student_id=student.id, content_release_id=release.id, lesson_id="L1-01",
                          status="completed", stage="complete"),
            LessonSession(student_id=student.id, content_release_id=release.id, lesson_id="L1-03",
                          status="waiting_review", stage="waiting_review"),
        ])
        db.commit()
    data = student_client.get("/v2/student/home").json()
    assert data["progress"]["completed_lessons"] == 1
    assert data["progress"]["assigned_lessons"] == 19
    assert data["progress"]["pending_review"] == 1
    assert data["progress"]["display_percent"] == round(100 / 19, 1)
    assert data["current_action"]["action"] == "lesson"
    assert data["current_action"]["state"] == "waiting_review"


def test_home_permissions_and_supervisor_projection_are_scoped(student_client, researcher_client):
    # researcher_client and student_client may be the same TestClient fixture:
    # authenticate anew before each role assertion if cookie state changes.
    from db.models import Student
    with TestingSessionLocal() as db:
        original = db.query(Student).filter(Student.access_code == "STU001").one()
        student_id = original.id
        db.add(Student(access_code="STU002", name="طالب 2", current_level=1))
        db.commit()
    assert researcher_client.get("/v2/student/home").status_code == 403
    result = researcher_client.get(f"/v2/student/admin/students/{student_id}/home")
    assert result.status_code == 200, result.text
    assert result.json()["student"]["id"] == student_id
    assert "STU001" not in result.text and "private_answer" not in result.text
    assert researcher_client.get("/v2/student/admin/students/999999/home").status_code == 404
    assert researcher_client.get("/v2/student/admin/students/999999/home").json()["detail"] == "الطالب غير موجود"


def test_student_is_forbidden_from_supervisor_v2_home(student_client):
    assert student_client.get("/v2/student/admin/students/1/home").status_code == 403


def test_unapproved_old_score_not_returned_in_v2_home(student_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(student_id=student.id, content_release_id=release.id,
                              current_level=1, current_lesson_id="L1-01", placement_state="placed"))
        db.add(AssessmentSession(
            student_id=student.id, content_release_id=release.id,
            session_type="pretest", status="completed", v2_state="completed",
            final_score=99, official_for_reporting=False, assessment_attempt_no=1,
        ))
        db.commit()
    result = student_client.get("/v2/student/home")
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["assessments"]["pretest"] is None
    assert "99.0" not in result.text


def test_large_assessment_history_selects_old_official_attempt_without_loading_fallbacks(student_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(AssessmentSession(
            student_id=student.id, content_release_id=release.id,
            session_type="pretest", status="completed", v2_state="completed",
            final_score=77, official_for_reporting=True, assessment_attempt_no=1,
        ))
        db.add_all([
            AssessmentSession(
                student_id=student.id, content_release_id=release.id,
                session_type="pretest", status="completed", v2_state="completed",
                final_score=99, official_for_reporting=False, assessment_attempt_no=attempt,
            )
            for attempt in range(2, 122)
        ])
        db.commit()
    result = student_client.get("/v2/student/home")
    assert result.status_code == 200, result.text
    assert result.json()["assessments"]["pretest"]["score_percent"] == 77.0
    assert "99.0" not in result.text


def test_v2_home_fails_closed_when_frozen_bank_checksum_mismatches(student_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(
            student_id=student.id, content_release_id=release.id,
            current_level=2, current_lesson_id="L2-01", placement_state="placed",
        ))
        release.checksum = "0" * 64
        db.commit()
    result = student_client.get("/v2/student/home")
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["mode"] == "v2"
    assert data["data_status"] == "partial"
    assert data["progress"]["assigned_lessons"] is None
    assert data["progress"]["display_percent"] is None
    assert data["rewards"] == {"state": "not_implemented_v2"}



def test_v1_pretest_history_requires_supervisor_migration_without_mutation(student_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        db.add(AssessmentSession(
            student_id=student.id, session_type="pretest", status="completed",
            assessment_attempt_no=1, v2_state=None, official_for_reporting=False,
        ))
        db.commit()
    result = student_client.get("/v2/student/home")
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["mode"] == "v2"
    assert data["journey"] is None
    assert data["current_action"]["action"] == "migration_review"
    assert data["progress"]["display_percent"] is None
    assert data["assessments"]["pretest"] is None
    assert "access_code" not in result.text and "private_answer" not in result.text
    assert student_client.post("/v2/assessments/pretest/start").status_code == 409
    with TestingSessionLocal() as db:
        assert db.query(StudentJourney).count() == 0
        assert db.query(AssessmentSession).count() == 1

def test_supervisor_v2_cohort_paginates_without_exposing_codes_or_v1_progress(researcher_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        student.name = "طالب الاختبار"
        db.add(Student(name="طالب ثاني", access_code="STU099", current_level=3, is_active=False))
        db.commit()
    result = researcher_client.get("/v2/student/admin/students/overview?limit=1&offset=0")
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["source"] == "himma_v2_readmodel"
    assert data["total"] == 2
    assert len(data["items"]) == 1
    assert data["items"][0]["full_name"] == "طالب ثاني"
    assert data["items"][0]["journey"] is None
    assert data["items"][0]["progress"]["display_percent"] is None
    assert data["items"][0]["status"] == "inactive"
    assert "access_code" not in result.text
    assert "STU099" not in result.text
    assert "core_completed_items" not in result.text
    second = researcher_client.get("/v2/student/admin/students/overview?limit=1&offset=1")
    assert second.status_code == 200
    assert second.json()["items"][0]["full_name"] == "طالب الاختبار"
    query = researcher_client.get("/v2/student/admin/students/overview?search=%D8%AB%D8%A7%D9%86%D9%8A&status=inactive")
    assert query.status_code == 200
    assert query.json()["total"] == 1
    assert query.json()["items"][0]["full_name"] == "طالب ثاني"


def test_student_cannot_see_staff_cohort_or_credentials(student_client):
    assert student_client.get("/v2/student/admin/students/overview").status_code == 403

def test_supervisor_v2_lesson_timeline_obeys_pinned_placement_and_review(researcher_client):
    from db.learning_models import LessonSession
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(
            student_id=student.id, content_release_id=release.id, current_level=2,
            current_lesson_id="L2-02", placement_state="placed",
        ))
        db.flush()
        db.add(LessonSession(student_id=student.id, content_release_id=release.id, lesson_id="L2-01",
                             status="completed", stage="complete"))
        db.add(LessonSession(student_id=student.id, content_release_id=release.id, lesson_id="L2-02",
                             status="waiting_review", stage="waiting_review"))
        db.commit()
        student_id = student.id
    response = researcher_client.get(f"/v2/student/admin/students/{student_id}/home")
    assert response.status_code == 200, response.text
    data = response.json()
    detail = data["lesson_overview"]
    assert detail["state"] == "ready"
    assert len(detail["items"]) == 19
    assert all(set(row) == {"lesson_id", "title", "level", "state", "session_id"} for row in detail["items"])
    states = {row["lesson_id"]: row["state"] for row in detail["items"]}
    assert states["L1-01"] == "skipped"
    assert states["L2-01"] == "completed"
    assert states["L2-02"] == "waiting_review"
    assert data["progress"]["completed_lessons"] == sum(row["state"] == "completed" for row in detail["items"])
    assert data["progress"]["skipped_by_placement"] == sum(row["state"] == "skipped" for row in detail["items"])
    assert "private_answer" not in response.text and "access_code" not in response.text



def test_student_created_by_supervisor_starts_first_v2_pretest_without_legacy_session(researcher_client):
    created = researcher_client.post('/researcher/students', json={
        'full_name': 'طالب اصطناعي جديد W1', 'grade_level': 3,
    })
    assert created.status_code == 201, created.text
    student = created.json()
    with TestingSessionLocal() as db:
        assert db.query(AssessmentSession).filter(AssessmentSession.student_id == student['id']).count() == 0
        assert db.query(StudentJourney).filter(StudentJourney.student_id == student['id']).count() == 0
    signed_in = researcher_client.post('/auth/student-login', json={'access_code': student['access_code']})
    assert signed_in.status_code == 200
    for _ in range(2):
        home = researcher_client.get('/v2/student/home')
        assert home.status_code == 200
        assert home.json()['current_action']['action'] == 'start_pretest'
        assert 'onboarding_review' not in home.json()
    started = researcher_client.post('/v2/assessments/pretest/start')
    assert started.status_code == 200, started.text
    assert started.json()['interaction']['progress']['index'] == 1
    resumed = researcher_client.post('/v2/assessments/pretest/start')
    assert resumed.json()['session']['session_id'] == started.json()['session']['session_id']
    with TestingSessionLocal() as db:
        assert db.query(AssessmentSession).filter(AssessmentSession.student_id == student['id']).count() == 1


def test_migration_blocker_has_staff_only_session_evidence_without_credentials(researcher_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == 'STU001').one()
        student_id = student.id
        db.add(AssessmentSession(student_id=student_id, session_type='pretest', status='in_progress', elapsed_seconds=1))
        db.commit()
    result = researcher_client.get(f'/v2/student/admin/students/{student_id}/home')
    assert result.status_code == 200
    blocker = result.json()['onboarding_review']
    assert len(blocker) == 1
    assert blocker[0]['version'] == 'v1'
    assert blocker[0]['status'] == 'in_progress'
    assert blocker[0]['saved_attempts'] == 0
    assert blocker[0]['official'] is False
    assert 'access_code' not in result.text and 'storage_key' not in result.text
    with TestingSessionLocal() as db:
        assert db.query(AssessmentSession).count() == 1
        assert db.query(StudentJourney).count() == 0


def test_supervisor_dashboard_is_v2_only_without_credentials_or_pagination_counts(researcher_client):
    with TestingSessionLocal() as db:
        release = register_candidate_release(db)
        student = db.query(Student).one()
        db.add(StudentJourney(student_id=student.id, content_release_id=release.id,
                              placement_state='placed', current_level=1, current_lesson_id='L1-01'))
        db.add_all([Student(name=f'اصطناعي {i}', access_code=f'OVW{i:03}', is_active=False) for i in range(7)])
        db.commit()
    result = researcher_client.get('/v2/student/admin/overview')
    assert result.status_code == 200, result.text
    data = result.json()
    assert data['source'] == 'himma_v2_readmodel'
    assert data['counts']['students'] == 8 and len(data['recent_students']) == 6
    assert data['counts']['active_accounts'] == data['counts']['learning'] == 1
    assert data['counts']['assessment_reviews'] == data['counts']['placements'] == 0
    for forbidden in ('access_code', 'core_completed_items', 'private_answer', 'storage_key'):
        assert forbidden not in result.text


def test_student_cannot_read_supervisor_dashboard(student_client):
    assert student_client.get('/v2/student/admin/overview').status_code == 403


def test_progress_keeps_completed_lower_level_lessons_after_advancing(researcher_client):
    from db.learning_models import PlacementDecisionV2
    from db.models import User
    with TestingSessionLocal() as db:
        release = register_candidate_release(db)
        student = db.query(Student).one()
        user = db.query(User).one()
        pretest = AssessmentSession(student_id=student.id, session_type='pretest', status='completed',
                                    v2_state='completed', content_release_id=release.id, official_for_reporting=True)
        db.add(pretest)
        db.flush()
        db.add(PlacementDecisionV2(student_id=student.id, assessment_session_id=pretest.id,
            content_release_id=release.id, assigned_level=1, reason='تسكين اصطناعي واضح',
            policy_version='test', decided_by=user.id))
        db.add(StudentJourney(student_id=student.id, content_release_id=release.id,
                              placement_state='placed', current_level=2, current_lesson_id='L2-01'))
        db.add_all([LessonSession(student_id=student.id, content_release_id=release.id,
            lesson_id=f'L1-{i:02}', stage='complete', status='completed') for i in range(1, 7)])
        db.commit()
        student_id = student.id
    data = researcher_client.get(f'/v2/student/admin/students/{student_id}/home').json()
    assert data['progress']['assigned_lessons'] == 19
    assert data['progress']['completed_lessons'] == 6
    assert data['progress']['skipped_by_placement'] == 0
    assert data['progress']['display_percent'] == round(600 / 19, 1)
    assert all(row['state'] == 'completed' for row in data['lesson_overview']['items'][:6])
