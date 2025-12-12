Here’s a concrete, engineering‑grade plan to introduce **parallelism / concurrency** into GrowNet **without sacrificing determinism** or the project’s invariants (two‑phase tick, one growth per region per tick, center‑mapped wiring, etc.). I split this into (A) high‑level design, (B) per‑phase parallelization, (C) language‑specific execution patterns (Java 21, C++, Python, Mojo), (D) RNG & numerics for reproducible results, and (E) a rollout plan with tests.

------

## A) Design principles (non‑negotiables)

1. **Determinism first.** Same seed + same inputs → identical results regardless of thread count, CPU, or scheduling.
2. **Two‑phase ticks with barriers.**
   - **Phase A:** integrate inputs, choose/reinforce slot, maybe fire.
   - **Phase B:** propagate firings through synapses, demos/tract hooks observe.
   - **End of tick:** `neuron.end_tick()`, then `bus.decay()` with `current_step += 1`.
      Parallel work must **not** bleed across these barriers.
3. **One growth per region per tick.** Slot→Neuron and Layer growth decisions can be collected in parallel but **applied** by a single, deterministic arbiter.
4. **No global mutable state writes from workers.** Workers produce **per‑task results**; a **deterministic combiner** merges them in a fixed order.
5. **No “fast math” that changes results.** When sums or thresholds are involved, use deterministic reductions (see §D).
6. **No single/double‑character identifiers** in new code; Python/Mojo public names in snake_case; Mojo uses typed `struct` + `fn`.

------

## B) Where parallelism pays off (and how to do it safely)

### B1) Phase A — neuron integration + slot selection (hot path)

- **Task shape:** per‑neuron, read‑mostly inputs, local writes (membrane potential, slot selection bookkeeping).
- **Parallelization:** partition neurons in **fixed contiguous tiles** per layer (e.g., 4–64 KB of state per tile for cache warmth).
   Each worker runs `integrate_and_select(neuron_range)` independently.
- **Growth intents:** when a neuron hits the growth trigger, it **records a “growth intent”** (seed neuron id + layer id + reason) into a **thread‑local list**. Do **not** grow immediately.
- **Barrier + arbiter:** after all workers finish, a single **RegionGrowthArbiter** (one per region) merges growth intents:
  - Sort intents by `(layer_index, neuron_index)` and apply **exactly one** growth per region per tick (first match wins).
  - This preserves determinism independent of worker interleaving.

### B2) Phase B — synapse propagation (heavy bandwidth)

- **Task shape:** per‑source neuron (or per‑synapse block) accumulation into target buffers.
- **Race‑free accumulation:** give each worker a **thread‑local accumulation buffer** for target deltas. After processing its shard, the worker publishes its buffer. The combiner then **reduces** buffers into the global target array in a **fixed worker order** (0,1,2,…), ensuring deterministic floating‑point summation (see §D).
- **Optional SIMD:** where available (Java Vector API, C++ intrinsics), vectorize inner loops; vectorization does not change determinism provided the reduction strategy is fixed.

### B3) Windowed wiring (center‑mapping + dedupe)

- **Build in parallel; normalize deterministically.**
  - **Parallel map:** compute `(source_index → center_index)` pairs.
  - **Local dedupe:** keep a small thread‑local `bitset`/`sorted vector` for `(source, center)` to avoid duplicates.
  - **Global merge:** concatenate per‑thread edges and **sort by `(source_index, center_index)`**; drop duplicates in **one pass**.
  - Sorting gives deterministic adjacency **order**, independent of thread scheduling.
- **Return value parity:** the function must still return the **number of unique source pixels** (unchanged).

### B4) Proximity autowiring (spatial hash + neighbor search)

