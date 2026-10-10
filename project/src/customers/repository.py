from src.platform import memory_db

PERSISTED_FIELDS = ("id", "name", "email", "country")


def save(customer):
    row = {field: customer.get(field) for field in PERSISTED_FIELDS}
    return memory_db.put("customers", row["id"], row)


def get(customer_id):
    return memory_db.get("customers", customer_id)
