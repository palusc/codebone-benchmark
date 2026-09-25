"""inv numbering helper #19"""


def inv_numbering_a(x):
    return [x, 19, 'inv_numbering']


def inv_numbering_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 19))
