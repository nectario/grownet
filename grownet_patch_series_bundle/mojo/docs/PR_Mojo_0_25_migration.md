# PR: Mojo 0.25.x Migration (copy model & minor syntax)

**Summary.** Adopt explicit `.copy()` for containers and config structs; replace deprecated `let` with `var` in PAL; keep semantics unchanged.

## Changes
- Mojo PAL: replace `let` with `var` in `pal/pal.mojo` (language deprecation).
- Region metrics: use `img.copy()` instead of aliasing in `compute_spatial_metrics`.
- Growth path: when growing a neuron, copy the `SlotConfig` explicitly before assigning to the new neuron.

## Rationale
- Aligns with Mojo 0.25.x copy model (explicit copies; implicit for containers is warning → error).
- Keeps GrowNet's determinism and clarity (no accidental aliasing).

## Tests
- Added `src/mojo/tests/copyability_test.mojo` and `src/mojo/tests/iterator_contract_test.mojo`.

## Notes
- No global `var` at file scope existed; no changes needed.
- No deprecated builtins (`alignof/sizeof/simdwidthof`) were found in the Mojo tree.
