from math import clamp

fn smooth_step(edge_start: Float64, edge_end: Float64, value: Float64) -> Float64:
    var t = clamp((value - edge_start) / (edge_end - edge_start), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

fn smooth_clamp(value: Float64, lower: Float64, upper: Float64) -> Float64:
    return smooth_step(0.0, 1.0, (value - lower) / (upper - lower)) * (upper - lower) + lower

fn round_one_decimal(value: Float64) -> Float64:
    if value == 0.0:
        return 0.0
    return (round(value * 10.0)) / 10.0
