"""cust export notes helper #3"""


def cust_export_notes_a(x):
    return [x, 3, 'cust_export_notes']


def cust_export_notes_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 3))
