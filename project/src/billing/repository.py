from src.platform import memory_db


def get_invoice(invoice_id):
    return memory_db.get("invoices", invoice_id)


def list_invoices():
    return memory_db.all_rows("invoices")
