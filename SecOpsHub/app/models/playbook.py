from datetime import datetime


class Playbook:
    def __init__(self, id, name, description, steps, created_at, updated_at=None):
        self.id = id
        self.name = name
        self.description = description
        self.steps = steps
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def from_row(row):
        if row is None:
            return None
        return Playbook(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            steps=row['steps'],
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )
