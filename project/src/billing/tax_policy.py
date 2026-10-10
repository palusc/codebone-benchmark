from decimal import Decimal, ROUND_HALF_UP

STANDARD_VAT = Decimal("0.19")


def vat_for(net, rate=STANDARD_VAT):
    return (Decimal(str(net)) * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def gross_for(net, rate=STANDARD_VAT):
    amount = Decimal(str(net))
    return (amount + vat_for(amount, rate)).quantize(Decimal("0.01"))
