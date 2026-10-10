from src.platform import event_bus

CREATED = "fulfillment.shipment.created"


def created(row):
    event_bus.publish(CREATED, {"shipment_id": row["id"]})
