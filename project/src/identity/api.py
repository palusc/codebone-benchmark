from src.identity.reset_tokens import issue
from src.platform.clock import utc_timestamp


def request_password_reset(body):
    return {"ok": True, "reset": issue(body["user_id"], utc_timestamp())}
