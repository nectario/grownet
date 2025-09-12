# Simple utilities used across the project.
struct MathUtils:
    """
    Smoothly clamp x into [lo, hi] using cubic Hermite easing in a soft band
    of width `soft` near each edge. The function is C¹ at band boundaries:
      - x <= lo                  → lo
      - lo < x < lo+soft         → lo + soft * h(t),   t = (x - lo)/soft
      - lo+soft <= x <= hi-soft  → x  (pass-through)
      - hi-soft < x < hi         → hi - soft * h(t),   t = (hi - x)/soft
      - x >= hi                  → hi
    where h(t) = t² (3 - 2t) is the smoothstep cubic.

    If `soft <= 0` we pick a default soft band = 10% of the range (capped to half-range).
    If 2*soft > (hi - lo) we reduce soft to half the range, leaving no linear core.
    """
    fn smooth_clamp(x: Float64, lo: Float64, hi: Float64, soft: Float64 = -1.0) -> Float64:
        if hi <= lo:
            return lo

        let rng = hi - lo
        var s = soft
        if s <= 0.0:
            s = 0.1 * rng
        if (2.0 * s) > rng:
            s = 0.5 * rng

        if x <= lo: return lo
        if x >= hi: return hi

        if s <= 0.0:
            return x

        if x < (lo + s):
            let t = (x - lo) / s
            let h = t * t * (3.0 - 2.0 * t)
            return lo + s * h

        if x > (hi - s):
            let t = (hi - x) / s
            let h = t * t * (3.0 - 2.0 * t)
            return hi - s * h

        return x

    fn lerp(start: Float64, end: Float64, weight: Float64) -> Float64:
        return start + (end - start) * weight

    fn abs_f64(value: Float64) -> Float64:
        if value < 0.0:
            return -value
        return value
