from decimal import Decimal
from src.billing.tax_policy import gross_for, vat_for
from src.platform import memory_db


def create_credit_note(note_id, invoice_id, net_amount):
    net = Decimal(str(net_amount))
    note = {"id": note_id, "invoice_id": invoice_id, "net": net,
            "vat": vat_for(net), "gross": gross_for(net)}
    return memory_db.put("credit_notes", note_id, note)
