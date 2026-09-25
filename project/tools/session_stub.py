"""session stub helper #25"""


def session_stub_a(x):
    return [x, 25, 'session_stub']


def session_stub_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 25))
