"""color utils helper #28"""


def color_utils_a(x):
    return [x, 28, 'color_utils']


def color_utils_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 28))
