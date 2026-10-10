def can_read_product(actor, row):
    return bool(actor.get("is_admin") or actor.get("organization_id") == row.get("organization_id"))


def label():
    return "Product access policy"
