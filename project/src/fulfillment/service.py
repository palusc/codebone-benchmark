from src.fulfillment import events, repository
from src.fulfillment.models import new_shipment


def create(entity_id, **fields):
    row = repository.save(new_shipment(entity_id, **fields))
    events.created(row)
    return row


def fetch(entity_id):
    return repository.get(entity_id)
