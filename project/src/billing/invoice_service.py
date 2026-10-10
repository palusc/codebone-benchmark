from decimal import Decimal
from src.billing.tax_policy import gross_for, vat_for
from src.platform import event_bus, memory_db


def create_invoice(invoice_id, customer_id, lines):
    net = sum(Decimal(str(line["unit_price"])) * line["quantity"] for line in lines)
    invoice = {
        "id": invoice_id,
        "customer_id": customer_id,
        "lines": lines,
        "net": net.quantize(Decimal("0.01")),
        "vat": vat_for(net),
        "gross": gross_for(net),
    }
    memory_db.put("invoices", invoice_id, invoice)
    event_bus.publish("billing.invoice.created", {"invoice_id": invoice_id, "gross": str(invoice["gross"])})
    return invoice
