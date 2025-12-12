We can hide *how* we run (threads, GPU, virtual threads) behind a single cross‑language API and keep GrowNet’s **public behavior and contract identical**. Below is a concrete, drop‑in design you can hand to Codex: a **Parallelism Abstraction Layer (PAL v1)** with the same names and semantics in **Python, Java, C++, and Mojo**. It preserves our invariants (two‑phase ticks, one growth per region per tick, determinism, center‑mapped wiring), and lets us plug in **GPU in Mojo** and **Virtual Threads in Java** without changing call‑sites.

------

## PAL v1 — Unified Parallelism & Concurrency Abstraction

### Goals

- **One API, many backends:** CPU threads, Java Virtual Threads (for orchestration), GPU in Mojo.
- **Deterministic results:** same seed + inputs → identical outputs, regardless of backend or thread count.
- **Drop‑in:** call‑sites do not know if work ran on CPU or GPU.
- **No style regressions:** descriptive identifiers; Python/Mojo public names in snake_case; no leading underscores; Mojo typed `struct` + `fn`.

### Non‑goals

- No changes to growth rules, slot selection logic, or tract/mesh semantics.
- No permanent runtime coordinates added to core objects (layout stays a pure function).
- No background async side‑effects; all kernels respect tick barriers.

------

## 1) Public API (identical shape in every language)

**Core concepts**

- **Domain**: a deterministic, ordered collection of work items (e.g., neuron tiles, synapse blocks, spatial cells).
- **Kernel**: a pure function the PAL executes for each item.
- **Reducer**: a deterministic combiner applied after all kernel invocations.
- **Options**: how to run (threads, tiles, device, vectorization), never observed by the caller.

### 1.1 Types

**Options / Config**

- `max_workers: int` — default hardware_concurrency (or platform default).
- `tile_size: int` — work granularity (e.g., neurons per tile).
- `reduction_mode: "ordered" | "pairwise_tree"` — deterministic reduction flavor.
- `device: "cpu" | "gpu" | "auto"` — `"auto"` chooses GPU if available (Mojo), else CPU.
- `vectorization_enabled: bool` — hint for SIMD on CPU kernels.

**Domains**

- `NeuronTiles(layer_index, total_neurons, tile_size)`
- `SynapseBlocks(layer_index, block_size)` (optional)
- `CenterWindows(dst_layer_index, kernel_h, kernel_w, stride_h, stride_w, padding)` (windowed wiring)
- `SpatialCells(radius, layout_params)` (proximity policy)

> Each domain **must** enumerate items in a **stable lexicographic order** so results never depend on scheduling.

### 1.2 Functions (exact names across languages)

```text
pal.configure(options: ParallelOptions) -> None
pal.parallel_map(domain, kernel(item) -> LocalResult,
                 reduce_in_order(local_results) -> GlobalResult,
                 options: ParallelOptions = default) -> GlobalResult

pal.parallel_for(domain, kernel(item) -> None,
                 options: ParallelOptions = default) -> None

pal.counter_rng(seed:int, step:int, draw_kind:int,
                layer_index:int, unit_index:int, draw_index:int) -> float64  # deterministic [0,1)
```

**Design rules**

- `parallel_map` returns **local results per worker**, then **reduces in a fixed order** (worker 0, 1, …) or via a fixed‑shape tree.
- `parallel_for` is a convenience when no reduction is needed.
- `counter_rng` is provided so probabilistic kernels stay deterministic under parallelism (no shared RNG state).

------

## 2) Backends per language (hidden behind PAL)

| Language | Backend (hidden)                                             | Notes                                                        |
| -------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| Python   | C++/C API via pybind11/nanobind; releases GIL; uses platform thread pool | Python orchestrates; heavy kernels in native code. Deterministic reductions in native code. |
| Java 21  | Structured Concurrency for orchestration; compute on a fixed platform thread pool; optional Virtual Threads for tasks | Virtual Threads are great for orchestration and I/O; for CPU kernels we **limit parallelism** to avoid oversubscription. |
| C++      | OpenMP (static) or TBB; thread‑local buffers; ordered merges | Choose one (OpenMP easiest to wire). Deterministic combine in worker‑id order. |
| Mojo     | CPU backend mirrors C++; GPU backend (when available) launches kernels; same deterministic reductions | Single front API: `device="gpu"` selects GPU kernels; otherwise falls back to CPU. Identical results by design. |

------

## 3) Where PAL is called (2D ticks and friends)

**Phase‑A (2D)**

```text
pal.parallel_for(
  domain = NeuronTiles(layer_index, total_neurons, tile_size),
  kernel = integrate_and_select_for_tile,           # writes only to tile-local or per-neuron state
  options = parallel_options
)
collect_growth_intents_thread_local()               # inside kernel
RegionGrowthArbiter.apply_one_growth_deterministic()# single-threaded, after barrier
```

