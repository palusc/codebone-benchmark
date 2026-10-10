import hashlib


def digest(password, salt="northstar"):
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
