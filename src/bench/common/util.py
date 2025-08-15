def percentile(values, pct):
    if not values:
        return None
    xs = sorted(values)
    k = int(round((pct/100.0) * (len(xs)-1)))
    return xs[max(0, min(k, len(xs)-1))]
