"""reset mail tpl helper #5"""


def reset_mail_tpl_a(x):
    return [x, 5, 'reset_mail_tpl']


def reset_mail_tpl_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 5))
