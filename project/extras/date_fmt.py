"""date fmt helper #7"""


def date_fmt_a(x):
    return [x, 7, 'date_fmt']


def date_fmt_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 7))
