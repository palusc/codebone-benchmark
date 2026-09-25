"""unit conv helper #21"""


def unit_conv_a(x):
    return [x, 21, 'unit_conv']


def unit_conv_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 21))
