from src.analytics import events, repository
from src.analytics.models import new_metric


def create(entity_id, **fields):
    row = repository.save(new_metric(entity_id, **fields))
    events.created(row)
    return row


def fetch(entity_id):
    return repository.get(entity_id)
