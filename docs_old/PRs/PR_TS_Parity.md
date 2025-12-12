Here’s a complete **PR you can drop into the repo** to bring the TypeScript package to parity with the rest of GrowNet. It fixes the functional gaps we discussed, adds tests, and includes a ready‑to‑apply patch bundle.

**The zip file referenced here has been extracted to: ./grownet-ts-parity-pr**

------

## PR title

**ts: parity — auto neuron growth + spatial metrics fix + policy alias + PAL/export polish + tests**

## What this PR addresses (everything from the review)

1. **Spatial metrics bug fix**
   - **Fix:** Bounding box (`rowMin/rowMax/colMin/colMax`) now updates **only for active pixels** (`value > 0`), not every pixel.
   - **Add:** `totalSynapses` is no longer hardcoded; it now **sums outgoing edge counts** across all neurons in all layers (robust to either `getOutgoingCount()` or `getOutgoing().length`).
2. **Automatic neuron growth (fallback‑streak + cooldown)**
   - **Implement:** Growth trigger in `Layer.endTick()` that grows **one neuron per layer per tick** when:
     - the neuron is at **strict capacity**,
     - the **last slot used** was a **fallback**,
     - **fallback streak** ≥ `fallbackGrowthThreshold`, and
     - **cooldown** satisfied (`neuronGrowthCooldownTicks`).
   - **Parity:** New neuron is same kind; deterministic autowiring is already handled via your mesh rules/tracts.
3. **GrowthPolicy naming parity**
   - **Add:** Accept **`percentAtCapFallbackThreshold`** (the wording used in the cross‑language spec) as an alias for the canonical TS field `percentNeuronsAtCapacityThreshold`. Prevents confusion when porting configs.
4. **PAL/export polish**
   - **Fix:** `src/index.ts` now re‑exports the PAL surface from `./pal/index.js` explicitly (consistent ESM barrel).
5. **Package hygiene**
   - **Add:** `"types": "dist/index.d.ts"` to `package.json` for proper TypeScript consumer DX.
   - **Add:** ESM‑friendly `.eslintrc.cjs` (NodeNext + `.js` import suffixes from `.ts` sources), avoiding false positives in CI.
6. **Tests**
   - **New:** `AutoGrowth.test.ts` — drives fallback → growth and asserts >1 neuron in the layer while enforcing “one growth per layer per tick”.
   - **New:** `SpatialMetricsParity.test.ts` — ensures bbox is computed over **positive** pixels only and that `totalSynapses` is **> 0** after a connection.
   - **Cleanup:** Removes stray duplicate imports from two test files if they exist (non‑blocking; the patch is fuzzy).

> **Intentionally \*not\* included here:** a full TS proximity policy engine. I kept this PR tight and risk‑free; if you want, I can follow up with STEP‑mode proximity (once‑per‑step guard, per‑source cooldown, budget, deterministic layout/hash) in a separate PR.

------

## How to apply (step‑by‑step)

1. **Unzip** the bundle anywhere and read the short instructions:

```
unzip grownet-ts-parity-pr.zip
cat grownet-ts-parity-pr/README_APPLY.md
```

1. **From the repo root**, apply patches (they use fuzzy context and will usually apply cleanly):

```bash
git apply -p0 grownet-ts-parity-pr/patches/region_metrics.patch || echo "manual merge may be required"
git apply -p0 grownet-ts-parity-pr/patches/layer_autogrowth.patch || echo "manual merge may be required"
git apply -p0 grownet-ts-parity-pr/patches/region_policy_alias.patch || echo "manual merge may be required"
git apply -p0 grownet-ts-parity-pr/patches/index_barrel.patch || echo "manual merge may be required"
git apply -p0 grownet-ts-parity-pr/patches/package_json_types.patch || echo "manual merge may be required"
git apply -p0 grownet-ts-parity-pr/patches/tests_cleanup.patch || echo "manual merge may be required"
```

1. **Add the new files**:

