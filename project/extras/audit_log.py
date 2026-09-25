"""audit log helper #15"""


def audit_log_a(x):
    return [x, 15, 'audit_log']


def audit_log_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 15))
