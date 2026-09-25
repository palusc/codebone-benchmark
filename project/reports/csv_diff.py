"""csv diff helper #26"""


def csv_diff_a(x):
    return [x, 26, 'csv_diff']


def csv_diff_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 26))
