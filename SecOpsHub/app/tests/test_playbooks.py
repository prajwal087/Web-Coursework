import json
from app.database import get_db


class TestPlaybooksList:
    def test_list_requires_auth(self, client):
        resp = client.get('/playbooks/', follow_redirects=True)
        assert b'login' in resp.data.lower()

    def test_list_empty(self, client, lead):
        resp = client.get('/playbooks/')
        assert resp.status_code == 200

    def test_list_with_playbooks(self, client, lead, sample_playbook):
        resp = client.get('/playbooks/')
        assert resp.status_code == 200
        assert b'Incident Response' in resp.data


class TestPlaybooksCreate:
    def test_create_playbook(self, client, lead):
        resp = client.post('/playbooks/new', data={
            'name': 'Malware Analysis',
            'description': 'Steps to analyze malware',
            'steps': '["Isolate","Scan","Report"]'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Malware Analysis' in resp.data

    def test_create_playbook_persists(self, client, lead):
        client.post('/playbooks/new', data={
            'name': 'Persistent PB',
            'description': 'Check DB',
            'steps': '["Step 1","Step 2"]'
        }, follow_redirects=True)
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM playbooks WHERE name = 'Persistent PB'")
                row = cur.fetchone()
                assert row is not None
                steps = json.loads(row['steps'])
                assert steps == ['Step 1', 'Step 2']
        finally:
            conn.close()

    def test_create_playbook_empty_name_fails(self, client, lead):
        resp = client.post('/playbooks/new', data={
            'name': '',
            'description': 'test',
            'steps': '[]'
        }, follow_redirects=True)
        assert b'required' in resp.data.lower() or resp.status_code == 400

    def test_create_playbook_with_newline_steps(self, client, lead):
        resp = client.post('/playbooks/new', data={
            'name': 'Newline Steps',
            'description': 'Steps separated by newlines',
            'steps': 'Step A\nStep B\nStep C'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Newline Steps' in resp.data

    def test_create_playbook_handles_invalid_json_steps(self, client, lead):
        resp = client.post('/playbooks/new', data={
            'name': 'Bad JSON',
            'description': 'Fallback to newline split',
            'steps': 'not json at all'
        }, follow_redirects=True)
        assert resp.status_code == 200


class TestPlaybooksView:
    def test_view_playbook(self, client, lead, sample_playbook):
        resp = client.get(f'/playbooks/{sample_playbook}')
        assert resp.status_code == 200
        assert b'Incident Response' in resp.data
        assert b'Identify' in resp.data

    def test_view_nonexistent_playbook(self, client, lead):
        resp = client.get('/playbooks/99999', follow_redirects=True)
        assert b'not found' in resp.data.lower()


class TestPlaybooksEdit:
    def test_edit_playbook(self, client, lead, sample_playbook):
        resp = client.post(f'/playbooks/{sample_playbook}/edit', data={
            'name': 'Updated IR',
            'description': 'Updated description',
            'steps': '["Step 1","Step 2"]'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Updated IR' in resp.data

    def test_edit_playbook_updates_db(self, client, lead, sample_playbook):
        client.post(f'/playbooks/{sample_playbook}/edit', data={
            'name': 'DB Updated PB',
            'description': 'New desc',
            'steps': '["Only step"]'
        }, follow_redirects=True)
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM playbooks WHERE id = %s", (sample_playbook,))
                row = cur.fetchone()
                assert row['name'] == 'DB Updated PB'
                steps = json.loads(row['steps'])
                assert steps == ['Only step']
        finally:
            conn.close()


class TestPlaybooksDelete:
    def test_delete_playbook(self, client, lead, sample_playbook):
        resp = client.post(f'/playbooks/{sample_playbook}/delete', follow_redirects=True)
        assert resp.status_code == 200

    def test_delete_playbook_removes_from_db(self, client, lead, sample_playbook):
        client.post(f'/playbooks/{sample_playbook}/delete', follow_redirects=True)
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM playbooks WHERE id = %s", (sample_playbook,))
                assert cur.fetchone() is None
        finally:
            conn.close()
