from src.customers import service


def create_customer(body):
    return {"ok": True, "customer": service.create_customer(body)}


def get_customer(body):
    return {"ok": True, "customer": service.get_customer(body["id"])}
