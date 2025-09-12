import math

def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value

def smooth_clamp(
    x: float,
    lo: float,
    hi: float,
    soft: float | None = None,
    smoothness: str = "cubic",
) -> float:
    """
    Smoothly clamp x into [lo, hi] using cubic Hermite easing bands of width `soft`
    near each edge. Semantics match Mojo's MathUtils.smooth_clamp:
      - x <= lo                  → lo
      - lo < x < lo+soft         → lo + soft * h(t),   t = (x - lo)/soft
      - lo+soft <= x <= hi-soft  → x (pass-through)
      - hi-soft < x < hi         → hi - soft * h(t),   t = (hi - x)/soft
      - x >= hi                  → hi
    h(t) is cubic (C¹) or quintic (C²) per `smoothness="cubic"|"quintic"` (case-insensitive).
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

    m = str(smoothness or "cubic").lower()
    def h_cubic(t: float) -> float:
        return t * t * (3.0 - 2.0 * t)
    def h_quintic(t: float) -> float:
        return t * t * t * (10.0 - 15.0 * t + 6.0 * t * t)
    h = h_quintic if m == "quintic" else h_cubic

    if x < (lo + s):
        t = (x - lo) / s
        return lo + s * h(t)
    if x > (hi - s):
        t = (hi - x) / s
        return hi - s * h(t)
    return x
