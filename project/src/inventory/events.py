from src.platform import event_bus

CREATED = "inventory.stock_item.created"


def created(row):
    event_bus.publish(CREATED, {"stock_item_id": row["id"]})
