"""feature flags helper #16"""


def feature_flags_a(x):
    return [x, 16, 'feature_flags']


def feature_flags_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 16))
