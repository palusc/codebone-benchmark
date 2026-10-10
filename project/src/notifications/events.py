from src.platform import event_bus

CREATED = "notifications.notification.created"


def created(row):
    event_bus.publish(CREATED, {"notification_id": row["id"]})
