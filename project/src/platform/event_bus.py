from copy import deepcopy

EVENTS = []


def publish(topic, payload):
    EVENTS.append({"topic": topic, "payload": deepcopy(payload)})


def reset():
    EVENTS.clear()


def published(topic=None):
    rows = EVENTS if topic is None else [e for e in EVENTS if e["topic"] == topic]
    return deepcopy(rows)
