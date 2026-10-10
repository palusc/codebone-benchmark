TABLE = "support_cases"


def new_case(entity_id, **fields):
    return {"id": entity_id, "kind": "case", **fields}
