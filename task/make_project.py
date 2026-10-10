"""Generate the deterministic Northstar SaaS benchmark project.

The project is intentionally realistic rather than obscure: several domains share a small
platform layer, HTTP handlers call services, services write repositories and publish events,
workers consume those events, and old migrations/docs create believable search noise.

Usage: python3 task/make_project.py [target]
"""
from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent


CORE_FILES = {
    "README.md": """
    # Northstar Commerce

    A compact SaaS commerce monolith used for integration exercises. It contains an API,
    background workers, domain modules, migrations and a small TypeScript operations console.

    Runtime code is pure Python so the exercise needs no dependency installation.
    """,
    "pyproject.toml": """
    [project]
    name = "northstar-commerce"
    version = "2.8.0"
    requires-python = ">=3.11"

    [tool.pytest.ini_options]
    pythonpath = ["."]
    """,
    ".gitignore": """
    __pycache__/
    *.pyc
    .northstar/
    """,
    "apps/__init__.py": "",
    "apps/api/__init__.py": "",
    "apps/api/main.py": """
    from apps.api.routes import ROUTES


    def dispatch(method, path, body=None):
        handler = ROUTES[f"{method} {path}"]
        return handler(body or {})
    """,
    "apps/api/routes.py": """
    from src.billing.api import create_invoice
    from src.customers.api import create_customer, get_customer
    from src.identity.api import request_password_reset
    from src.payments.api import payment_webhook

    ROUTES = {
        "POST /v1/invoices": create_invoice,
        "POST /v1/customers": create_customer,
        "GET /v1/customers": get_customer,
        "POST /v1/password-resets": request_password_reset,
        "POST /v1/webhooks/payments": payment_webhook,
    }
    """,
    "src/__init__.py": "",
    "src/platform/__init__.py": "",
    "src/platform/clock.py": """
    import time


    def utc_timestamp():
        return int(time.time())
    """,
    "src/platform/ids.py": """
    from itertools import count

    _ids = count(1000)


    def new_id(prefix):
        return f"{prefix}_{next(_ids)}"
    """,
    "src/platform/memory_db.py": """
    from copy import deepcopy

    TABLES = {
        "customers": {},
        "invoices": {},
        "credit_notes": {},
        "ledger_entries": [],
        "claimed_webhooks": set(),
    }


    def reset():
        TABLES["customers"].clear()
        TABLES["invoices"].clear()
        TABLES["credit_notes"].clear()
        TABLES["ledger_entries"].clear()
        TABLES["claimed_webhooks"].clear()


    def put(table, key, value):
        TABLES[table][str(key)] = deepcopy(value)
        return deepcopy(value)


    def get(table, key):
        value = TABLES[table].get(str(key))
        return deepcopy(value) if value is not None else None


    def append(table, value):
        TABLES[table].append(deepcopy(value))
        return deepcopy(value)


    def all_rows(table):
        rows = TABLES[table]
        return deepcopy(list(rows.values()) if isinstance(rows, dict) else rows)
    """,
    "src/platform/event_bus.py": """
    from copy import deepcopy

    EVENTS = []


    def publish(topic, payload):
        EVENTS.append({"topic": topic, "payload": deepcopy(payload)})


    def reset():
        EVENTS.clear()


    def published(topic=None):
        rows = EVENTS if topic is None else [e for e in EVENTS if e["topic"] == topic]
        return deepcopy(rows)
    """,
    "src/platform/errors.py": """
    class NotFoundError(LookupError):
        pass


    class ValidationError(ValueError):
        pass
    """,
    "src/billing/__init__.py": "",
    "src/billing/tax_policy.py": """
    from decimal import Decimal, ROUND_HALF_UP

    STANDARD_VAT = Decimal("0.19")


    def vat_for(net, rate=STANDARD_VAT):
        return (Decimal(str(net)) * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


    def gross_for(net, rate=STANDARD_VAT):
        amount = Decimal(str(net))
        return (amount + vat_for(amount, rate)).quantize(Decimal("0.01"))
    """,
    "src/billing/invoice_service.py": """
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
    """,
    "src/billing/credit_notes.py": """
    from decimal import Decimal
    from src.billing.tax_policy import gross_for, vat_for
    from src.platform import memory_db


    def create_credit_note(note_id, invoice_id, net_amount):
        net = Decimal(str(net_amount))
        note = {"id": note_id, "invoice_id": invoice_id, "net": net,
                "vat": vat_for(net), "gross": gross_for(net)}
        return memory_db.put("credit_notes", note_id, note)
    """,
    "src/billing/reporting.py": """
    from decimal import Decimal, ROUND_HALF_UP


    def invoice_export_row(invoice):
        # Kept separate from the invoice renderer for finance exports.
        net = Decimal(str(invoice["net"]))
        gross = (net * Decimal("1.19")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {"invoice_id": invoice["id"], "net": net, "gross": gross}
    """,
    "src/billing/api.py": """
    from src.billing.invoice_service import create_invoice as create


    def create_invoice(body):
        invoice = create(body["id"], body["customer_id"], body["lines"])
        return {"ok": True, "invoice": invoice}
    """,
    "src/billing/repository.py": """
    from src.platform import memory_db


    def get_invoice(invoice_id):
        return memory_db.get("invoices", invoice_id)


    def list_invoices():
        return memory_db.all_rows("invoices")
    """,
    "src/billing/events.py": """
    INVOICE_CREATED = "billing.invoice.created"
    CREDIT_NOTE_CREATED = "billing.credit_note.created"
    """,
    "src/customers/__init__.py": "",
    "src/customers/repository.py": """
    from src.platform import memory_db

    PERSISTED_FIELDS = ("id", "name", "email", "country")


    def save(customer):
        row = {field: customer.get(field) for field in PERSISTED_FIELDS}
        return memory_db.put("customers", row["id"], row)


    def get(customer_id):
        return memory_db.get("customers", customer_id)
    """,
    "src/customers/serializers.py": """
    PUBLIC_FIELDS = ("id", "name", "email", "country")


    def public_customer(customer):
        return {field: customer.get(field) for field in PUBLIC_FIELDS}
    """,
    "src/customers/events.py": """
    from src.platform import event_bus


    def customer_created(customer):
        payload = {"customer_id": customer["id"], "email": customer.get("email"),
                   "country": customer.get("country")}
        event_bus.publish("customers.customer.created", payload)
    """,
    "src/customers/service.py": """
    from src.customers import events, repository, serializers
    from src.platform.errors import NotFoundError


    def create_customer(data):
        customer = {"id": data["id"], "name": data["name"], "email": data.get("email"),
                    "country": data.get("country", "DE")}
        saved = repository.save(customer)
        events.customer_created(saved)
        return serializers.public_customer(saved)


    def get_customer(customer_id):
        customer = repository.get(customer_id)
        if customer is None:
            raise NotFoundError(f"customer {customer_id} not found")
        return serializers.public_customer(customer)
    """,
    "src/customers/api.py": """
    from src.customers import service


    def create_customer(body):
        return {"ok": True, "customer": service.create_customer(body)}


    def get_customer(body):
        return {"ok": True, "customer": service.get_customer(body["id"])}
    """,
    "src/identity/__init__.py": "",
    "src/identity/reset_tokens.py": """
    import secrets

    RESET_TTL_MINUTES = 15


    def issue(user_id, now):
        return {"user_id": user_id, "token": secrets.token_urlsafe(18), "issued_at": now}


    def is_valid(token, now):
        return now - token["issued_at"] < RESET_TTL_MINUTES
    """,
    "src/identity/passwords.py": """
    import hashlib


    def digest(password, salt="northstar"):
        return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    """,
    "src/identity/api.py": """
    from src.identity.reset_tokens import issue
    from src.platform.clock import utc_timestamp


    def request_password_reset(body):
        return {"ok": True, "reset": issue(body["user_id"], utc_timestamp())}
    """,
    "src/identity/sessions.py": """
    SESSIONS = {}


    def create(session_id, user_id):
        SESSIONS[session_id] = user_id
        return {"id": session_id, "user_id": user_id}
    """,
    "src/payments/__init__.py": "",
    "src/payments/ledger.py": """
    from src.platform import memory_db


    def claim_webhook(event_id):
        claimed = memory_db.TABLES["claimed_webhooks"]
        if event_id in claimed:
            return False
        claimed.add(event_id)
        return True


    def add_entry(entry):
        return memory_db.append("ledger_entries", entry)


    def entries():
        return memory_db.all_rows("ledger_entries")
    """,
    "src/payments/webhooks.py": """
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
    """,
    "src/payments/api.py": """
    from src.payments.webhooks import handle_payment_succeeded


    def payment_webhook(body):
        if body.get("type") != "payment.succeeded":
            return {"processed": False, "ignored": True}
        return handle_payment_succeeded(body)
    """,
    "src/payments/gateway.py": """
    def capture(payment_id, amount):
        return {"id": payment_id, "amount": amount, "status": "captured"}
    """,
    "workers/__init__.py": "",
    "workers/billing_worker.py": """
    from src.billing.repository import get_invoice


    def render_receipt(invoice_id):
        invoice = get_invoice(invoice_id)
        return f"Receipt {invoice_id}: {invoice['gross']}" if invoice else None
    """,
    "workers/customer_worker.py": """
    def sync_customer_to_crm(event):
        return {"external_id": event["payload"]["customer_id"], "synced": True}
    """,
    "workers/payment_worker.py": """
    def reconcile_charge(event):
        return {"event_id": event["payload"]["event_id"], "reconciled": True}
    """,
}


