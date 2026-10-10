TABLE = "organizations"


def new_organization(entity_id, **fields):
    return {"id": entity_id, "kind": "organization", **fields}
