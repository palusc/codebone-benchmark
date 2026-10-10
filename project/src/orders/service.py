from src.orders import events, repository
from src.orders.models import new_order


def create(entity_id, **fields):
    row = repository.save(new_order(entity_id, **fields))
    events.created(row)
    return row


def fetch(entity_id):
    return repository.get(entity_id)
