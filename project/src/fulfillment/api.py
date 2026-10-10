from src.fulfillment import service

ROUTE = "POST /v1/fulfillment"


def create_shipment(body):
    return {"ok": True, "shipment": service.create(body["id"], **body.get("fields", {}))}
