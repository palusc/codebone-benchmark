"""metrics stub helper #24"""


def metrics_stub_a(x):
    return [x, 24, 'metrics_stub']


def metrics_stub_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 24))
