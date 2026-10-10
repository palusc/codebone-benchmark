def can_read_stock_item(actor, row):
    return bool(actor.get("is_admin") or actor.get("organization_id") == row.get("organization_id"))


def label():
    return "Stock Item access policy"
