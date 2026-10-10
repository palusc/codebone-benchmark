from src.inventory import service

ROUTE = "POST /v1/inventory"


def create_stock_item(body):
    return {"ok": True, "stock_item": service.create(body["id"], **body.get("fields", {}))}
