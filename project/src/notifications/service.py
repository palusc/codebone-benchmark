from src.notifications import events, repository
from src.notifications.models import new_notification


def create(entity_id, **fields):
    row = repository.save(new_notification(entity_id, **fields))
    events.created(row)
    return row


def fetch(entity_id):
    return repository.get(entity_id)
