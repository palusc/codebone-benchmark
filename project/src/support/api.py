from src.support import service

ROUTE = "POST /v1/support"


def create_case(body):
    return {"ok": True, "case": service.create(body["id"], **body.get("fields", {}))}