- **Parallel grid build:** compute `(cell_key, neuron_id)` pairs in parallel; **stable‑sort** by `cell_key` (deterministic), then group.
- **Neighbor probes:** process each cell‑group in parallel; candidates come from a **fixed 3×3×3** stencil around the key.
- **Probabilistic modes:** compute probability per pair; for Bernoulli draws use **counter‑based RNG** (§D2).
- **Budget & cooldown:** each worker writes accepted edges to a local list; the combiner merges by `(src_layer,src_neuron,dst_layer,dst_neuron)` with a **budget cap** enforced in **lexicographic order**, guaranteeing the same subset regardless of worker completion order.
- **Mesh rules:** if cross‑layer, the combiner records mesh rules **once**, after merging.

### B5) End‑of‑tick (decay)

- **Parallelizable** because it is a pure per‑neuron update. Use the same fixed partitioning as Phase A.
- **Note:** the **bus** `current_step` increment must be **single‑threaded** and occur **after** workers finish.

------

## C) Language‑specific execution patterns

### C1) **Java 21** (Virtual Threads + Structured Concurrency)

**Short answer:** Use **StructuredTaskScope** for orchestration, **fixed platform thread pools** for CPU‑bound loops, **Virtual Threads** only when ergonomic (blocking or many tiny tasks).

- **Why**: Virtual Threads are great for blocking workloads; GrowNet is CPU‑bound. For compute kernels, **avoid oversubscription** by using a fixed‑size `Executor` (≈ number of cores). Still use **StructuredTaskScope** to encode barriers and cancellation cleanly.

**Pattern**

```java
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    // Submit layer tiles in a fixed order for Phase A
    for (LayerTile tile : layerTilesInDeterministicOrder) {
        scope.fork(() -> { integrator.run(tile); return null; });
    }
    scope.join();  // barrier
    scope.throwIfFailed();
}
// Now single-threaded: growth arbiter applies exactly one growth per region/tick
growthArbiter.applyOneGrowth(region, intentsCollectedDeterministically);
```

- **Deterministic reduction:** for sums, accumulate in thread‑local arrays and reduce them on the **main thread** in worker index order.
- **Vectorization:** consider **Java Vector API** for inner loops (SIMD) while staying in the same deterministic reduction order.
- **Configuration knobs:** `grownet.parallelism = cores`, `grownet.tile_size = 4096` (number of neurons per tile), `grownet.vector_width = auto`.

### C2) **C++** (std::thread / TBB / OpenMP — pick one)

- **Recommendation:** use **TBB `parallel_for`** or **OpenMP** with **static scheduling** and **per‑thread buffers**; then reduce in worker id order.
- **Example (OpenMP outline):**

```cpp
#pragma omp parallel
{
    int worker_id = omp_get_thread_num();
    auto& local_accum = worker_accumulators[worker_id];
    #pragma omp for schedule(static)
    for (int neuron_index = neuron_begin; neuron_index < neuron_end; ++neuron_index) {
        integrate_and_select(neuron_index, local_accum);
    }
} // implicit barrier
// Deterministic combine
for (int worker_id = 0; worker_id < worker_count; ++worker_id) {
    reduce_into_global(worker_accumulators[worker_id]); // fixed order
}
```

- **Numerics:** disable fast‑math that reorders operations; do reproducible reductions (pairwise or Kahan—see §D3).

### C3) **Python**

- Keep Python as the **orchestrator**; do heavy work in **C++ extension** (pybind11/nanobind) that internally uses threads and **releases the GIL**.
- Expose a small set of knobs: `set_thread_count(n)`, `set_tile_size(k)`.
- Ensure probabilistic paths call into C++ RNG functions that are **counter‑based** (see §D2).

### C4) **Mojo**

- If/when you adopt threads in Mojo, mirror the C++ pattern: fixed tiling, per‑thread accumulators, deterministic merges. Keep the public API typed and snake_case.

------

## D) Determinism: RNG, reductions, and ordering

### D1) Fixed ordering everywhere

- Enumerate **layers** and **neurons** in ascending index order for all maps.
- After parallel generation (e.g., edges), **sort** by a canonical key and **then** apply effects. This removes scheduler dependence.

### D2) RNG for parallel worlds (no shared mutable state)

