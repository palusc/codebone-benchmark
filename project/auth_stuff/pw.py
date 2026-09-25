import hashlib


def hash_pw(pw, salt="x"):
    return hashlib.sha256((salt + pw).encode()).hexdigest()
