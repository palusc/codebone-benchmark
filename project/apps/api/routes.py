from src.billing.api import create_invoice
from src.customers.api import create_customer, get_customer
from src.identity.api import request_password_reset
from src.payments.api import payment_webhook

ROUTES = {
    "POST /v1/invoices": create_invoice,
    "POST /v1/customers": create_customer,
    "GET /v1/customers": get_customer,
    "POST /v1/password-resets": request_password_reset,
    "POST /v1/webhooks/payments": payment_webhook,
}
