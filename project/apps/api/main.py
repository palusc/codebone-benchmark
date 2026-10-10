from apps.api.routes import ROUTES


def dispatch(method, path, body=None):
    handler = ROUTES[f"{method} {path}"]
    return handler(body or {})