**Phase‑B (2D)**

```text
pal.parallel_map(
  domain = NeuronTiles(layer_index, total_neurons, tile_size),
  kernel = propagate_outgoing_for_tile -> ThreadLocalAccumulator,
  reduce_in_order = merge_accumulators_in_worker_order_into_global
)
```

**Windowed wiring (center‑mapping)**

```text
edges = pal.parallel_map(
  domain = CenterWindows(dst_layer_index, k_h, k_w, s_h, s_w, padding),
  kernel = compute_source_to_center_pairs_for_window -> local_edge_vector,
  reduce_in_order = concatenate_then_sort_by_source_then_center_then_dedupe
)
# edges committed once; return unique source count unchanged
```

**Proximity autowiring (optional policy)**

```text
cell_table = pal.parallel_map(
  domain = SpatialCells(radius, layout_params),
  kernel = build_cell_entries -> local_cell_entries,
  reduce_in_order = stable_sort_by_cell_key_then_group
)

accepted_edges = pal.parallel_map(
  domain = SpatialCells(radius, layout_params),
  kernel = probe_neighbors_with_counter_rng -> local_edges,
  reduce_in_order = union_then_cap_by_budget_in_lexicographic_order
)
```

------

## 4) RNG and determinism (shared)

- **Never** use shared mutable RNG.
- Use `pal.counter_rng(seed, step, draw_kind, layer_index, unit_index, draw_index)` across languages; implement with a **counter‑based algorithm** (e.g., Philox/Threefry/PCG‑hash).
- **Reduction**: either **ordered** (worker 0..N‑1) or a **fixed‑shape pairwise tree**. Always in `double` for accumulation, then cast if needed.
- **Iteration order**: domains enumerate in ascending, stable order (e.g., row‑major tile order for 2D).

------

## 5) Minimal interfaces (copy/paste skeletons)

### 5.1 Python

```python
# src/python/pal/api.py
from dataclasses import dataclass
from typing import Callable, Iterable, Any, List

@dataclass
class ParallelOptions:
    max_workers: int | None = None
    tile_size: int = 4096
    reduction_mode: str = "ordered"  # "ordered" | "pairwise_tree"
    device: str = "cpu"              # "cpu" | "gpu" | "auto"
    vectorization_enabled: bool = True

def configure(options: ParallelOptions) -> None: ...
def parallel_for(domain: Iterable[Any], kernel: Callable[[Any], None],
                 options: ParallelOptions | None = None) -> None: ...
def parallel_map(domain: Iterable[Any], kernel: Callable[[Any], Any],
                 reduce_in_order: Callable[[List[Any]], Any],
                 options: ParallelOptions | None = None) -> Any: ...
def counter_rng(seed:int, step:int, draw_kind:int, layer_index:int,
                unit_index:int, draw_index:int) -> float: ...
```

> Implementation delegates to a native module (`_pal_native`) that runs threads or GPU and performs deterministic reductions.

### 5.2 Java (package `ai.nektron.grownet.pal`)

```java
public final class ParallelOptions {
  public Integer maxWorkers; public int tileSize = 4096;
  public String reductionMode = "ordered";
  public String device = "cpu"; public boolean vectorizationEnabled = true;
}

public interface Domain<T> extends Iterable<T> {} // deterministic iteration

public final class PAL {
  public static void configure(ParallelOptions options) { /* store globally or thread-local */ }
  public static <T> void parallelFor(Domain<T> domain, Consumer<T> kernel, ParallelOptions opts) { /* StructuredTaskScope + fixed executor */ }
  public static <T,R> R parallelMap(Domain<T> domain, Function<T,R> kernel,
                                    Function<List<R>, R> reduceInOrder,
                                    ParallelOptions opts) { /* same */ }
  public static double counterRng(long seed, long step, int drawKind, int layerIndex, int unitIndex, int drawIndex) { /* counter-based */ }
}
```

> Compute tasks run on a **fixed platform executor** sized to cores; Virtual Threads can wrap tasks for structured orchestration but are **bounded** by that executor to avoid oversubscription.

### 5.3 C++ (header‑only façade; OpenMP/TBB under the hood)

```cpp
// include/grownet/pal/Pal.h
struct ParallelOptions {
  int  max_workers = 0;    // 0 => auto
  int  tile_size   = 4096;
  enum class Reduction { Ordered, PairwiseTree } reduction = Reduction::Ordered;
  enum class Device    { Cpu, Gpu, Auto } device = Device::Cpu;
  bool vectorization_enabled = true;
};

namespace pal {
  void configure(const ParallelOptions& options);

  template <typename Domain, typename Kernel>
  void parallel_for(const Domain& domain, Kernel kernel, const ParallelOptions* options);

  template <typename Domain, typename Kernel, typename Reduce>
  auto parallel_map(const Domain& domain, Kernel kernel, Reduce reduce_in_order, const ParallelOptions* options) -> typename /* deduced type */;

  double counter_rng(std::uint64_t seed, std::uint64_t step,
                     int draw_kind, int layer_index, int unit_index, int draw_index);
}
```

