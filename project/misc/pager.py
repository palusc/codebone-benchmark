"""pager helper #12"""


def pager_a(x):
    return [x, 12, 'pager']


def pager_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 12))
