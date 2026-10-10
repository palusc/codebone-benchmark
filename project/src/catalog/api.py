from src.catalog import service

ROUTE = "POST /v1/catalog"


def create_product(body):
    return {"ok": True, "product": service.create(body["id"], **body.get("fields", {}))}
