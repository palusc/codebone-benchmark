"""queue stub helper #22"""


def queue_stub_a(x):
    return [x, 22, 'queue_stub']


def queue_stub_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 22))
