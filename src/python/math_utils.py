import math

def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value

def smooth_clamp(value, low, high, k=0.5):
    # simple smooth step toward bounds; k in (0,1]
    value = clamp(value, low - 1e6, high + 1e6)
    span = high - low
    if span <= 0:
        return low
    t_ratio = (value - low) / span
    t_ratio = clamp(t_ratio, 0.0, 1.0)
    # cubic smoothstep
    t_ratio = t_ratio * t_ratio * (3.0 - 2.0 * t_ratio)
    return low + t_ratio * span
