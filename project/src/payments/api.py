from src.payments.webhooks import handle_payment_succeeded


def payment_webhook(body):
    if body.get("type") != "payment.succeeded":
        return {"processed": False, "ignored": True}
    return handle_payment_succeeded(body)
