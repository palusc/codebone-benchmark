from src.platform import memory_db


def claim_webhook(event_id):
    claimed = memory_db.TABLES["claimed_webhooks"]
    if event_id in claimed:
        return False
    claimed.add(event_id)
    return True


def add_entry(entry):
    return memory_db.append("ledger_entries", entry)


def entries():
    return memory_db.all_rows("ledger_entries")
