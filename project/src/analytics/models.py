TABLE = "metric_points"


def new_metric(entity_id, **fields):
    return {"id": entity_id, "kind": "metric", **fields}
