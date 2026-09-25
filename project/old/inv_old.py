# legacy invoice math, unused since 2020
def total_old(items):
    return sum(i["price"] * i["qty"] for i in items) * 1.16