- Replace shared RNG state with a **counter‑based RNG** (stateless function):
   `random_double = RNG(region_seed, current_step, draw_kind, layer_index, neuron_index, draw_index)`
   where `draw_kind` is a small integer (e.g., 0=proximity, 1=dropout…).
- **Why**: The draw no longer depends on **who** ran it or **when**, only on **what** was computed.
- Practical choices: Philox/Threefry (counter‑based), or SplitMix64/PCG derived by hashing the 5‑tuple above. Keep identical implementation across languages.

### D3) Floating‑point reproducibility

- **Per‑thread accumulators + ordered reduction.** The simplest robust pattern:
  1. Each worker accumulates in `double` (even if weights are `float`).
  2. The combiner reduces buffers in **ascending worker id**.
- For tight tolerance across platforms, use **pairwise tree reduction** with a fixed tree shape (e.g., power‑of‑two fan‑in).
- Avoid `-ffast-math` / aggressive autovectorization that reorders sums. Prefer explicit Vector API or intrinsics where you control reduction order.

------

## E) Rollout plan (3 stages)

### Stage 1 — Infrastructure (2 weeks)

- Add a **Policy‑layer “ParallelExecutor”** (sidecar) per language:
  - `parallel_for_neurons(region, layer_index, tile_size, worker_fn)`
  - `reduce_in_order(buffers, combine_fn)`
  - `set_thread_count(n)`; defaults to `hardware_concurrency`.
- Implement **counter‑based RNG** across languages and wire proximity policy to use it.
- Add **Parallel Parity Tests**:
  - Run the same tiny model with `thread_count = 1, 2, 8`; assert that the entire region state (slots, synapses, bus step, metrics) is **bit‑identical** at **N** ticks.

### Stage 2 — Hot paths (3–4 weeks)

- Phase A parallelization (integration + slot selection).
- Phase B parallelization (propagation with ordered reductions).
- Windowed wiring (map + sort‑dedupe); proximity policy (grid build + search as in §B4).
- **Growth arbiter** extraction: collect intents in parallel; apply **one growth** per region in a deterministic section.

### Stage 3 — Optimization & polish (ongoing)

- Tune tile size; add SIMD in inner loops (Java Vector API, C++ intrinsics).
- Profile & choose **SoA** layouts where beneficial (e.g., separate arrays for `membrane`, `threshold`, `inhibition`).
- Expose safe, read‑only **telemetry** (threads used, tile timing) to your visualizer—no core fields; emit via a sidecar hook.

------

## F) Concrete examples (short)

### F1) Deterministic growth arbiter (language‑agnostic sketch)

```text
collect_growth_intents_in_parallel(): vector<Intent>
  # each worker pushes to its local list

merge_and_apply_one(region, intents):
  sort intents by (layer_index, neuron_index, trigger_kind)
  for intent in intents:
     if region.can_grow(intent):    # capacity, cooldown, etc.
         region.grow_from(intent)   # adds exactly one neuron or one layer
         record_mesh_rules_if_needed(intent)
         break
```

### F2) Java 21: structured concurrency for Phase A and Phase B

```java
// Phase A
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    for (LayerTile tile : tilesInOrder) {
        scope.fork(() -> { integrator.runTile(tile, localIntentBuffer); return null; });
    }
    scope.join(); scope.throwIfFailed();
}
growthArbiter.applyOne(region, mergeIntentsDeterministically(workerIntentBuffers));

// Phase B
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    for (PropagationTile tile : propagationTiles) {
        scope.fork(() -> { propagator.runTile(tile, threadLocalAccumulator); return null; });
    }
    scope.join(); scope.throwIfFailed();
}
reduceAccumulatorsInWorkerOrder(accumulators, globalTargetDeltas);
```

### F3) C++: deterministic reduction pattern

