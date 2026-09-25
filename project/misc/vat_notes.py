"""vat notes helper #4"""


def vat_notes_a(x):
    return [x, 4, 'vat_notes']


def vat_notes_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 4))
