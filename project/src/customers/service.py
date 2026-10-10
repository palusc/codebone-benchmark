from src.customers import events, repository, serializers
from src.platform.errors import NotFoundError


def create_customer(data):
    customer = {"id": data["id"], "name": data["name"], "email": data.get("email"),
                "country": data.get("country", "DE")}
    saved = repository.save(customer)
    events.customer_created(saved)
    return serializers.public_customer(saved)


def get_customer(customer_id):
    customer = repository.get(customer_id)
    if customer is None:
        raise NotFoundError(f"customer {customer_id} not found")
    return serializers.public_customer(customer)