> Implementation chooses OpenMP (static) or TBB; both return identical results by using **thread‑local outputs** and **deterministic merges**.

### 5.4 Mojo (CPU and GPU in one façade)

```mojo
# src/mojo/pal/pal.mojo
struct ParallelOptions:
    var max_workers: Int? = None
    var tile_size: Int = 4096
    var reduction_mode: String = "ordered"
    var device: String = "cpu"         # "cpu" | "gpu" | "auto"
    var vectorization_enabled: Bool = True

fn configure(options: ParallelOptions) -> None: ...

fn parallel_for[T](domain: List[T], kernel: fn(T) -> None, options: ParallelOptions) -> None: ...
fn parallel_map[T, R](domain: List[T], kernel: fn(T) -> R,
                      reduce_in_order: fn(List[R]) -> R,
                      options: ParallelOptions) -> R: ...

fn counter_rng(seed: Int, step: Int, draw_kind: Int, layer_index: Int, unit_index: Int, draw_index: Int) -> Float64: ...
```

> With `device="gpu"`, the dispatcher launches GPU kernels (where available) that **write thread‑local tiles to device memory**, then copy back partials for a **deterministic host‑side reduction** (or a **deterministic device reduction** if supported).

------

## 6) Example: 2D Phase‑A with PAL (language‑agnostic pseudo)

```text
options = ParallelOptions(max_workers=cores, tile_size=64*64, reduction_mode="ordered", device="auto")

domain = NeuronTiles(layer_index, total_neurons, options.tile_size)

pal.parallel_for(
  domain,
  kernel = (tile) => {
     for neuron_index in tile.neuron_indices:
         integrate_inputs(neuron_index)
         selected_slot = select_or_create_slot_2d(neuron_index)   # existing logic
         if growth_triggered(neuron_index):
             thread_local_intents.push( GrowthIntent(layer_index, neuron_index) )
  },
  options
)

RegionGrowthArbiter.apply_one_growth_deterministic(region, gather_thread_local_intents_in_canonical_order())
```

**Phase‑B** uses `parallel_map` to return one `ThreadLocalAccumulator` per worker and then merges them **in worker order**.

------

## 7) GPU (Mojo) and Virtual Threads (Java)

- **Mojo GPU**
  - Provide GPU kernels for inner loops (integration, propagation, window map).
  - Keep deterministic merges either on host (copy back thread‑local partials) or with a **fixed‑order device reduction** (e.g., serial per target block).
  - The choice of `"gpu"` is **entirely inside PAL**; call‑sites just pass `device="auto"`.
- **Java Virtual Threads**
  - Use **Virtual Threads** for **structured orchestration** (scopes, cancellation, timeouts) but bind tasks to a **fixed parallelism** executor for the CPU‑bound kernels.
  - PAL hides this; the same `parallelFor` and `parallelMap` are used.

------

## 8) Tests (must‑pass before enabling by default)

1. **Determinism sweep**: same seed + inputs → identical model state across `max_workers ∈ {1,2,8}`, `device ∈ {"cpu","gpu","auto"}`.
2. **Phase invariants**: two‑phase barriers honored; **one growth per region per tick** via the arbiter.
3. **Windowed wiring parity**: center indices and **unique source count** identical to baseline.
4. **Proximity (if enabled)**: STEP mode requires no RNG; probabilistic modes identical with `pal.counter_rng`.
5. **Performance sanity**: large 2D (≥ 512×512) shows ≥2× vs single‑thread baseline while passing all parity tests.

------

## 9) Migration plan

- **Step 1:** Land PAL façade + CPU backends (C++/Java/Mojo), wire 2D Phase‑A and Phase‑B only; keep a feature flag (default off).
- **Step 2:** Parallelize windowed wiring and proximity policy through PAL.
- **Step 3:** Add Mojo GPU backend behind `device="auto"`; keep CPU fallback.
- **Step 4:** Enable PAL by default on 2D paths after determinism gates are green.

------

## 10) What stays invisible to callers

- Whether a tile ran on 1 thread or 64, CPU or GPU.
- Whether Java used Virtual Threads or platform threads to orchestrate.
- How reductions were implemented (ordered vs fixed tree).
   **Only the outputs and runtime stay the same**—the PAL guarantees the determinism and invariants GrowNet requires.

------

If you want, I can generate **starter files** for `pal/` in all four languages (interfaces + stub backends) so Codex can scaffold the project quickly.