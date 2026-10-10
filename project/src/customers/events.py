from src.platform import event_bus


def customer_created(customer):
    payload = {"customer_id": customer["id"], "email": customer.get("email"),
               "country": customer.get("country")}
    event_bus.publish("customers.customer.created", payload)
