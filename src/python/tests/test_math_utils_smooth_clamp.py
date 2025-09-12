from math_utils import smooth_clamp


def test_smooth_clamp_basic():
    lower_bound, upper_bound, soft_width = 0.0, 10.0, 2.0
    assert smooth_clamp(-5.0, lower_bound, upper_bound, soft_width) == lower_bound
    assert smooth_clamp(15.0, lower_bound, upper_bound, soft_width) == upper_bound
    assert abs(smooth_clamp(5.0, lower_bound, upper_bound, soft_width) - 5.0) < 1e-12
    assert smooth_clamp(lower_bound, lower_bound, upper_bound, soft_width) == lower_bound
    assert smooth_clamp(upper_bound, lower_bound, upper_bound, soft_width) == upper_bound


def test_smooth_clamp_default_soft():
    # Should pick ~10% of range and cap at half-range if needed
    lower_bound, upper_bound = 0.0, 10.0
    y_val = smooth_clamp(1.0, lower_bound, upper_bound, None)  # near lo; should be > lo and < 1.0
    assert lower_bound < y_val < 1.0

def test_smooth_clamp_quintic_vs_cubic():
    lower_bound, upper_bound, soft_width = 0.0, 10.0, 2.0
    sample_value = lower_bound + 0.25 * soft_width  # t=0.25 in lower band
    cubic_value = smooth_clamp(sample_value, lower_bound, upper_bound, soft_width, smoothness="cubic")
    quintic_value = smooth_clamp(sample_value, lower_bound, upper_bound, soft_width, smoothness="quintic")
    assert quintic_value < cubic_value