DOMAINS = [
    ("orders", "orders", "order"),
    ("catalog", "products", "product"),
    ("inventory", "stock_items", "stock_item"),
    ("fulfillment", "shipments", "shipment"),
    ("subscriptions", "subscriptions", "subscription"),
    ("support", "support_cases", "case"),
    ("analytics", "metric_points", "metric"),
    ("notifications", "notifications", "notification"),
    ("organizations", "organizations", "organization"),
    ("audit", "audit_entries", "audit_entry"),
]


def domain_files(domain: str, table: str, entity: str) -> dict[str, str]:
    title = entity.replace("_", " ").title()
    return {
        f"src/{domain}/__init__.py": "",
        f"src/{domain}/models.py": f'''\
        TABLE = "{table}"


        def new_{entity}(entity_id, **fields):
            return {{"id": entity_id, "kind": "{entity}", **fields}}
        ''',
        f"src/{domain}/repository.py": f'''\
        from copy import deepcopy
        from src.{domain}.models import TABLE

        _ROWS = {{}}


        def save(row):
            _ROWS[str(row["id"])] = deepcopy(row)
            return deepcopy(row)


        def get(entity_id):
            row = _ROWS.get(str(entity_id))
            return deepcopy(row) if row else None


        def list_all():
            return deepcopy(list(_ROWS.values()))
        ''',
        f"src/{domain}/service.py": f'''\
        from src.{domain} import events, repository
        from src.{domain}.models import new_{entity}


        def create(entity_id, **fields):
            row = repository.save(new_{entity}(entity_id, **fields))
            events.created(row)
            return row


        def fetch(entity_id):
            return repository.get(entity_id)
        ''',
        f"src/{domain}/events.py": f'''\
        from src.platform import event_bus

        CREATED = "{domain}.{entity}.created"


        def created(row):
            event_bus.publish(CREATED, {{"{entity}_id": row["id"]}})
        ''',
        f"src/{domain}/api.py": f'''\
        from src.{domain} import service

        ROUTE = "POST /v1/{domain}"


        def create_{entity}(body):
            return {{"ok": True, "{entity}": service.create(body["id"], **body.get("fields", {{}}))}}
        ''',
        f"src/{domain}/serializers.py": f'''\
        def public_{entity}(row):
            return {{key: value for key, value in row.items() if not key.startswith("internal_")}}
        ''',
        f"src/{domain}/policies.py": f'''\
        def can_read_{entity}(actor, row):
            return bool(actor.get("is_admin") or actor.get("organization_id") == row.get("organization_id"))


        def label():
            return "{title} access policy"
        ''',
    }


