from math_utils import MathUtils

fn check(cond: Bool, msg: String):
    if not cond: raise Error("Test failed: " + msg)

fn approx(a: Float64, b: Float64, eps: Float64 = 1e-9) -> Bool:
    return abs(a - b) <= eps

fn test_smooth_clamp_basic():
    let lo: Float64 = 0.0
    let hi: Float64 = 10.0
    let s:  Float64 = 2.0

    check(MathUtils.smooth_clamp(-5.0, lo, hi, s) == lo, "below lo clamps to lo")
    check(MathUtils.smooth_clamp(15.0, lo, hi, s) == hi, "above hi clamps to hi")

    # Middle passes through
    check(approx(MathUtils.smooth_clamp(5.0, lo, hi, s), 5.0), "middle passes through")

    # Edge limits
    check(MathUtils.smooth_clamp(lo, lo, hi, s) == lo, "at lo equals lo")
    check(MathUtils.smooth_clamp(hi, lo, hi, s) == hi, "at hi equals hi")

fn main():
    test_smooth_clamp_basic()
    print("[MOJO] math_utils_test passed.")

