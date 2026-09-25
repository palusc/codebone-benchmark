def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def chunks(seq, n):
    return [seq[i:i + n] for i in range(0, len(seq), n)]