```bash
cp grownet-ts-parity-pr/new_files/.eslintrc.cjs src/typescript/grownet-ts/.eslintrc.cjs
mkdir -p src/typescript/grownet-ts/tests
cp grownet-ts-parity-pr/new_files/tests/AutoGrowth.test.ts src/typescript/grownet-ts/tests/AutoGrowth.test.ts
cp grownet-ts-parity-pr/new_files/tests/SpatialMetricsParity.test.ts src/typescript/grownet-ts/tests/SpatialMetricsParity.test.ts
```

1. **Build and test the TS package**:

```bash
pushd src/typescript/grownet-ts
npm ci
npm run typecheck
npm run lint
npm test
popd
```

1. **Create the branch & commit**:

```bash
git checkout -b feat/ts-parity-autogrowth-spatial-metrics
git add -A
git commit -m "ts: parity — auto neuron growth + spatial metrics fix + policy alias + types + tests"
git push -u origin feat/ts-parity-autogrowth-spatial-metrics
```

------

## What changed (by file) — highlights

### `src/typescript/grownet-ts/src/Region.ts`

- **Spatial metrics fix:** bbox updated only when `value > 0`.
- **Synapse counting:** sums outgoing per neuron (`getOutgoingCount()` if available; else `getOutgoing().length`; else 0).
- **Policy alias:** `setGrowthPolicy(...)` accepts `percentAtCapFallbackThreshold` and normalizes into `percentNeuronsAtCapacityThreshold`.

### `src/typescript/grownet-ts/src/core/Layer.ts`

- **Auto‑growth trigger:** in `endTick()`, evaluate neurons in order and (if the trigger fires) call `tryGrowNeuron()` and mark `lastGrowthTick`. Enforces **one growth per layer per tick**.

### `src/typescript/grownet-ts/src/index.ts`

- **Barrel:** explicit PAL re‑exports from `./pal/index.js` to fix NodeNext ESM import ergonomics.

### `src/typescript/grownet-ts/package.json`

- **DX:** adds `"types": "dist/index.d.ts"`.

### `src/typescript/grownet-ts/.eslintrc.cjs` (new)

- **ESM/NodeNext resolver** to avoid lint false positives on `.js` suffix imports from TS.

### Tests (new)

- `tests/AutoGrowth.test.ts`
- `tests/SpatialMetricsParity.test.ts`

*(Also includes a tiny cleanup patch that removes stray duplicated imports if present.)*

------

## Why these changes are safe

- **Isolated behavior:** The growth trigger only runs inside `Layer.endTick()` and respects all config switches:
  - `growthEnabled` and `neuronGrowthEnabled`
  - `fallbackGrowthThreshold`
  - `neuronGrowthCooldownTicks`
- **Determinism preserved:** Growth is deterministic (input‑driven and order‑preserving) and autowiring replays deterministic mesh rules; PAL ordered reduction remains untouched.
- **Metrics parity:** The bbox/centroid computation now matches Python/Java/C++/Mojo semantics (operate over active pixels only).
- **No API breaks:** The policy alias is additive; existing callers continue to work.

------

## Test plan

- **Unit tests:** Run `npm test` in `src/typescript/grownet-ts`. New tests should pass alongside your existing PAL determinism, ND smoke, spatial metrics wrapper, and windowed wiring tests.
- **Ad‑hoc check:** Feed an image with two nonzero pixels at (1,1) and (2,2); bbox should be (rowMin=1,colMin=1,rowMax=2,colMax=2).
- **Growth smoke:** Drive repeated fallback on a single‑neuron layer; expect neuron count > 1 while still only one growth per tick.

------

## Follow‑ups (separate PRs I can send after this lands)

1. **Proximity policy (STEP mode) for TS** with once‑per‑step guard, per‑source cooldown, budget, deterministic layout and spatial hash (mirroring Python/Java/Mojo).
2. **Parallel tile execution for generic `parallelMap`** (keeping ordered reduction deterministic).
3. **Style pass** to remove single‑letter loop variables across the TS source for strict convention adherence.
4. **Optionally** add a tiny helper to record mesh rules on cross‑layer edges if/when the TS proximity policy adds edges dynamically.

------

