import json
import os

_PATH = os.environ.get("SHOP_DB", "shop_db.json")
_FIELDS = ("id", "name", "email")


def _load():
    if not os.path.exists(_PATH):
        return {"customers": {}, "invoices": {}}
    with open(_PATH) as f:
        return json.load(f)


def _save(db):
    with open(_PATH, "w") as f:
        json.dump(db, f)


def save_customer(c):
    db = _load()
    db["customers"][str(c["id"])] = {k: c.get(k) for k in _FIELDS}
    _save(db)


def get_customer(cid):
    return _load()["customers"].get(str(cid))


def save_invoice(inv):
    db = _load()
    db["invoices"][str(inv["id"])] = inv
    _save(db)
