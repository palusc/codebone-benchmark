TABLE = "shipments"


def new_shipment(entity_id, **fields):
    return {"id": entity_id, "kind": "shipment", **fields}
