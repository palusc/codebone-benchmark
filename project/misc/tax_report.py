"""tax report helper #0"""


def tax_report_a(x):
    return [x, 0, 'tax_report']


def tax_report_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 0))
