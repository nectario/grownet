from math_utils import smooth_clamp


def test_smooth_clamp_basic():
    lo, hi, s = 0.0, 10.0, 2.0
    assert smooth_clamp(-5.0, lo, hi, s) == lo
    assert smooth_clamp(15.0, lo, hi, s) == hi
    assert abs(smooth_clamp(5.0, lo, hi, s) - 5.0) < 1e-12
    assert smooth_clamp(lo, lo, hi, s) == lo
    assert smooth_clamp(hi, lo, hi, s) == hi


def test_smooth_clamp_default_soft():
    # Should pick ~10% of range and cap at half-range if needed
    lo, hi = 0.0, 10.0
    y = smooth_clamp(1.0, lo, hi, None)  # near lo; should be > lo and < 1.0
    assert lo < y < 1.0

