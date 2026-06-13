from datetime import datetime

class Evidence:
    def __init__(self, id, title, content, source, created_at, case_id):
        self.id = id
        self.title = title
        self.content = content
        self.source = source
        self.created_at = created_at
        self.case_id = case_id
