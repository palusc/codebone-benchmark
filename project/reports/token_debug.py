"""token debug helper #2"""


def token_debug_a(x):
    return [x, 2, 'token_debug']


def token_debug_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 2))
