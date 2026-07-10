from app.database import get_db


class TestEvidenceList:
    def test_list_requires_auth(self, client):
        resp = client.get('/evidence/', follow_redirects=True)
        assert b'login' in resp.data.lower()

    def test_list_empty(self, client, lead):
        resp = client.get('/evidence/')
        assert resp.status_code == 200

    def test_list_with_evidence(self, client, lead, sample_case):
        client.post('/evidence/new', data={
            'title': 'Suspicious IP Log',
            'content': 'IP 10.0.0.1 accessed admin panel',
            'source': 'manual',
            'case_id': str(sample_case)
        }, follow_redirects=True)
        resp = client.get('/evidence/')
        assert resp.status_code == 200
        assert b'Suspicious IP Log' in resp.data


class TestEvidenceCreate:
    def test_create_evidence(self, client, lead, sample_case):
        resp = client.post('/evidence/new', data={
            'title': 'Firewall Log Entry',
            'content': 'Blocked inbound connection from 203.0.113.5',
            'source': 'manual',
            'case_id': str(sample_case)
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Firewall Log Entry' in resp.data or b'Evidence added' in resp.data

    def test_create_evidence_persists(self, client, lead, sample_case):
        client.post('/evidence/new', data={
            'title': 'Persist Check',
            'content': 'Evidence content here',
            'source': 'manual',
            'case_id': str(sample_case)
        }, follow_redirects=True)
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM evidence WHERE title = 'Persist Check'")
                row = cur.fetchone()
                assert row is not None
                assert row['content'] == 'Evidence content here'
                assert row['case_id'] == sample_case
        finally:
            conn.close()

    def test_create_evidence_empty_title_fails(self, client, lead, sample_case):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM evidence")
                before = cur.fetchone()['cnt']
        finally:
            conn.close()
        resp = client.post('/evidence/new', data={
            'title': '',
            'content': 'Some content here',
            'source': 'manual',
            'case_id': str(sample_case)
        }, follow_redirects=True)
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM evidence")
                after = cur.fetchone()['cnt']
        finally:
            conn.close()
        # Evidence count should not increase if empty title was rejected
        assert after == before, (
            f"BUG: Evidence was created with empty title! "
            f"Count changed from {before} to {after}. "
            "validate_evidence() in helpers.py does not validate title."
        )
        # Should stay on form page, not redirect to view
        assert b'Add Evidence' in resp.data

    def test_create_evidence_empty_content_fails(self, client, lead, sample_case):
        resp = client.post('/evidence/new', data={
            'title': 'No content',
            'content': '',
            'source': 'manual',
            'case_id': str(sample_case)
        }, follow_redirects=True)
        assert b'required' in resp.data.lower()

    def test_create_evidence_invalid_source_fails(self, client, lead, sample_case):
        resp = client.post('/evidence/new', data={
            'title': 'Bad source',
            'content': 'Some content',
            'source': 'invalid_source_type',
            'case_id': str(sample_case)
        }, follow_redirects=True)
        assert b'invalid' in resp.data.lower()


class TestEvidenceView:
    def test_view_evidence(self, client, lead, sample_case):
        client.post('/evidence/new', data={
            'title': 'View Test',
            'content': 'Content to view',
            'source': 'manual',
            'case_id': str(sample_case)
        }, follow_redirects=True)
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM evidence ORDER BY id DESC LIMIT 1")
                ev_id = cur.fetchone()['id']
        finally:
            conn.close()
        resp = client.get(f'/evidence/{ev_id}')
        assert resp.status_code == 200
        assert b'View Test' in resp.data

    def test_view_nonexistent_evidence(self, client, lead):
        resp = client.get('/evidence/99999', follow_redirects=True)
        assert b'not found' in resp.data.lower()


class TestEvidenceEdit:
    def test_edit_evidence(self, client, lead, sample_case):
        client.post('/evidence/new', data={
            'title': 'Editable',
            'content': 'Original content',
            'source': 'manual',
            'case_id': str(sample_case)
        }, follow_redirects=True)
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM evidence ORDER BY id DESC LIMIT 1")
                ev_id = cur.fetchone()['id']
        finally:
            conn.close()
        resp = client.post(f'/evidence/{ev_id}/edit', data={
            'title': 'Edited Title',
            'content': 'Edited content',
            'source': 'ip_intel',
            'case_id': str(sample_case)
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Edited Title' in resp.data


class TestEvidenceDelete:
    def test_delete_evidence(self, client, lead, sample_case):
        client.post('/evidence/new', data={
            'title': 'To Delete',
            'content': 'Delete me',
            'source': 'manual',
            'case_id': str(sample_case)
        }, follow_redirects=True)
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM evidence ORDER BY id DESC LIMIT 1")
                ev_id = cur.fetchone()['id']
        finally:
            conn.close()
        resp = client.post(f'/evidence/{ev_id}/delete', follow_redirects=True)
        assert resp.status_code == 200

    def test_delete_evidence_removes_from_db(self, client, lead, sample_case):
        client.post('/evidence/new', data={
            'title': 'Gone',
            'content': 'Will be deleted',
            'source': 'manual',
            'case_id': str(sample_case)
        }, follow_redirects=True)
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM evidence ORDER BY id DESC LIMIT 1")
                ev_id = cur.fetchone()['id']
        finally:
            conn.close()
        client.post(f'/evidence/{ev_id}/delete', follow_redirects=True)
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM evidence WHERE id = %s", (ev_id,))
                assert cur.fetchone() is None
        finally:
            conn.close()

