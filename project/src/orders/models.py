TABLE = "orders"


def new_order(entity_id, **fields):
    return {"id": entity_id, "kind": "order", **fields}
