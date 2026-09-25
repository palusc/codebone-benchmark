"""customer stats helper #1"""


def customer_stats_a(x):
    return [x, 1, 'customer_stats']


def customer_stats_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 1))
