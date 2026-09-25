"""health helper #23"""


def health_a(x):
    return [x, 23, 'health']


def health_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 23))
