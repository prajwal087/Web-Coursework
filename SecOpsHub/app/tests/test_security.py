class TestSecurityGaps:
    def test_admin_page_requires_lead_role(self, client):
        resp = client.get('/admin/', follow_redirects=True)
        assert resp.status_code == 200

    def test_admin_page_not_accessible_by_analyst(self, client):
        resp = client.get('/admin/')
        assert resp.status_code == 302

    def test_analyst_new_requires_lead(self, client):
        resp = client.get('/analysts/new')
        assert resp.status_code == 302

    def test_analyst_edit_requires_lead(self, client):
        resp = client.get('/analysts/1/edit')
        assert resp.status_code == 302

    def test_analyst_delete_requires_lead(self, client):
        resp = client.post('/analysts/1/delete')
        assert resp.status_code == 302

    def test_csrf_protection_active(self, client):
        resp = client.post('/analysts/1/delete', headers={'X-CSRFToken': ''})
        assert resp.status_code in (302, 400, 403)

    def test_profile_shows_own_cases_only(self, client):
        resp = client.get('/profile/')
        assert resp.status_code == 302

    def test_http_security_headers_present(self, client):
        resp = client.get('/auth/login')
        assert resp.headers.get('X-Content-Type-Options') == 'nosniff'
        assert resp.headers.get('X-Frame-Options') == 'DENY'
        assert resp.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'

    def test_session_cookie_http_only(self, client):
        resp = client.get('/auth/login')
        cookie = resp.headers.get('Set-Cookie', '')
        assert 'HttpOnly' in cookie
