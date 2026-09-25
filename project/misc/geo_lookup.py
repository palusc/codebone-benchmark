"""geo lookup helper #8"""


def geo_lookup_a(x):
    return [x, 8, 'geo_lookup']


def geo_lookup_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 8))
