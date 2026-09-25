import secrets

TTL_MINUTES = 15


def make_reset_token(user, now):
    return {"user": user, "value": secrets.token_hex(8), "issued": now}


def is_valid(tok, now):
    return now - tok["issued"] < TTL_MINUTES
