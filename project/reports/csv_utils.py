"""csv utils helper #6"""


def csv_utils_a(x):
    return [x, 6, 'csv_utils']


def csv_utils_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 6))
