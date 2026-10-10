def reconcile_charge(event):
    return {"event_id": event["payload"]["event_id"], "reconciled": True}
