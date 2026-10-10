from src.payments import ledger
from src.platform import event_bus


def handle_payment_succeeded(payload):
    event_id = payload["id"]
    charge = payload["data"]["object"]
    entry = {"event_id": event_id, "charge_id": charge["id"],
             "invoice_id": charge["metadata"]["invoice_id"], "amount": charge["amount"]}
    ledger.add_entry(entry)
    event_bus.publish("payments.charge.succeeded", entry)
    return {"processed": True, "duplicate": False, "event_id": event_id}
