from itertools import count

_ids = count(1000)


def new_id(prefix):
    return f"{prefix}_{next(_ids)}"
