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
    smoothness: str = "quintic",
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
    range_span = hi - lo
    soft_band = (0.1 * range_span) if (soft is None or soft <= 0.0) else float(soft)
    if 2.0 * soft_band > range_span:
        soft_band = 0.5 * range_span

    if x <= lo:
        return lo
    if x >= hi:
        return hi
    if soft_band <= 0.0:
        return x

    mode = str(smoothness or "cubic").lower()
    def h_cubic(param: float) -> float:
        return param * param * (3.0 - 2.0 * param)
    def h_quintic(param: float) -> float:
        return param * param * param * (10.0 - 15.0 * param + 6.0 * param * param)
    h = h_quintic if mode == "quintic" else h_cubic

    if x < (lo + soft_band):
        normalized_position = (x - lo) / soft_band
        return lo + soft_band * h(normalized_position)
    if x > (hi - soft_band):
        normalized_position_upper = (hi - x) / soft_band
        return hi - soft_band * h(normalized_position_upper)
    return x
