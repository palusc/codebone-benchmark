from src.catalog import events, repository
from src.catalog.models import new_product


def create(entity_id, **fields):
    row = repository.save(new_product(entity_id, **fields))
    events.created(row)
    return row


def fetch(entity_id):
    return repository.get(entity_id)
