from src.orders import service

ROUTE = "POST /v1/orders"


def create_order(body):
    return {"ok": True, "order": service.create(body["id"], **body.get("fields", {}))}
