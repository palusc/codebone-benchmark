def slug(s):
    return "-".join(s.lower().split())


def trunc(s, n=40):
    return s if len(s) <= n else s[: n - 1] + "~"
