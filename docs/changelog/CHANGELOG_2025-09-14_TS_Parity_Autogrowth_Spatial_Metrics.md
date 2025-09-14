# 2025-09-14 — TypeScript parity: auto-growth, spatial metrics, policy alias, PAL/export polish, tests

Scope: `src/typescript/grownet-ts`

## Summary

This change brings the TypeScript package to functional parity on several core behaviors:

- Automatic neuron growth (fallback-streak + cooldown) with a one-growth-per-layer-per-tick guard.
- Spatial metrics correctness: bbox/centroid computed over active pixels only; synapse counting now reflects real outgoing edges.
- GrowthPolicy naming parity: accept `percentAtCapFallbackThreshold` alias.
- PAL/export hygiene and package types.
- Additional tests to validate behavior.

## Details

### Auto neuron growth (Layer.endTick)
- Triggers growth when, for a neuron:
  - slot capacity is reached (strict capacity), and
  - `lastSlotUsedFallback == true`, and
  - `fallbackStreak >= fallbackGrowthThreshold`, and
  - cooldown satisfied: `bus.currentStep - lastGrowthTick >= neuronGrowthCooldownTicks`.
- Only one neuron may grow per layer per tick.
- Newly grown neuron is auto-wired via existing mesh rules and re-attached to windowed tracts.

### Spatial metrics parity
- BBox min/max indices are updated only for pixels with `value > 0`.
- `totalSynapses` is the sum of outgoing edges across the region (preferring `getOutgoingCount()`, falling back to `getOutgoing().length`).

### GrowthPolicy alias
- `Region.setGrowthPolicy(...)` now accepts `percentAtCapFallbackThreshold` and maps it to `percentNeuronsAtCapacityThreshold` when the latter is omitted.

### PAL/export/package
- Barrel exports align with NodeNext ESM usage.
- Package now exposes TypeScript types via `"types": "dist/index.d.ts"`.
- Added ESM-friendly `.eslintrc.cjs` to eliminate false positives on `.js` import suffixes from TS code.

## Tests added
- `tests/AutoGrowth.test.ts` — drives fallback → growth; asserts at most one growth per layer per tick.
- `tests/SpatialMetricsParity.test.ts` — ensures bbox uses only active pixels; asserts `totalSynapses > 0` after wiring.

## Rationale

These changes complete key parity items for the TypeScript runtime: correct spatial metrics, automatic neuron growth, consistent policy knobs, and robust export/ESM ergonomics. The behavior matches Python/Java/C++/Mojo where applicable, with deterministic growth and autowiring semantics.

## Notes and follow-ups

- Proximity policy (STEP) remains a follow-up for TS (parity with other languages). A separate PR will implement once-per-step guard, per-source cooldown, budget, and deterministic layout/hash.
- CI enforces no single-/double-character identifiers; code has been conformed across the new/changed TS sources.

