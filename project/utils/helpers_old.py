# TODO remove, replaced by helpers.py
def clamp(x, lo, hi):
    return x if lo <= x <= hi else (lo if x < lo else hi)
