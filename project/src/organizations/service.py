from src.organizations import events, repository
from src.organizations.models import new_organization


def create(entity_id, **fields):
    row = repository.save(new_organization(entity_id, **fields))
    events.created(row)
    return row


def fetch(entity_id):
    return repository.get(entity_id)
