import math

def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value

def smooth_clamp(x: float, lo: float, hi: float, soft: float | None = None) -> float:
    """
    Smoothly clamp x into [lo, hi] using cubic Hermite easing bands of width `soft`
    near each edge. Semantics match Mojo's MathUtils.smooth_clamp:
      - x <= lo                  → lo
      - lo < x < lo+soft         → lo + soft * h(t),   t = (x - lo)/soft
      - lo+soft <= x <= hi-soft  → x (pass-through)
      - hi-soft < x < hi         → hi - soft * h(t),   t = (hi - x)/soft
      - x >= hi                  → hi
    h(t) = t^2 (3 - 2t).
    If soft is None or <= 0 → 10% of range, capped at half-range.
    """
    if hi <= lo:
        return lo
    rng = hi - lo
    s = (0.1 * rng) if (soft is None or soft <= 0.0) else float(soft)
    if 2.0 * s > rng:
        s = 0.5 * rng

    if x <= lo:
        return lo
    if x >= hi:
        return hi
    if s <= 0.0:
        return x

    if x < (lo + s):
        t = (x - lo) / s
        h = t * t * (3.0 - 2.0 * t)
        return lo + s * h
    if x > (hi - s):
        t = (hi - x) / s
        h = t * t * (3.0 - 2.0 * t)
        return hi - s * h
    return x
