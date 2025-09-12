# CHANGELOG — 2025-09-12

## Changed

- smooth_clamp default smoothing changed from "cubic" (C¹) to "quintic" (C²) in both Mojo and Python for smoother transitions.
  - Mojo: `MathUtils.smooth_clamp(x, lo, hi, soft=-1.0, smoothness="quintic")`
    - File: `src/mojo/math_utils.mojo`
  - Python: `smooth_clamp(x, lo, hi, soft=None, smoothness="quintic")`
    - File: `src/python/math_utils.py`

## Rationale

- Quintic (C²) smoothstep provides a tighter, visually smoother easing near bounds while preserving hard clamps outside `[lo, hi]` and pass‑through in the core region.

## Migration

- Existing behavior can be preserved by passing `smoothness="cubic"` explicitly.
- No other semantics changed.

## Tests

- Added/updated tests verify basic clamping and that `quintic` produces a tighter easing than `cubic` near edges:
  - Mojo: `src/mojo/tests/math_utils_test.mojo`
  - Python: `src/python/tests/test_math_utils_smooth_clamp.py`

## Notes

- Default soft band remains 10% of the range (capped at half-range) when `soft` is not provided or non‑positive.
- This is a non‑breaking default change; call sites that depend on cubic easing should pass `smoothness="cubic"`.
