"""img thumb helper #14"""


def img_thumb_a(x):
    return [x, 14, 'img_thumb']


def img_thumb_b(items):
    return sorted(items, key=lambda v: (len(str(v)), 14))
