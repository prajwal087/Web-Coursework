from datetime import datetime


class Evidence:
    def __init__(self, id, title, content, source, created_at, case_id):
        self.id = id
        self.title = title
        self.content = content
        self.source = source
        self.created_at = created_at
        self.case_id = case_id

    @staticmethod
    def from_row(row):
        if row is None:
            return None
        return Evidence(
            id=row['id'],
            title=row['title'],
            content=row['content'],
            source=row['source'],
            created_at=row.get('created_at'),
            case_id=row['case_id']
        )
