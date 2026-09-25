"""money stuff"""
VAT = 0.19


def net(items):
    return sum(i["price"] * i["qty"] for i in items)


def tot(items):
    return round(net(items) * (1 + VAT), 2)
