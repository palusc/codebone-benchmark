# one-off from 2021, do not run
from db import store

def run():
    for cid in range(1, 5):
        store.save_customer({"id": cid, "name": f"legacy{cid}", "email": None})
