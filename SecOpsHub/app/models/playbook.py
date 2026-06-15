from datetime import datetime


class Playbook:
    def __init__(self, id, name, description, steps, created_at):
        self.id = id
        self.name = name
        self.description = description
        self.steps = steps
        