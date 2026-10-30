"""Read-only staff bank/media preview never shares answer keys with a learner."""
from v2_content.repository import get_release


def test_bank_requires_staff_and_is_read_only(student_client):
    assert student_client.get('/v2/content/admin/bank').status_code == 403
    assert student_client.post('/v2/content/admin/bank', json={}).status_code == 405
    assert student_client.get('/v2/lessons/admin/media/LET-02').status_code == 403


def test_all_300_questions_are_sequenced_once_with_current_six_interactions(researcher_client):
    rows = []
    for offset in range(0, 300, 50):
        response = researcher_client.get(f'/v2/content/admin/bank?limit=50&offset={offset}')
        assert response.status_code == 200, response.text
        data = response.json()
        assert data['mode'] == 'read_only' and data['bank_total'] == data['total'] == 300
        assert len(data['sections']) == 33
        assert sum(section['question_count'] for section in data['sections']) == 300
        assert len(data['items']) == 50
        rows.extend(data['items'])
    ids = [row['question']['question_id'] for row in rows]
    assert len(set(ids)) == 300
    assert ids[0] == 'V2-PRE-Q01' and ids[-1] == 'V2-POST-Q30'
    assert {row['question']['interaction'] for row in rows} == {
        'choose_one', 'listen_choose_one', 'sequence', 'build_word', 'choose_image', 'read_aloud',
    }
    assert all(isinstance(row['answer'], dict) for row in rows)


def test_lesson_bank_includes_intro_and_uses_staff_media_urls(researcher_client):
    response = researcher_client.get('/v2/content/admin/bank?section=L1-01')
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 8
    assert next(section for section in data['sections'] if section['id'] == 'L1-01')['intro']['text']
    assert [row['question']['role'] for row in data['items']] == ['guided_practice'] * 4 + ['independent_check'] * 4
    urls = [asset['url'] for row in data['items'] for asset in row['media'] if asset['url']]
    assert urls and all(url.startswith('/api/v2/lessons/admin/media/') for url in urls)
    assert researcher_client.get('/v2/content/admin/bank?section=unknown').status_code == 404
    assert researcher_client.get('/v2/content/admin/bank?search=nonexistent-search').json()['items'] == []


def test_inventory_and_preview_are_staff_only_private_and_test_marked(researcher_client):
    inventory = researcher_client.get('/v2/lessons/admin/media-inventory')
    assert inventory.status_code == 200
    assert len(inventory.json()['items']) == 87
    for kind in ('audio', 'image', 'video'):
        asset = next(asset for asset in get_release()['media'] if asset['kind'] == kind)
        response = researcher_client.get(f'/v2/lessons/admin/media/{asset["id"]}')
        assert response.status_code == 200, response.text[:100]
        assert response.headers['cache-control'] == 'private, no-store'
        assert response.headers['x-himma-test-only'] == 'false'
        assert response.headers['content-type'].startswith(kind + '/')
        assert response.content
    assert researcher_client.get('/v2/lessons/admin/media/no-such-asset').status_code == 404


def test_production_preview_never_serves_unapproved_fixture_to_staff(researcher_client, monkeypatch):
    monkeypatch.setenv('ENV', 'production')
    monkeypatch.setenv('V2_FIXTURE_MEDIA_ENABLED', 'false')
    response = researcher_client.get('/v2/lessons/admin/media/VID-L1-01')
    assert response.status_code == 200
    assert response.headers['x-himma-test-only'] == 'false'
    assert researcher_client.get('/v2/lessons/admin/media/AUD-L1-03-MA').status_code == 404


def test_private_review_workbook_matches_current_compiled_questions_without_static_stale_copy(researcher_client):
    from io import BytesIO
    import json
    from openpyxl import load_workbook
    from conftest import TestingSessionLocal
    from db.models import AuditLog

    release = get_release()
    response = researcher_client.get("/v2/content/admin/review-export.xlsx")
    assert response.status_code == 200, response.text[:200]
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    workbook = load_workbook(BytesIO(response.content))
    sheet = workbook["الأسئلة المعتمدة"]
    exported = {row[3]: row for row in list(sheet.values)[1:]}
    assert len(exported) == len(release["questions"]) == 300
    assert set(exported) == {question["id"] for question in release["questions"]}
    for question in release["questions"]:
        row = exported[question["id"]]
        assert row[8] == question["prompt"]
        assert row[4] == question["role"]
        assert row[5] == question["interaction"]
        assert row[6] == question["skill_group"]
        assert json.loads(row[10]) == question["options"]
        expected = [
            {"id": option_id, "text": next(
                (opt.get("text") or json.dumps(opt.get("media", []),
                                                ensure_ascii=False, sort_keys=True, separators=(",", ":")))
                for opt in question["options"] if opt["id"] == option_id
            )}
            for option_id in question["private_answer"].get("correct_option_ids", [])
        ]
        assert json.loads(row[11]) == expected
    assert len(list(workbook["الأقسام والأهداف"].values)) - 1 == 33
    meta = {row[0]: row[1] for row in workbook["معلومات المراجعة"].values}
    assert meta["البصمة"] == release["checksum"]
    assert meta["عدد الأسئلة"] == 300
    with TestingSessionLocal() as db:
        assert db.query(AuditLog).filter(AuditLog.action == "v2.content.review_exported").count() == 1


def test_private_content_answers_cannot_be_downloaded_by_child_and_never_cached(researcher_client, student_client):
    assert researcher_client.post("/auth/login", json={
        "username": "researcher1", "password": "test-only-researcher-password",
    }).status_code == 200
    bank = researcher_client.get("/v2/content/admin/bank?section=L1-01")
    assert bank.status_code == 200
    assert bank.headers["cache-control"] == "private, no-store"
    assert bank.headers["x-content-type-options"] == "nosniff"
    assert student_client.post("/auth/student-login", json={"access_code": "STU001"}).status_code == 200
    assert student_client.get("/v2/content/admin/review-export.xlsx").status_code == 403
    assert student_client.get("/v2/content/admin/bank").status_code == 403


def test_staff_bank_searches_visible_stimulus_and_options_but_not_private_answers(researcher_client, monkeypatch):
    from copy import deepcopy
    from urllib.parse import urlencode
    import v2_content_api

    release = deepcopy(get_release())
    question = next(row for row in release["questions"] if row["options"] and row.get("stimulus") is not None)
    marker = "REVIEW-PRIVATE-NO-SEARCH-872"
    question["private_answer"]["review_hidden_marker"] = marker
    question["stimulus"]["text"] = "اختبار حروف ظاهرة فريد 872"
    question["options"][0]["text"] = "خيار ظاهر فريد 872"
    monkeypatch.setattr(v2_content_api, "get_release", lambda: release)
    section = question.get("owner_id") or question["role"]
    for term in ("اختبار حروف ظاهرة فريد 872", "خيار ظاهر فريد 872"):
        query = urlencode({"section": section, "search": term})
        response = researcher_client.get(f"/v2/content/admin/bank?{query}")
        assert response.status_code == 200, response.text
        assert question["id"] in [item["question"]["question_id"] for item in response.json()["items"]]
    hidden = researcher_client.get("/v2/content/admin/bank?search=" + marker)
    assert hidden.status_code == 200
    assert hidden.json()["total"] == 0
