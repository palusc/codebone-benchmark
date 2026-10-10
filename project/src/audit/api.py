from src.audit import service

ROUTE = "POST /v1/audit"


def create_audit_entry(body):
    return {"ok": True, "audit_entry": service.create(body["id"], **body.get("fields", {}))}
