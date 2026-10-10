from src.platform import event_bus

CREATED = "audit.audit_entry.created"


def created(row):
    event_bus.publish(CREATED, {"audit_entry_id": row["id"]})
