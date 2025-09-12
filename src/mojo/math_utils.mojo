# Simple utilities used across the project.
struct MathUtils:
    """
    Smoothly clamp x into [lo, hi] using easing bands of width `soft`
    near each edge. Choose easing via `smoothness`:
      - "cubic"   → h(t) = t² (3 − 2t)          (C¹ continuous)
      - "quintic" → h(t) = t³ (10 − 15t + 6t²)  (C² continuous)

    The function is:
      - x <= lo                  → lo
      - lo < x < lo+soft         → lo + soft * h((x - lo)/soft)
      - lo+soft <= x <= hi-soft  → x  (pass-through)
      - hi-soft < x < hi         → hi - soft * h((hi - x)/soft)
      - x >= hi                  → hi
    h is cubic or quintic per 'smoothness' (case-insensitive).

    If `soft <= 0` we pick a default soft band = 10% of the range (capped to half-range).
    If 2*soft > (hi - lo) we reduce soft to half the range, leaving no linear core.
    """
    fn smooth_clamp(x: Float64, lo: Float64, hi: Float64, soft: Float64 = -1.0, smoothness: String = "cubic") -> Float64:
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

        # choose easing function h(t)
        fn h_cubic(t: Float64) -> Float64:
            return t * t * (3.0 - 2.0 * t)
        fn h_quintic(t: Float64) -> Float64:
            # t^3*(10 - 15t + 6t^2) == 6t^5 - 15t^4 + 10t^3
            return t * t * t * (10.0 - 15.0 * t + 6.0 * t * t)
        var is_quintic = (smoothness == "quintic") or (smoothness == "Quintic") or (smoothness == "QUINTIC")

        if x < (lo + s):
            let t = (x - lo) / s
            return lo + s * (if is_quintic { h_quintic(t) } else { h_cubic(t) })

        if x > (hi - s):
            let t = (hi - x) / s
            return hi - s * (if is_quintic { h_quintic(t) } else { h_cubic(t) })

        return x

    fn lerp(start: Float64, end: Float64, weight: Float64) -> Float64:
        return start + (end - start) * weight

    fn abs_f64(value: Float64) -> Float64:
        if value < 0.0:
            return -value
        return value
