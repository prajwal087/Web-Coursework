from flask_login import UserMixin
import bcrypt
from datetime import datetime, timezone


class Analyst(UserMixin):
    def __init__(self, id, username, email, password_hash, role='analyst', created_at=None, updated_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode('utf-8'), self.password_hash.encode('utf-8')
        )

    @staticmethod
    def from_row(row):
        if row is None:
            return None
        return Analyst(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            role=row['role'],
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )
