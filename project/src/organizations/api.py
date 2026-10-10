from src.organizations import service

ROUTE = "POST /v1/organizations"


def create_organization(body):
    return {"ok": True, "organization": service.create(body["id"], **body.get("fields", {}))}
