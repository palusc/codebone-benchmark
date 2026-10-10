from src.platform import event_bus

CREATED = "support.case.created"


def created(row):
    event_bus.publish(CREATED, {"case_id": row["id"]})
