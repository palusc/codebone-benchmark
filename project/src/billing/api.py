from src.billing.invoice_service import create_invoice as create


def create_invoice(body):
    invoice = create(body["id"], body["customer_id"], body["lines"])
    return {"ok": True, "invoice": invoice}
