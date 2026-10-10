from src.audit import events, repository
from src.audit.models import new_audit_entry


def create(entity_id, **fields):
    row = repository.save(new_audit_entry(entity_id, **fields))
    events.created(row)
    return row


def fetch(entity_id):
    return repository.get(entity_id)
