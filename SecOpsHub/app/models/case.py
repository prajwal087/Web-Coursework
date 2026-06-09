from datetime import datetime


class Case:
    def __init__(self, id, title, description, severity, status, created_at, updated_at, analyst_id):
        self.id = id
        self.title = title
        self.description = description
        self.severity = severity
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.analyst_id = analyst_id

    @staticmethod
    def from_row(row):
        if row is None:
            return None
        return Case(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            severity=row['severity'],
            status=row['status'],
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            analyst_id=row['analyst_id']
        )
