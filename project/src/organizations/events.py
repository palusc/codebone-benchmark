from src.platform import event_bus

CREATED = "organizations.organization.created"


def created(row):
    event_bus.publish(CREATED, {"organization_id": row["id"]})
