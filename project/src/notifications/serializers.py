def public_notification(row):
    return {key: value for key, value in row.items() if not key.startswith("internal_")}