```cpp
// worker_accumulators: vector<AlignedBuffer> sized to thread_count
#pragma omp parallel
{
    const int worker_id = omp_get_thread_num();
    auto& local = worker_accumulators[worker_id];
    #pragma omp for schedule(static)
    for (int neuron_index = neuron_begin; neuron_index < neuron_end; ++neuron_index) {
        integrate_and_select(neuron_index, local);
    }
}
// Deterministic combine
for (int worker_id = 0; worker_id < worker_count; ++worker_id) {
    reduce_into_global(worker_accumulators[worker_id]); // fixed order merge
}
```

------

## G) Where Virtual Threads help (and where they don’t)

- **Help:** ergonomics for **structured concurrency**, timeouts, cancellations, or if you add **I/O‑bound** demo pipelines (telemetry streaming, logging, WebSocket UI). Virtual Threads keep code simple without tying up platform threads.
- **Don’t help:** raw **CPU‑bound kernels**. Use a **fixed parallelism** executor for heavy loops to avoid oversubscription; still manage orchestration with `StructuredTaskScope`.

------

## H) Risk register & mitigations

- **Non‑deterministic floats:** use ordered reductions; avoid fast‑math; promote accumulators to `double`.
- **RNG contention or drift:** use **counter‑based RNG** keyed by `(region_seed, step, draw_kind, layer, neuron, draw_index)`.
- **Data races:** immutable inputs, thread‑local outputs, deterministic merges.
- **Oversubscription:** fixed thread pool size near core count; optional NUMA awareness later.
- **Growth thrash:** keep **cooldowns** and apply **one growth per region per tick** via arbiter.

------

## I) Definition of Done (parallel MVP)

- Parallel execution for Phase A and Phase B with **identical outputs** to the single‑threaded reference (across `thread_count ∈ {1,2,8}`).
- Windowed wiring and proximity policy use **sort‑dedupe** and **budgeted merges** (deterministic).
- Growth arbiter enforces **one growth** per region per tick with **stable tie‑breaks**.
- Counter‑based RNG in all languages; no global RNG fallbacks; STEP proximity needs no RNG.
- Parity tests + stress tests are green; performance shows **>2×** on 8 cores for representative demos.

------

## J) Quick backlog (post‑MVP)

- SIMD in inner loops (Java Vector API, C++ intrinsics) with deterministic reductions.
- NUMA‑aware tiling for very large regions.
- Thread‑pool affinity per region (multi‑region runs).
- Optional GPU backends (weights only; core logic stays on CPU for parity).

------

### Bottom line

Yes—parallelism will benefit GrowNet **immensely** if we keep it **deterministic and staged**. Use **fixed tiling + thread‑local buffers + ordered merges**, a **counter‑based RNG**, and **structured concurrency** (Java 21) for clean barriers. Start with Phase A/Phase B, then windowed wiring and proximity. Add the growth arbiter to preserve “one growth per region per tick.” This gets you real‑world speedups **without** compromising the scientific contract or cross‑language parity.

#### **Parallelism for 2D Ticks**

Short answer: **Yes.** The 2D tick path is the *best* place to harvest parallel speedups—both in **Phase‑A** (per‑neuron integration + slot selection) and **Phase‑B** (synapse propagation). The key is to do it **deterministically** with clear barriers so we never violate GrowNet’s invariants (two‑phase ticks, one growth per region per tick, center‑mapped windowed wiring, bus decay semantics).

Below is a practical blueprint you can hand to Codex to implement parallel 2D ticks across Java 21, C++, Python (via C++ bindings), and Mojo.

------

## Where the speedup comes from in 2D

**Hot loops on 2D layers:**

- **Phase‑A (compute‑bound)**: For each pixel‑neuron, integrate inputs, choose/reinforce slot (2D bins), maybe fire. Each neuron can be processed **independently** → tile and parallelize.
- **Phase‑B (bandwidth‑bound)**: For each firing neuron, walk outgoing synapses to accumulate into targets. Do **thread‑local accumulators** then a **deterministic reduction**.
- **Windowed wiring** (sliding kernel → center mapping): Build `(source_index → center_index)` pairs in parallel, then **sort + dedupe** once—deterministic regardless of scheduling.
- **Proximity policy** (if enabled): Build the **spatial hash** in parallel and probe neighbors per cell‑group.

