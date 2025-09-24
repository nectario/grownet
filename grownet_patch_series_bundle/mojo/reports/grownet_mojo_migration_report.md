# GrowNet Mojo Migration Report (0.25.x copyability & syntax)

Date: 2025-09-24T02:13:03.815358

## Changes applied

- mojo: replace 'let' with 'var' in pal/pal.mojo
- mojo: explicit copy of 2D frame in compute_spatial_metrics
- mojo: explicit copy of SlotConfig in try_grow_neuron()

### Files touched

  - b/src/mojo/pal/pal.mojo
  - a/src/mojo/pal/pal.mojo
  - b/src/mojo/region.mojo
  - a/src/mojo/region.mojo
  - a/src/mojo/layer.mojo
  - b/src/mojo/layer.mojo

## Additional findings / manual review suggestions

- Remaining `let` occurrences: 0
- Top-level `var` (globals): none found.
- Simple alias assignments from container-typed vars (potential implicit copy sites): 1
  - /mnt/data/GrowNet/src/mojo/region.mojo:152: `var chosen = img`   → consider `img.copy()` (we updated this one if still present).
- Iterator deref `[]` on loop variables: none found.
- Deprecated builtins (`alignof/sizeof/simdwidthof` etc): none found.