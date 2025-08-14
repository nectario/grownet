# math_utils.mojo — small helpers kept explicit and readable

alias ONE:  F64 = 1.0
alias ZERO: F64 = 0.0

fn abs_val(x: F64) -> F64:
    return x if x >= 0.0 else -x

fn min_val(a: F64, b: F64) -> F64:
    return a if a <= b else b

fn max_val(a: F64, b: F64) -> F64:
    return a if a >= b else b

fn smooth_clamp(x: F64, low: F64, high: F64) -> F64:
    # clamp with gentle edges (readability > terseness)
    let lo = min_val(x, high)
    let hi = max_val(lo, low)
    return hi

fn round_one_decimal(x: F64) -> F64:
    # e.g., 0.27 → 0.3
    let scaled = x * 10.0
    let n = Int64(scaled)
    let frac = scaled - F64(n)
    let half_up = n + (1 if frac >= 0.5 else 0)
    return F64(half_up) / 10.0

fn floor_int(x: F64) -> Int64:
    let i = Int64(x)
    if F64(i) > x:
        return i - 1
    return i
