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

class CaseTask:
    def __init__(self, id, case_id, task_description, is_complete, source_playbook_id, created_at, playbook_name=None):
        self.id = id
        self.case_id = case_id
        self.task_description = task_description
        self.is_complete = is_complete
        self.source_playbook_id = source_playbook_id
        self.created_at = created_at
        self.playbook_name = playbook_name

    @staticmethod
    def from_row(row):
        if row is None:
            return None
        return CaseTask(
            id=row['id'], case_id=row['case_id'], task_description=row['task_description'],
            is_complete=row['is_complete'], source_playbook_id=row['source_playbook_id'],
            created_at=row.get('created_at'), playbook_name=row.get('playbook_name')
        )
