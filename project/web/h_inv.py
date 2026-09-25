from db import store
from utils import calc2


def mk_inv(body):
    inv = {"id": body["id"], "items": body["items"], "total": calc2.tot(body["items"])}
    store.save_invoice(inv)
    return {"ok": True, "invoice": inv}
