"""Mechanical verification for the Northstar benchmark.

Usage: python3 task/check.py <project_dir>
Prints one JSON object and exits 0 only when all four tasks pass.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from decimal import Decimal
from pathlib import Path


PROJECT = Path(sys.argv[1]).resolve()
os.chdir(PROJECT)
sys.path.insert(0, str(PROJECT))


def fresh_imports() -> None:
    for name in list(sys.modules):
        if name == "src" or name.startswith("src."):
            del sys.modules[name]
    importlib.invalidate_caches()


def vat_check() -> tuple[bool, str]:
    try:
        from src.billing.credit_notes import create_credit_note
        from src.billing.invoice_service import create_invoice
        from src.billing.reporting import invoice_export_row
        from src.platform import memory_db

        memory_db.reset()
        invoice = create_invoice("inv_1", "cus_1", [{"unit_price": "100.00", "quantity": 1}])
        credit = create_credit_note("cn_1", "inv_1", "100.00")
        exported = invoice_export_row(invoice)
        values = (invoice["gross"], credit["gross"], exported["gross"])
        ok = values == (Decimal("120.00"), Decimal("120.00"), Decimal("120.00"))
        return ok, f"invoice/credit/export gross={','.join(map(str, values))}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def customer_phone_check() -> tuple[bool, str]:
    try:
        from src.customers.service import create_customer, get_customer
        from src.platform import event_bus, memory_db

        memory_db.reset()
        event_bus.reset()
        phone = "+49 30 5550102"
        created = create_customer({"id": "cus_7", "name": "Ada", "email": "ada@example.test", "phone": phone})
        fetched = get_customer("cus_7")
        payload = event_bus.published("customers.customer.created")[-1]["payload"]
        optional = create_customer({"id": "cus_8", "name": "Lin"})
        ok = created.get("phone") == phone and fetched.get("phone") == phone and payload.get("phone") == phone
        ok = ok and "phone" in optional and optional["phone"] is None
        return ok, f"created={created.get('phone')!r}, fetched={fetched.get('phone')!r}, event={payload.get('phone')!r}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def reset_token_check() -> tuple[bool, str]:
    try:
        from src.identity.reset_tokens import is_valid, issue

        token = issue("usr_1", now=1_000)
        ten_minutes = is_valid(token, now=1_600)
        after_expiry = is_valid(token, now=1_901)
        return ten_minutes and not after_expiry, f"valid@10m={ten_minutes}, valid@15m01s={after_expiry}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def webhook_idempotency_check() -> tuple[bool, str]:
    try:
        from src.payments.ledger import entries
        from src.payments.webhooks import handle_payment_succeeded
        from src.platform import event_bus, memory_db

        memory_db.reset()
        event_bus.reset()
        payload = {"id": "evt_retry_42", "type": "payment.succeeded", "data": {"object": {
            "id": "ch_42", "amount": 12900, "metadata": {"invoice_id": "inv_42"}}}}
        first = handle_payment_succeeded(payload)
        second = handle_payment_succeeded(payload)
        emitted = event_bus.published("payments.charge.succeeded")
        ok = len(entries()) == 1 and len(emitted) == 1
        ok = ok and first.get("processed") is True and second.get("duplicate") is True
        return ok, f"ledger={len(entries())}, events={len(emitted)}, duplicate={second.get('duplicate')}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    fresh_imports()
    checks = {
        "vat_policy": vat_check,
        "customer_phone": customer_phone_check,
        "reset_token_ttl": reset_token_check,
        "webhook_idempotency": webhook_idempotency_check,
    }
    results = {}
    details = {}
    for name, check in checks.items():
        passed, detail = check()
        results[name] = passed
        details[name] = detail
    payload = {"passed": results, "details": details, "tasks_ok": sum(results.values()), "tasks_total": len(results)}
    print(json.dumps(payload, sort_keys=True))
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
