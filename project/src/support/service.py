from src.support import events, repository
from src.support.models import new_case


def create(entity_id, **fields):
    row = repository.save(new_case(entity_id, **fields))
    events.created(row)
    return row


def fetch(entity_id):
    return repository.get(entity_id)
