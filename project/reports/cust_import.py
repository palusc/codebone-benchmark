"""cust import helper #18"""


def cust_import_a(x):
    return [x, 18, 'cust_import']


def cust_import_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 18))
