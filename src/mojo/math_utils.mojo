# Smooth‑step helpers ported from C++ prototype
# C++ reference: math_utils.cpp :contentReference[oaicite:1]{index=1}

from math import clamp

fn smoothstep(edge0: F64, edge1: F64, x: F64) -> F64:
    let t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

fn smooth_clamp(x: F64, lo: F64, hi: F64) -> F64:
    return smoothstep(0.0, 1.0, (x - lo) / (hi - lo)) * (hi - lo) + lo

fn round_two(x: F64) -> F64:
    if x == 0.0: return 0.0
    return (round(x * 10.0)) / 10.0


