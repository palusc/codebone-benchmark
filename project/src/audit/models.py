TABLE = "audit_entries"


def new_audit_entry(entity_id, **fields):
    return {"id": entity_id, "kind": "audit_entry", **fields}
