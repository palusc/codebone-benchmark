"""locale helper #20"""


def locale_a(x):
    return [x, 20, 'locale']


def locale_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 20))
