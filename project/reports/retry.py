"""retry helper #10"""


def retry_a(x):
    return [x, 10, 'retry']


def retry_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 10))
