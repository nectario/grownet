# Simple utilities used across the project.
struct MathUtils:
    fn smooth_clamp(value: Float64, min_value: Float64, max_value: Float64) -> Float64:
        var val = value
        if val < min_value:
            val = min_value
        if val > max_value:
            val = max_value
        return val

    fn lerp(a: Float64, b: Float64, t: Float64) -> Float64:
        return a + (b - a) * t

    fn abs_f64(x: Float64) -> Float64:
        if x < 0.0:
            return -x
        return x
