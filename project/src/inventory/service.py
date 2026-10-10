from src.inventory import events, repository
from src.inventory.models import new_stock_item


def create(entity_id, **fields):
    row = repository.save(new_stock_item(entity_id, **fields))
    events.created(row)
    return row


def fetch(entity_id):
    return repository.get(entity_id)
