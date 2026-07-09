from app.database import get_db
from app.models.case import Case
from app.models.case import CaseTask


class TestCasesList:
    def test_list_requires_auth(self, client):
        resp = client.get('/cases/', follow_redirects=True)
        assert b'login' in resp.data.lower()

    def test_list_empty(self, client, lead):
        resp = client.get('/cases/')
        assert resp.status_code == 200

    def test_list_with_cases(self, client, lead, sample_case):
        resp = client.get('/cases/')
        assert resp.status_code == 200
        assert b'Test Security Incident' in resp.data


class TestCasesCreate:
    def test_create_case(self, client, lead):
        resp = client.post('/cases/new', data={
            'title': 'Phishing Campaign',
            'description': 'Multiple phishing emails reported',
            'severity': 'critical'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Phishing Campaign' in resp.data

    def test_create_case_persists_to_db(self, client, lead):
        client.post('/cases/new', data={
            'title': 'DB Check Case',
            'description': 'Verify persistence',
            'severity': 'medium'
        }, follow_redirects=True)
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM cases WHERE title = 'DB Check Case'")
                row = cur.fetchone()
                assert row is not None
                assert row['severity'] == 'medium'
                case = Case.from_row(row)
                assert case.description == 'Verify persistence'
        finally:
            conn.close()

    def test_create_case_empty_title_fails(self, client, lead):
        resp = client.post('/cases/new', data={
            'title': '',
            'description': 'test',
            'severity': 'low'
        }, follow_redirects=True)
        assert b'required' in resp.data.lower() or resp.status_code == 400

    def test_create_case_invalid_severity_fails(self, client, lead):
        resp = client.post('/cases/new', data={
            'title': 'Bad severity',
            'description': 'test',
            'severity': 'ultra-critical'
        }, follow_redirects=True)
        assert resp.status_code in (200, 400)
        assert b'invalid' in resp.data.lower()

    def test_create_case_missing_severity_fails(self, client, lead):
        resp = client.post('/cases/new', data={
            'title': 'No severity',
            'description': 'test'
        }, follow_redirects=True)
        assert b'invalid' in resp.data.lower() or resp.status_code == 400

    def test_create_case_title_too_long_fails(self, client, lead):
        long_title = 'A' * 201
        resp = client.post('/cases/new', data={
            'title': long_title,
            'description': 'test',
            'severity': 'low'
        }, follow_redirects=True)
        assert b'200' in resp.data or resp.status_code == 400

    def test_create_case_sanitizes_html(self, client, lead):
        resp = client.post('/cases/new', data={
            'title': '<script>alert("xss")</script>',
            'description': 'safe',
            'severity': 'low'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'<script>' not in resp.data

    def test_create_case_title_with_html_at_limit_fails(self, client, lead):
        html_chars = "<>" * 5
        title = "A" * 190 + html_chars
        resp = client.post('/cases/new', data={
            'title': title,
            'description': 'test',
            'severity': 'low'
        }, follow_redirects=True)
        assert b'Title must be 200' in resp.data


class TestCasesView:
    def test_view_case(self, client, lead, sample_case):
        resp = client.get(f'/cases/{sample_case}')
        assert resp.status_code == 200
        assert b'Test Security Incident' in resp.data

    def test_view_nonexistent_case(self, client, lead):
        resp = client.get('/cases/99999', follow_redirects=True)
        assert b'not found' in resp.data.lower() or resp.status_code == 302


class TestCasesEdit:
    def test_edit_case(self, client, lead, sample_case):
        resp = client.post(f'/cases/{sample_case}/edit', data={
            'title': 'Updated Title',
            'description': 'Updated description',
            'severity': 'low',
            'status': 'in_progress'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Updated Title' in resp.data

    def test_edit_case_actually_updates_db(self, client, lead, sample_case):
        client.post(f'/cases/{sample_case}/edit', data={
            'title': 'DB Updated',
            'description': 'New desc',
            'severity': 'critical',
            'status': 'resolved'
        }, follow_redirects=True)
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM cases WHERE id = %s", (sample_case,))
                row = cur.fetchone()
                assert row['title'] == 'DB Updated'
                assert row['severity'] == 'critical'
                assert row['status'] == 'resolved'
        finally:
            conn.close()

    def test_edit_case_empty_title_fails(self, client, lead, sample_case):
        resp = client.post(f'/cases/{sample_case}/edit', data={
            'title': '',
            'description': 'test',
            'severity': 'low',
            'status': 'open'
        }, follow_redirects=True)
        assert b'required' in resp.data.lower()


class TestCasesDelete:
    def test_delete_case(self, client, lead, sample_case):
        resp = client.post(f'/cases/{sample_case}/delete', follow_redirects=True)
        assert resp.status_code == 200

    def test_delete_case_removes_from_db(self, client, lead, sample_case):
        client.post(f'/cases/{sample_case}/delete', follow_redirects=True)
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM cases WHERE id = %s", (sample_case,))
                assert cur.fetchone() is None
        finally:
            conn.close()


class TestCasesPlaybook:
    def test_apply_playbook_to_case(self, client, lead, sample_case, sample_playbook):
        resp = client.post(f'/cases/{sample_case}/apply-playbook', data={
            'playbook_id': sample_playbook
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'applied' in resp.data.lower() or b'success' in resp.data.lower()

    def test_apply_playbook_creates_tasks(self, client, lead, sample_case, sample_playbook):
        client.post(f'/cases/{sample_case}/apply-playbook', data={
            'playbook_id': sample_playbook
        }, follow_redirects=True)
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) AS cnt FROM case_tasks WHERE case_id = %s",
                    (sample_case,)
                )
                row = cur.fetchone()
                assert row['cnt'] == 4
        finally:
            conn.close()

    def test_apply_same_playbook_twice_fails(self, client, lead, sample_case, sample_playbook):
        client.post(f'/cases/{sample_case}/apply-playbook', data={
            'playbook_id': sample_playbook
        }, follow_redirects=True)
        resp = client.post(f'/cases/{sample_case}/apply-playbook', data={
            'playbook_id': sample_playbook
        }, follow_redirects=True)
        assert b'already' in resp.data.lower() or b'applied' in resp.data.lower()

    def test_toggle_task(self, client, lead, sample_case, sample_playbook):
        client.post(f'/cases/{sample_case}/apply-playbook', data={
            'playbook_id': sample_playbook
        }, follow_redirects=True)
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM case_tasks WHERE case_id = %s LIMIT 1",
                    (sample_case,)
                )
                task_id = cur.fetchone()['id']
        finally:
            conn.close()
        resp = client.post(
            f'/cases/{sample_case}/tasks/{task_id}/toggle',
            data={'is_complete': '1'},
            follow_redirects=True
        )
        assert resp.status_code == 200
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT is_complete FROM case_tasks WHERE id = %s", (task_id,))
                assert cur.fetchone()['is_complete'] == 1
        finally:
            conn.close()

    def test_toggle_task_ajax(self, client, lead, sample_case, sample_playbook):
        client.post(f'/cases/{sample_case}/apply-playbook', data={
            'playbook_id': sample_playbook
        }, follow_redirects=True)
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM case_tasks WHERE case_id = %s LIMIT 1",
                    (sample_case,)
                )
                task_id = cur.fetchone()['id']
        finally:
            conn.close()
        resp = client.post(
            f'/cases/{sample_case}/tasks/{task_id}/toggle',
            data={'is_complete': '1'},
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data is not None
        assert data.get('success') is True
