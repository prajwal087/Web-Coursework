import time


def _register_lead(client):
    """Register and login as a lead user for testing."""
    import random
    ts = str(int(time.time() * 1000))[-6:]
    uname = f'lead_{ts}'
    email = f'{uname}@test.com'
    client.post('/auth/register', data={
        'username': uname,
        'email': email,
        'password': 'StrongPass123!'
    })
    resp = client.post('/auth/login', data={
        'username': uname,
        'password': 'StrongPass123!'
    }, follow_redirects=True)
    return resp


def _make_lead(client):
    """Create a lead user directly in DB to bypass rate limits."""
    import bcrypt
    import random
    from app.database import get_db
    ts = str(int(time.time() * 1000))[-6:]
    uname = f'lead_{ts}'
    email = f'{uname}@test.com'
    pw_hash = bcrypt.hashpw(b'StrongPass123!', bcrypt.gensalt()).decode()
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO analysts (username, email, password_hash, role) VALUES (%s, %s, %s, 'lead')",
                (uname, email, pw_hash)
            )
        conn.commit()
    finally:
        conn.close()
    client.post('/auth/login', data={
        'username': uname,
        'password': 'StrongPass123!'
    }, follow_redirects=True)
    return uname


class TestEdgeCases:
    def test_create_case_empty_title_fails(self, client):
        _make_lead(client)
        resp = client.post('/cases/new', data={
            'title': '',
            'description': 'test',
            'severity': 'low'
        }, follow_redirects=True)
        assert b'required' in resp.data.lower() or resp.status_code == 400

    def test_create_case_invalid_severity_rejected(self, client):
        _make_lead(client)
        resp = client.post('/cases/new', data={
            'title': 'Test case',
            'description': 'test',
            'severity': 'ultra-critical'
        }, follow_redirects=True)
        assert resp.status_code in (200, 400)
        assert b'invalid' in resp.data.lower() or resp.status_code == 400

    def test_create_analyst_weak_password_rejected(self, client):
        _make_lead(client)
        resp = client.post('/analysts/new', data={
            'username': 'hacker',
            'email': 'hacker@evil.com',
            'password': '12',
            'role': 'analyst'
        }, follow_redirects=True)
        assert resp.status_code in (200, 400)
        assert b'at least' in resp.data.lower() or b'too short' in resp.data.lower() or b'weak' in resp.data.lower() or resp.status_code == 400

    def test_xss_in_case_description_stripped(self, client):
        _make_lead(client)
        malicious = '<script>alert("xss")</script>'
        resp = client.post('/cases/new', data={
            'title': 'XSS Test',
            'description': malicious,
            'severity': 'low'
        }, follow_redirects=True)
        assert b'<script>' not in resp.data

    def test_duplicate_username_rejected(self, client):
        uname = _make_lead(client)
        resp = client.post('/analysts/new', data={
            'username': uname,
            'email': 'unique@test.com',
            'password': 'StrongPass123!',
            'role': 'analyst'
        }, follow_redirects=True)
        assert b'already exists' in resp.data.lower() or resp.status_code == 400

    def test_sql_injection_in_username(self, client):
        resp = client.post('/auth/login', data={
            'username': "' OR 1=1 --",
            'password': 'anything'
        }, follow_redirects=True)
        assert resp.status_code in (200, 429)
        assert b'Invalid' in resp.data or b'login' in resp.data.lower() or b'locked' in resp.data

    def test_evidence_nonexistent_case_rejected(self, client):
        _make_lead(client)
        resp = client.post('/evidence/new', data={
            'title': 'Valid title',
            'content': 'Some content',
            'source': 'manual',
            'case_id': '99999'
        }, follow_redirects=True)
        assert b'Case not found' in resp.data
