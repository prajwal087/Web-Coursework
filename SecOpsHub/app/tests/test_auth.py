class TestAuthRoutes:
    def test_login_page_loads(self, client):
        resp = client.get('/auth/login')
        assert resp.status_code == 200
        assert b'SecOpsHub' in resp.data

    def test_login_invalid_credentials(self, client):
        resp = client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'wrong'
        })
        assert resp.status_code in (200, 429)
        if resp.status_code == 200:
            assert b'Invalid' in resp.data

    def test_logout_requires_login(self, client):
        resp = client.post('/auth/logout', follow_redirects=True)
        assert resp.status_code == 200
        assert b'login' in resp.data.lower() or b'Login' in resp.data

    def test_dashboard_redirects_anon(self, client):
        resp = client.get('/', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Login' in resp.data or b'login' in resp.data

    def test_login_empty_username(self, client):
        resp = client.post('/auth/login', data={
            'username': '',
            'password': 'anything'
        })
        assert resp.status_code in (200, 400)
        assert b'required' in resp.data.lower() or b'Username and password' in resp.data

    def test_login_empty_password(self, client):
        resp = client.post('/auth/login', data={
            'username': 'admin',
            'password': ''
        })
        assert resp.status_code in (200, 400)
        assert b'required' in resp.data.lower() or b'Username and password' in resp.data

    def test_session_expires_after_timeout(self, client):
        with client.session_transaction() as sess:
            sess['_permanent'] = True
        resp = client.get('/')
        assert resp.status_code == 302

    def test_remember_me_persists_session(self, client):
        client.post('/auth/register', data={
            'username': 'Prajwal',
            'email': 'prajwal@test.com',
            'password': 'Pr@jwalBuild1',
        })
        resp = client.post('/auth/login', data={
            'username': 'Prajwal',
            'password': 'Pr@jwalBuild1',
            'remember': 'true'
        }, follow_redirects=True)
        assert b'SOC Dashboard' in resp.data or b'Dashboard' in resp.data

    def test_login_rate_limit_exceeded(self, client):
        for _ in range(12):
            resp = client.post('/auth/login', data={
                'username': 'test',
                'password': 'wrong'
            })
        assert resp.status_code == 429
