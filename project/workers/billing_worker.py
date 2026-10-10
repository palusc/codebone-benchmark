from src.billing.repository import get_invoice


def render_receipt(invoice_id):
    invoice = get_invoice(invoice_id)
    return f"Receipt {invoice_id}: {invoice['gross']}" if invoice else None
