from src.subscriptions import service

ROUTE = "POST /v1/subscriptions"


def create_subscription(body):
    return {"ok": True, "subscription": service.create(body["id"], **body.get("fields", {}))}
