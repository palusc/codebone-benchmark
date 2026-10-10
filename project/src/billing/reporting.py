from decimal import Decimal, ROUND_HALF_UP


def invoice_export_row(invoice):
    # Kept separate from the invoice renderer for finance exports.
    net = Decimal(str(invoice["net"]))
    gross = (net * Decimal("1.19")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"invoice_id": invoice["id"], "net": net, "gross": gross}
