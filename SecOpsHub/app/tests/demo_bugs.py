import pytest
import bcrypt
from app import create_app
from app.database import get_db
from config import Config


@pytest.fixture(autouse=True)
def clear_login_attempts(app):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM login_attempts")
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def app():
    Config.MYSQL_DB = 'secops_hub_test'
    _app = create_app()
    _app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SERVER_NAME': 'localhost.localdomain',
    })
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SET FOREIGN_KEY_CHECKS = 0")
            for table in ('evidence', 'case_tasks', 'cases', 'playbooks',
                          'activity_log', 'sessions', 'login_attempts', 'analysts'):
                cur.execute(f"DELETE FROM {table}")
            cur.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()
    finally:
        conn.close()
    return _app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


def _register_and_login(client, username, email, password, role='analyst'):
    import time
    from app.database import get_db
    ts = str(int(time.time() * 1000))[-6:]
    uname = f'{username}_{ts}'
    email_addr = f'{uname}@{email}'
    pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO analysts (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                (uname, email_addr, pw_hash, role)
            )
        conn.commit()
    finally:
        conn.close()

    client.post('/auth/login', data={
        'username': uname,
        'password': password
    }, follow_redirects=True)
    return uname


@pytest.fixture
def lead(client):
    return _register_and_login(client, 'lead', 'lead.com', 'StrongPass123!', 'lead')


@pytest.fixture
def analyst(client):
    return _register_and_login(client, 'analyst', 'analyst.com', 'StrongPass123!', 'analyst')


@pytest.fixture
def sample_case(client, lead):
    client.post('/cases/new', data={
        'title': 'Test Security Incident',
        'description': 'This is a test case',
        'severity': 'high'
    }, follow_redirects=True)
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM cases ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            return row['id']
    finally:
        conn.close()


@pytest.fixture
def sample_playbook(client, lead):
    client.post('/playbooks/new', data={
        'name': 'Incident Response',
        'description': 'Standard IR steps',
        'steps': '["Identify","Contain","Eradicate","Recover"]'
    }, follow_redirects=True)
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM playbooks ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            return row['id']
    finally:
        conn.close()
