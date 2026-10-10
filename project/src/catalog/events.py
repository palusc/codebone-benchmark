from src.platform import event_bus

CREATED = "catalog.product.created"


def created(row):
    event_bus.publish(CREATED, {"product_id": row["id"]})
