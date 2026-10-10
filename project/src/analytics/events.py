from src.platform import event_bus

CREATED = "analytics.metric.created"


def created(row):
    event_bus.publish(CREATED, {"metric_id": row["id"]})
