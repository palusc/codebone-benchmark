TABLE = "notifications"


def new_notification(entity_id, **fields):
    return {"id": entity_id, "kind": "notification", **fields}
