from math import isclose

def smooth_step(edge_start: float, edge_end: float, value: float) -> float:
    """Cubic Hermite smoothstep for gentle transitions."""
    if isclose(edge_end, edge_start):
        return 0.0
    t = (value - edge_start) / (edge_end - edge_start)
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return t * t * (3.0 - 2.0 * t)

def smooth_clamp(value: float, lower: float, upper: float) -> float:
    """Clamp with smooth edges to avoid hard saturation kinks."""
    return smooth_step(0.0, 1.0, (value - lower) / (upper - lower)) * (upper - lower) + lower
