from utils import calc2


def row_for(inv):
    net = calc2.net(inv["items"])
    gross = net * 1.19
    return {"id": inv["id"], "net": round(net, 2), "gross": round(gross, 2)}


def to_csv(invs):
    lines = ["id,net,gross"]
    for inv in invs:
        r = row_for(inv)
        lines.append(f'{r["id"]},{r["net"]},{r["gross"]}')
    return "\n".join(lines)
