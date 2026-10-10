from src.notifications import service

ROUTE = "POST /v1/notifications"


def create_notification(body):
    return {"ok": True, "notification": service.create(body["id"], **body.get("fields", {}))}
