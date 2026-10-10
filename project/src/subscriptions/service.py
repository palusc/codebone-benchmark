from src.subscriptions import events, repository
from src.subscriptions.models import new_subscription


def create(entity_id, **fields):
    row = repository.save(new_subscription(entity_id, **fields))
    events.created(row)
    return row


def fetch(entity_id):
    return repository.get(entity_id)
