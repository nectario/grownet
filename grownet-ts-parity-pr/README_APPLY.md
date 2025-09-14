# GrowNet TypeScript Parity PR (bundle)

This bundle contains a ready-to-apply set of patches and new tests to bring the
TypeScript package (`src/typescript/grownet-ts`) to parity with the project contract.

## What this PR does
- Fixes spatial metrics (bbox was updated for all pixels; now only for active pixels > 0).
- Counts total synapses across the region (previously reported 0).
- Wires **automatic neuron growth** (fallback-streak + cooldown, one growth per layer per tick).
- Accepts `percentAtCapFallbackThreshold` alias in growth policy for cross-language consistency.
- Fixes PAL/index re-exports.
- Adds `types` field to `package.json`.
- Adds NodeNext ESM-friendly ESLint config to avoid false positives on `.js` imports from TS.
- Removes trailing duplicate imports in tests (if present).
- Adds new tests for auto-growth and spatial metrics parity.

## How to apply

1) From the repo root, back up the TS package just in case:
   cp -r src/typescript/grownet-ts src/typescript/grownet-ts.backup

2) Review and apply the patches (they use fuzzy context and should apply cleanly):
   git apply -p0 patches/region_metrics.patch || echo "Manual merge may be required"
   git apply -p0 patches/layer_autogrowth.patch || echo "Manual merge may be required"
   git apply -p0 patches/index_barrel.patch || echo "Manual merge may be required"
   git apply -p0 patches/package_json_types.patch || echo "Manual merge may be required"
   git apply -p0 patches/tests_cleanup.patch || echo "Manual merge may be required"

   # If `git apply` fails for any file, open the corresponding patch and integrate the
   # change manually (search anchors are provided).

3) Add new files (ESLint config + tests):
   cp new_files/.eslintrc.cjs src/typescript/grownet-ts/.eslintrc.cjs
   mkdir -p src/typescript/grownet-ts/tests
   cp new_files/tests/AutoGrowth.test.ts src/typescript/grownet-ts/tests/AutoGrowth.test.ts
   cp new_files/tests/SpatialMetricsParity.test.ts src/typescript/grownet-ts/tests/SpatialMetricsParity.test.ts

4) Install and run the TypeScript package:
   pushd src/typescript/grownet-ts
   npm ci
   npm run typecheck
   npm run lint
   npm test
   popd

5) Commit all changes and open the PR:
   git checkout -b feat/ts-parity-autogrowth-spatial-metrics
   git add -A
   git commit -m "ts: parity — auto neuron growth + spatial metrics fix + policy alias + types + tests"
   git push -u origin feat/ts-parity-autogrowth-spatial-metrics

## Notes

- If the TypeScript package lives at a different path, adjust `-p0` or the patch paths.
- The auto-growth logic only triggers one neuron growth per **layer** per **tick**.
- The spatial metrics fix updates bbox only when the pixel is active (value > 0) and
  reports real synapse counts by summing outgoing edges.
