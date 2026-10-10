PUBLIC_FIELDS = ("id", "name", "email", "country")


def public_customer(customer):
    return {field: customer.get(field) for field in PUBLIC_FIELDS}
