"""id gen helper #29"""


def id_gen_a(x):
    return [x, 29, 'id_gen']


def id_gen_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 29))
