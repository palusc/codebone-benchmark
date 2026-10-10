from copy import deepcopy

TABLES = {
    "customers": {},
    "invoices": {},
    "credit_notes": {},
    "ledger_entries": [],
    "claimed_webhooks": set(),
}


def reset():
    TABLES["customers"].clear()
    TABLES["invoices"].clear()
    TABLES["credit_notes"].clear()
    TABLES["ledger_entries"].clear()
    TABLES["claimed_webhooks"].clear()


def put(table, key, value):
    TABLES[table][str(key)] = deepcopy(value)
    return deepcopy(value)


def get(table, key):
    value = TABLES[table].get(str(key))
    return deepcopy(value) if value is not None else None


def append(table, value):
    TABLES[table].append(deepcopy(value))
    return deepcopy(value)


def all_rows(table):
    rows = TABLES[table]
    return deepcopy(list(rows.values()) if isinstance(rows, dict) else rows)
