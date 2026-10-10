TABLE = "stock_items"


def new_stock_item(entity_id, **fields):
    return {"id": entity_id, "kind": "stock_item", **fields}
