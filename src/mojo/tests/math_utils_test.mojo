from math_utils import MathUtils

fn check(cond: Bool, msg: String):
    if not cond: raise Error("Test failed: " + msg)

fn approx(a: Float64, b: Float64, eps: Float64 = 1e-9) -> Bool:
    return abs(a - b) <= eps

fn test_smooth_clamp_basic():
    let lower_bound: Float64 = 0.0
    let upper_bound: Float64 = 10.0
    let soft_width:  Float64 = 2.0

    check(MathUtils.smooth_clamp(-5.0, lower_bound, upper_bound, soft_width) == lower_bound, "below lo clamps to lo")
    check(MathUtils.smooth_clamp(15.0, lower_bound, upper_bound, soft_width) == upper_bound, "above hi clamps to hi")

    # Middle passes through
    check(approx(MathUtils.smooth_clamp(5.0, lower_bound, upper_bound, soft_width), 5.0), "middle passes through")

    # Edge limits
    check(MathUtils.smooth_clamp(lower_bound, lower_bound, upper_bound, soft_width) == lower_bound, "at lo equals lo")
    check(MathUtils.smooth_clamp(upper_bound, lower_bound, upper_bound, soft_width) == upper_bound, "at hi equals hi")

fn test_smooth_clamp_quintic_vs_cubic():
    let lower_bound2: Float64 = 0.0
    let upper_bound2: Float64 = 10.0
    let soft_width2:  Float64 = 2.0
    # pick a point in lower band with t=0.25 → x = lo + 0.25*soft = 0.5
    let sample_value  : Float64 = lower_bound2 + 0.25 * soft_width2
    let cubic_value : Float64 = MathUtils.smooth_clamp(sample_value, lower_bound2, upper_bound2, soft_width2, "cubic")
    let quintic_value : Float64 = MathUtils.smooth_clamp(sample_value, lower_bound2, upper_bound2, soft_width2, "quintic")
    # quintic is tighter near edges → yq < yc for t=0.25
    check(quintic_value < cubic_value, "quintic < cubic near edge")

fn main():
    test_smooth_clamp_basic()
    test_smooth_clamp_quintic_vs_cubic()
    print("[MOJO] math_utils_test passed.")
