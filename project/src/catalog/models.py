TABLE = "products"


def new_product(entity_id, **fields):
    return {"id": entity_id, "kind": "product", **fields}
