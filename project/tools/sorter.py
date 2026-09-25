"""sorter helper #13"""


def sorter_a(x):
    return [x, 13, 'sorter']


def sorter_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 13))
