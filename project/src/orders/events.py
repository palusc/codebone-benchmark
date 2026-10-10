from src.platform import event_bus

CREATED = "orders.order.created"


def created(row):
    event_bus.publish(CREATED, {"order_id": row["id"]})
