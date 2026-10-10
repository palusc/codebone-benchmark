TABLE = "subscriptions"


def new_subscription(entity_id, **fields):
    return {"id": entity_id, "kind": "subscription", **fields}
