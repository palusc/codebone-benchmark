from web import h_cust, h_inv, h_misc

ROUTES = {
    "GET /c": h_cust.get_c,
    "POST /c": h_cust.new_c,
    "POST /i": h_inv.mk_inv,
    "GET /ping": h_misc.ping,
}


def dispatch(method, path, body=None):
    return ROUTES[f"{method} {path}"](body or {})
