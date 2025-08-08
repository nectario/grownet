# math_utils.mojo
# Simple helpers used across GrowNet (Mojo reference implementation).

alias ONE: Float64 = 1.0
alias ZERO: Float64 = 0.0

fn abs_f64(x: Float64) -> Float64:
    if x >= 0.0:
        return x
    else:
        return -x

fn smooth_clamp(x: Float64, lo: Float64, hi: Float64) -> Float64:
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x

fn round_one_decimal(x: Float64) -> Float64:
    # Round to 1 decimal place without importing math modules.
    var scaled = x * 10.0
    if scaled >= 0.0:
        var i = Int64(scaled + 0.5)
        return Float64(i) / 10.0
    else:
        var i = Int64(scaled - 0.5)
        return Float64(i) / 10.0

fn percent_delta(previous: Float64, new_value: Float64) -> Float64:
    # Handle first time gracefully.
    if previous == 0.0:
        return 0.0
    return abs_f64(new_value - previous) / abs_f64(previous)

fn pseudo_random_pair(i: Int64, j: Int64) -> Float64:
    # Deterministic pseudo-random in [0,1) based on two integers.
    # Avoids external RNG imports to keep Mojo code portable.
    var x = (i * 1103515245 + j * 12345) % 2147483647
    if x < 0:
        x = -x
    return Float64(x) / 2147483647.0
