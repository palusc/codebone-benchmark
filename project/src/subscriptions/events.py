from src.platform import event_bus

CREATED = "subscriptions.subscription.created"


def created(row):
    event_bus.publish(CREATED, {"subscription_id": row["id"]})
