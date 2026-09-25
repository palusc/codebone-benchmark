from db import store


def new_c(body):
    c = {"id": body["id"], "name": body["name"], "email": body.get("email")}
    store.save_customer(c)
    return {"ok": True, "customer": c}


def get_c(body):
    c = store.get_customer(body["id"])
    if c is None:
        return {"ok": False}
    return {"ok": True, "customer": {"id": c["id"], "name": c["name"], "email": c["email"]}}
