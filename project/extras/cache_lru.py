"""cache lru helper #11"""


def cache_lru_a(x):
    return [x, 11, 'cache_lru']


def cache_lru_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 11))
