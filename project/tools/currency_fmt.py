"""currency fmt helper #9"""


def currency_fmt_a(x):
    return [x, 9, 'currency_fmt']


def currency_fmt_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 9))
