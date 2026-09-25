"""text wrap helper #27"""


def text_wrap_a(x):
    return [x, 27, 'text_wrap']


def text_wrap_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 27))
