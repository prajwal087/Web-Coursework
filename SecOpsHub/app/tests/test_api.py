import json


class TestApiCases:
    def test_api_list_cases_requires_auth(self, client):
        resp = client.get('/api/cases')
        assert resp.status_code == 302

    def test_api_list_cases_returns_json(self, client, lead):
        resp = client.get('/api/cases')
        assert resp.status_code == 200
        assert resp.content_type == 'application/json'
        data = json.loads(resp.data)
        assert isinstance(data, list)

    def test_api_list_cases_with_data(self, client, lead, sample_case):
        resp = client.get('/api/cases')
        data = json.loads(resp.data)
        ids = [c['id'] for c in data]
        assert sample_case in ids

    def test_api_get_case(self, client, lead, sample_case):
        resp = client.get(f'/api/cases/{sample_case}')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['id'] == sample_case
        assert data['title'] == 'Test Security Incident'
        assert data['severity'] == 'high'

    def test_api_get_case_not_found(self, client, lead):
        resp = client.get('/api/cases/99999')
        assert resp.status_code == 404
        data = json.loads(resp.data)
        assert 'error' in data

    def test_api_stats(self, client, lead):
        resp = client.get('/api/stats')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'cases' in data
        assert 'analysts' in data

    def test_api_dashboard_stats(self, client, lead):
        resp = client.get('/api/dashboard/stats')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'status_chart' in data
        assert 'severity_chart' in data

    def test_api_analysts(self, client, lead):
        resp = client.get('/api/analysts')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(a['role'] == 'lead' for a in data)


class TestApiCaseDetail:
    def test_api_get_case_json_structure(self, client, lead, sample_case):
        resp = client.get(f'/api/cases/{sample_case}')
        data = json.loads(resp.data)
        for key in ('id', 'title', 'description', 'severity', 'status',
                     'analyst', 'created_at', 'updated_at'):
            assert key in data

    def test_api_get_case_anonymous_rejected(self, client, app):
        from app.database import get_db
        from datetime import datetime, timezone
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO analysts (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                    ('anon_test_user', 'anon@test.com', 'hash', 'analyst')
                )
                cur.execute(
                    "INSERT INTO cases (title, description, severity, analyst_id, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)",
                    ('Anon Case', 'test', 'low', cur.lastrowid, datetime.now(timezone.utc), datetime.now(timezone.utc))
                )
                case_id = cur.lastrowid
            conn.commit()
        finally:
            conn.close()
        resp = client.get(f'/api/cases/{case_id}')
        assert resp.status_code == 302
