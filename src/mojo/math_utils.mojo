# math_utils.mojo
# Small helpers kept deliberately simple and explicit.

alias ONE: F64  = 1.0
alias ZERO: F64 = 0.0

fn abs_val(x: F64) -> F64:
    if x >= 0.0:
        return x
    return -x

fn min_val(a: F64, b: F64) -> F64:
    if a <= b:
        return a
    return b

fn max_val(a: F64, b: F64) -> F64:
    if a >= b:
        return a
    return b

fn smooth_clamp(x: F64, low: F64, high: F64) -> F64:
    let clamped = max_val(low, min_val(x, high))
    return clamped

# Round to one decimal place (0.27 -> 0.3; -0.27 -> -0.3), half-away-from-zero.
fn round_one_decimal(x: F64) -> F64:
    let scaled: F64 = x * 10.0
    let adj: F64 = -0.5 if scaled < 0.0 else 0.5
    let res: F64 = scaled + adj
    return F64(res) / 10.0

# Simple floor that works well for positive/negative numbers.
fn floor_to_int(x: F64) -> Int64:
    var i: Int64 = Int64(x)
    if F64(i) > x:
        return i - 1
    return i

# Percent delta helper (returns 0.0 if previous == 0)
fn percent_delta(previous: F64, current: F64) -> F64:
    if previous == 0.0:
        return 0.0
    return abs_val(current - previous) / abs_val(previous) * 100.0