> On a typical 8–16‑core desktop, you can expect **3–8×** on larger 2D layers (e.g., ≥ 256×256), with Phase‑B often limited by memory bandwidth. For very small 2D layers (≤ 64×64), the thread overhead can outweigh benefits—use a threshold.

------

## Deterministic tiling of a 2D layer

**Partitioning:** split each 2D layer into fixed **row‑major tiles** (for example, 64×64 pixels per tile), and enumerate tiles in ascending `(tile_row, tile_col)` order.

- **Phase‑A:** each worker processes `integrate_and_select(tile_range)`.
- **Phase‑B:** each worker processes `propagate_outgoing(tile_range, thread_local_accumulator)`.
- **Windowed wiring:** either iterate destination centers by tile or iterate source tiles and produce `(source, center)` candidates; then **sort once** and dedupe globally.

**Why this works:**

- No halos are required for Phase‑A (each neuron uses its own local state).
- For Phase‑B and windowed wiring, per‑thread outputs go to **local structures** (vectors/bitsets), then one **ordered merge** ensures reproducible results.

------

## Growth invariants (critical)

Parallel workers **collect “growth intents” only** (e.g., “neuron 17 in layer 3 wants to grow”); a single **RegionGrowthArbiter** runs after Phase‑B to:

1. **Sort** intents by `(layer_index, neuron_index, trigger_kind)`.
2. Apply **exactly one** growth per region in that tick (first eligible intent wins).
3. Record **mesh rules** deterministically (same as today).

This preserves “**one growth per region per tick**” regardless of thread scheduling.

------

## Numeric reproducibility

- Use **thread‑local accumulators** in **double** precision.
- Merge them in a **fixed order** (worker 0, then worker 1, …) or use a **fixed‑shape pairwise reduction**.
- **Do not** enable fast‑math modes that reorder sums. If you add SIMD (Java Vector API, C++ intrinsics), keep reductions deterministic.

------

## RNG in parallel (probabilistic features only)

- Replace shared RNG with **counter‑based draws** keyed by a deterministic tuple:

  ```
  rng_value = RNG(region_seed, current_step, draw_kind, layer_index, neuron_index, draw_index)
  ```

- This makes outcomes independent of thread scheduling.

- Features that don’t need randomness (e.g., proximity STEP mode) remain RNG‑free.

------

## Language‑specific execution patterns

### Java 21

- Orchestrate with **Structured Concurrency**; run compute tiles on a **fixed platform thread pool** sized to core count (Virtual Threads are great for blocking workloads, but compute kernels should avoid oversubscription).

- **Pattern (Phase‑A):**

  ```java
  try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
      for (Tile tile : tilesInOrder) {
          scope.fork(() -> { phaseAIntegrator.runTile(region, layerIndex, tile, threadLocalIntentBuffer); return null; });
      }
      scope.join(); scope.throwIfFailed();
  }
  growthArbiter.applyOneGrowth(region, mergeIntentsDeterministically(workerIntentBuffers));
  ```

- **Phase‑B:** same pattern with `threadLocalAccumulator`, then a **single‑threaded deterministic reduction**.

- Consider **Java Vector API** inside tile loops for extra wins (keep reduction order fixed).

### C++

- Use **OpenMP (static)** or **TBB** for tiling; keep **per‑thread buffers**, then merge in worker id order.

  ```cpp
  #pragma omp parallel
  {
      int worker_id = omp_get_thread_num();
      auto& local = worker_accumulators[worker_id];
  
      #pragma omp for schedule(static)
      for (int neuron_index = neuron_begin; neuron_index < neuron_end; ++neuron_index) {
          integrate_and_select(neuron_index, local);   // Phase‑A core
      }
  } // barrier
  
  for (int worker_id = 0; worker_id < worker_count; ++worker_id) {
      reduce_into_global(worker_accumulators[worker_id]); // deterministic merge
  }
  ```

