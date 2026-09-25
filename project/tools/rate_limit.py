"""rate limit helper #17"""


def rate_limit_a(x):
    return [x, 17, 'rate_limit']


def rate_limit_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 17))
