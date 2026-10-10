def sync_customer_to_crm(event):
    return {"external_id": event["payload"]["customer_id"], "synced": True}
