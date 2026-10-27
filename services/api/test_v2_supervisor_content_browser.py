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
    assert len(inventory.json()['items']) == 89
    for kind in ('audio', 'image', 'video'):
        asset = next(asset for asset in get_release()['media'] if asset['kind'] == kind)
        response = researcher_client.get(f'/v2/lessons/admin/media/{asset["id"]}')
        assert response.status_code == 200, response.text[:100]
        assert response.headers['cache-control'] == 'private, no-store'
        assert response.headers['x-himma-test-only'] == 'true'
        assert response.headers['content-type'].startswith(kind + '/')
        assert response.content
    assert researcher_client.get('/v2/lessons/admin/media/no-such-asset').status_code == 404


def test_production_preview_never_serves_unapproved_fixture_to_staff(researcher_client, monkeypatch):
    monkeypatch.setenv('ENV', 'production')
    monkeypatch.setenv('V2_FIXTURE_MEDIA_ENABLED', 'false')
    response = researcher_client.get('/v2/lessons/admin/media/VID-L1-01')
    assert response.status_code == 404
