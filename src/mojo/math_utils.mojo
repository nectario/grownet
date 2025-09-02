# Simple utilities used across the project.
struct MathUtils:
    fn smooth_clamp(value: Float64, min_value: Float64, max_value: Float64) -> Float64:
        var val = value
        if val < min_value:
            val = min_value
        if val > max_value:
            val = max_value
        return val

    fn lerp(start: Float64, end: Float64, weight: Float64) -> Float64:
        return start + (end - start) * weight

    fn abs_f64(value: Float64) -> Float64:
        if value < 0.0:
            return -value
        return value
