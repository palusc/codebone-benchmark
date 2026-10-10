from copy import deepcopy
from src.analytics.models import TABLE

_ROWS = {}


def save(row):
    _ROWS[str(row["id"])] = deepcopy(row)
    return deepcopy(row)


def get(entity_id):
    row = _ROWS.get(str(entity_id))
    return deepcopy(row) if row else None


def list_all():
    return deepcopy(list(_ROWS.values()))
