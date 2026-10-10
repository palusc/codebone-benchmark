from src.analytics import service

ROUTE = "POST /v1/analytics"


def create_metric(body):
    return {"ok": True, "metric": service.create(body["id"], **body.get("fields", {}))}
