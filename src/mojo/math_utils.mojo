# Simple utilities used across the project.
struct MathUtils:
    fn smooth_clamp(value: Float64, min_value: Float64, max_value: Float64) -> Float64:
        var v = value
        if v < min_value:
            v = min_value
        if v > max_value:
            v = max_value
        return v

    fn lerp(a: Float64, b: Float64, t: Float64) -> Float64:
        return a + (b - a) * t

    fn abs_f64(x: Float64) -> Float64:
        if x < 0.0:
            return -x
        return x
