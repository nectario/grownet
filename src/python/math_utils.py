from __future__ import annotations

def smooth_clamp(x: float, low: float, high: float) -> float:
    if x < low:
        return low
    if x > high:
        return high
    return x

def round_one_decimal(x: float) -> float:
    # e.g., 0.27 -> 0.3; 0.24 -> 0.2
    return round(x * 10.0) / 10.0
