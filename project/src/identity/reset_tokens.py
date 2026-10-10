import secrets

RESET_TTL_MINUTES = 15


def issue(user_id, now):
    return {"user_id": user_id, "token": secrets.token_urlsafe(18), "issued_at": now}


def is_valid(token, now):
    return now - token["issued_at"] < RESET_TTL_MINUTES