- Windowed wiring: produce edges in parallel → **sort by `(source_index, center_index)`** → dedupe → commit once.

### Python (via C++ bindings)

- Keep Python as **orchestrator**; call into a C++ extension (pybind11/nanobind) that:
  - releases the **GIL** around kernels,
  - accepts **NumPy** buffers for frames,
  - uses the same C++ tiling and reduction patterns,
  - exposes knobs: `set_thread_count(n)`, `set_tile_size(k)`.
- Python and C++ must share the **same deterministic RNG** policy (counter‑based) for probabilistic features.

### Mojo

- Mirror the C++ plan when you enable threads: fixed tiling, per‑thread accumulators, deterministic merges. Keep public API typed and snake_case.

------

## Windowed wiring on 2D (center‑mapping) — parallel recipe

1. **Map step (parallel):** for each destination **center** tile, compute the source window ranges, produce `(source_index, center_index)` pairs in a **thread‑local vector**.
2. **Global normalize:** concatenate → **sort once** by `(source_index, center_index)` → drop duplicates with a linear pass.
3. **Weights/tracts:** assign default weights (or run the topographic preset) in a **second pass**, and record **mesh rules** if cross‑layer.

This keeps edge topology **identical** to the sequential baseline.

------

## Proximity policy on 2D (optional) — parallel recipe

1. **Grid build (parallel):** compute `(cell_key, neuron_id)` from deterministic layout; stable‑sort by `cell_key`.
2. **Neighbor search (parallel):** for each cell group, scan the fixed **3×3×3** stencil; compute distances; for probabilistic modes, draw with **counter‑based RNG**.
3. **Budgeted merge:** union per‑thread accepted edges and **cap** at `proximity_max_edges_per_tick` using a **lexicographic order** of `(src_layer, src_neuron, dst_layer, dst_neuron)`.
4. **Mesh rules:** record once for cross‑layer edges.

------

## API knobs to add (non‑intrusive, sidecar or config)

- `parallelism.thread_count`: default `hardware_concurrency`.
- `parallelism.tile_size_pixels`: default `4096` (≈ 64×64).
- `parallelism.reduction_mode`: `"ordered"` | `"pairwise_tree"`.
- `parallelism.enable_vectorization`: `true|false` (opt‑in).
- (Optional) `parallelism.min_2d_area_for_threads`: do not spawn threads below this area.

These are **policy‑layer knobs**, not new fields on core types.

------

## Test plan (must‑pass gates)

1. **Determinism:** same seed + inputs → identical model state after N ticks for `thread_count ∈ {1,2,8}`.
2. **Phase invariants:** growth intents collected in parallel but **only one** growth per region per tick.
3. **2D slot selection:** anchors, fallback flags, and one‑shot unfreeze parity identical to baseline.
4. **Windowed wiring:** center indices and **unique source count** identical to baseline.
5. **Proximity policy:** STEP mode identical without RNG; probabilistic modes identical with counter‑based RNG.
6. **Performance sanity:** large 2D (e.g., 512×512) shows **>2×** speedup at 8 cores with ordered reductions.

------

## Suggested first milestone (small, high ROI)

1. **C++ core:** add parallel Phase‑A and Phase‑B for **2D layers only**, with deterministic reductions and a growth arbiter.
2. **Java 21:** orchestrate the same with `StructuredTaskScope` and a fixed `Executor` sized to core count.
3. **Python:** call the C++ kernels via pybind11; keep Python API stable.
4. **Mojo:** keep sequential for now; follow C++ pattern later.
5. Land **determinism tests** (1/2/8 threads) and a **tile‑size threshold** to avoid oversubscribing small images.

------

### Bottom line

**Yes**—2D ticks are the ideal place to introduce parallelism. Tile the 2D layers, do per‑tile work in parallel with **thread‑local buffers**, and merge results **in a fixed order**. Keep growth decisions centralized and deterministic. With this approach, you get substantial speedups on 2D workloads **without** compromising GrowNet’s scientific contract or cross‑language parity.