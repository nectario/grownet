import math

def clamp(value: float, min_value: float, max_value: float) -> float:
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value

def smooth_clamp(value: float, min_value: float, max_value: float, softness: float = 0.0) -> float:
    """
    Clamp with optional 'soft' knee near bounds.
    softness=0 -> hard clamp. For small softness (e.g., 0.01) transitions are smoother.
    """
    if softness <= 0.0:
        return clamp(value, min_value, max_value)
    # Soft knee: compress when moving past the bounds
    if value < min_value:
        return min_value + math.tanh((value - min_value) / softness) * softness
    if value > max_value:
        return max_value + math.tanh((value - max_value) / softness) * softness
    return value

def compute_percent_delta(current_value: float, previous_value: float) -> float:
    if previous_value == 0.0:
        return 0.0 if current_value == 0.0 else 100.0
    return abs(current_value - previous_value) / abs(previous_value) * 100.0