DOC_TOPICS = [
    "api-versioning", "audit-retention", "billing-close", "customer-import", "event-naming",
    "inventory-reservations", "payment-retries", "privacy-exports", "queue-ownership",
    "regional-tax", "support-sla", "webhook-signatures",
]


def generated_files() -> dict[str, str]:
    files: dict[str, str] = {}
    for domain, table, entity in DOMAINS:
        files.update(domain_files(domain, table, entity))
        files[f"frontend/features/{domain}/api.ts"] = dedent(f'''\
            export const endpoint = "/v1/{domain}";
            export async function list{domain.title()}() {{
              const response = await fetch(endpoint);
              if (!response.ok) throw new Error("{domain} request failed");
              return response.json();
            }}
        ''')
        files[f"frontend/features/{domain}/types.ts"] = dedent(f'''\
            export type {entity.title().replace("_", "")} = {{
              id: string;
              organizationId?: string;
              status?: string;
            }};
        ''')
    for index, topic in enumerate(DOC_TOPICS, 1):
        files[f"docs/adr/{index:03d}-{topic}.md"] = dedent(f'''\
            # ADR {index:03d}: {topic.replace("-", " ").title()}

            Status: accepted

            This note records historical context for the {topic.replace("-", " ")} boundary.
            Runtime behavior remains owned by the corresponding domain service and repository.
        ''')
    for index in range(1, 16):
        files[f"migrations/{index:04d}_schema_step.py"] = dedent(f'''\
            """Historical migration {index:04d}; not used by the runtime benchmark."""

            REVISION = "{index:04d}"


            def upgrade(schema):
                schema.append("migration_{index:04d}")
                return schema
        ''')
    return files


def write_file(root: Path, relative: str, body: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(body).lstrip("\n"), encoding="utf-8")


def main(target: str | Path) -> None:
    root = Path(target).resolve()
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise ValueError(f"Refusing to overwrite a non-empty destination: {root}")
    root.mkdir(parents=True, exist_ok=True)
    for relative, body in {**CORE_FILES, **generated_files()}.items():
        write_file(root, relative, body)
    file_count = sum(1 for path in root.rglob("*") if path.is_file())
    line_count = sum(len(path.read_text(encoding="utf-8").splitlines()) for path in root.rglob("*") if path.is_file())
    print(f"generated {file_count} files / {line_count} lines at {root}")


if __name__ == "__main__":
    destination = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "project"
    main(destination)
