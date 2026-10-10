def can_read_audit_entry(actor, row):
    return bool(actor.get("is_admin") or actor.get("organization_id") == row.get("organization_id"))


def label():
    return "Audit Entry access policy"
