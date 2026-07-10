from datetime import datetime
from app.models.analyst import Analyst
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.playbook import Playbook


class TestAnalyst:
    def test_from_row(self):
        row = {
            'id': 1, 'username': 'alice', 'email': 'alice@secops.com',
            'password_hash': '$2b$12$abc', 'role': 'analyst',
            'created_at': datetime(2026, 1, 1)
        }
        a = Analyst.from_row(row)
        assert a.id == 1
        assert a.username == 'alice'
        assert a.role == 'analyst'

    def test_from_row_none(self):
        assert Analyst.from_row(None) is None

    def test_set_password(self):
        a = Analyst(None, 'test', 't@t.com', '')
        a.set_password('MyP@ss123')
        assert a.password_hash != ''
        assert a.password_hash != 'MyP@ss123'

    def test_check_password_correct(self):
        a = Analyst(None, 'test', 't@t.com', '')
        a.set_password('MyP@ss123')
        assert a.check_password('MyP@ss123') is True

    def test_check_password_wrong(self):
        a = Analyst(None, 'test', 't@t.com', '')
        a.set_password('MyP@ss123')
        assert a.check_password('wrong') is False

    def test_check_password_empty(self):
        a = Analyst(None, 'test', 't@t.com', '')
        a.set_password('MyP@ss123')
        assert a.check_password('') is False

    def test_default_role(self):
        a = Analyst(1, 'alice', 'a@a.com', 'hash')
        assert a.role == 'analyst'

    def test_custom_role(self):
        a = Analyst(1, 'lead', 'l@l.com', 'hash', role='lead')
        assert a.role == 'lead'


class TestCase:
    def test_from_row(self):
        row = {
            'id': 1, 'title': 'Phishing Alert', 'description': 'Suspicious email',
            'severity': 'high', 'status': 'open',
            'created_at': datetime(2026, 1, 1), 'updated_at': datetime(2026, 1, 2),
            'analyst_id': 1
        }
        c = Case.from_row(row)
        assert c.id == 1
        assert c.title == 'Phishing Alert'
        assert c.severity == 'high'

    def test_from_row_none(self):
        assert Case.from_row(None) is None


class TestEvidence:
    def test_from_row(self):
        row = {
            'id': 1, 'title': 'IP Log', 'content': '8.8.8.8',
            'source': 'manual', 'created_at': datetime(2026, 1, 1),
            'case_id': 1
        }
        e = Evidence.from_row(row)
        assert e.title == 'IP Log'
        assert e.case_id == 1


class TestPlaybook:
    def test_from_row(self):
        row = {
            'id': 1, 'name': 'Ransomware Response', 'description': 'Steps',
            'steps': '["isolate","analyze"]', 'created_at': datetime(2026, 1, 1)
        }
        p = Playbook.from_row(row)
        assert p.name == 'Ransomware Response'

