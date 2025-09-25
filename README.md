# GrowNet

**GrowNet** is a growth‑based, event‑driven learning system inspired by how humans develop capability over time. Instead of large end‑to‑end gradients, GrowNet learns *locally*, adds capacity *incrementally*, and wires itself *deterministically*. The goal is to provide a credible alternative path toward general intelligence—one that can be configured as a **world model**, a **language model**, a **reasoning/thinking module**, or any other skill‑acquisition pipeline your application demands. *This is an active research project; claims are aspirational and under empirical validation.*

------

## Why this is different from today’s deep learning

- **Local learning. No backprop.** Neurons adapt based on local events; learning and selection are driven by *slots* that activate and stabilize without backpropagating error across layers. 
- **Two‑phase clock, deterministic wiring.** Every tick runs as: **(A)** deliver & fire, then **(B)** end‑tick & bus decay; wiring and growth reuse recorded mesh rules so behavior is reproducible. 
- **Capacity grows as needed.** Adaptation escalates **Slots → Neurons → Layers → Regions** as pressure builds, with explicit cooldowns and “one‑growth‑per‑tick” safety at the region level.
- **Spatial focus with windowed wiring.** 2D inputs connect via center‑mapped windows; duplicates are deduped; return value is the **unique source count**, making spatial fan‑in both controlled and measurable. 
- **Rigorous slot semantics.** Strict slot capacity (no new slot at cap), explicit fallback marking, and optional frozen slots (with *prefer_last_slot_once* after unfreeze) make learning stable and interpretable. 

> **Positioning:** GrowNet is intended to be **domain‑agnostic**. With suitable sensors/encoders, the same core can serve as a *world model*, *language model*, or *deliberation engine*—the architecture does not assume image tokens, attention stacks, or backprop. (This is an open research program; the contract codifies determinism and learning semantics to make rigorous comparisons possible.) 

------

## Core ideas at a glance

- **Slots (concept cells).** Inputs are binned relative to a *FIRST* anchor (scalar or 2D), producing stable “concept slots.” When capacity is reached or a new bin is out‑of‑domain, the selector *reuses deterministically* and flags a *fallback*. 
- **Growth rules with cooldowns.** Fallback streaks trigger neuron growth; layer growth is policy‑driven (thresholds and cooldown ticks); regions enforce exactly one growth action per tick for stability. 
- **Two‑phase tick with buses.** Lateral/region buses apply multiplicative inhibition decay, reset modulation, and increment a step counter used by cooldown logic. 
- **Spatial focus (2D).** “Same” padding defines centers by floor semantics; each source pixel connects to **one center** per window; cross‑window duplicates are deduped. 

------

## What you can build

- **World models.** Stream structured sensory frames into 2D layers, wire via windowed/connect rules, and let growth allocate representational capacity where pressure is highest. 
- **Language models.** Feed token features into scalar or grid encodings; slots stabilize symbol‑context concepts; downstream layers compose via learned connectivity. (Same learning rules—no backprop assumptions.) 
- **Thinking/Planning modules.** Use growth thresholds and cooldowns to control expansion of working memory and policy layers; deterministic wiring lets you audit the evolution of structure. 

------

## Cross‑language contract (v5)

GrowNet’s **public surface and invariants** are defined by a language‑agnostic contract so Python, C++, Java, and Mojo behave the same. Highlights:

- **Invariants:** local, event‑driven learning; strict slot capacity & fallback marking; two‑phase tick; deterministic wiring; best‑effort growth; public APIs are no‑throw on normal ticks. 
- **Windowed wiring (2D):** center‑mapping rule, dedupe semantics, **unique source count** return value, and `attach_source_neuron(new_src)` for deterministic re‑wiring after growth. 
- **Naming/style:** snake_case in Python/Mojo, camelCase in Java, descriptive identifiers (avoid single‑ or double‑char names), and **no leading underscores** in public APIs. 

> See the contract for the full API lists (Region/Layers/Neuron/Weight/Bus types and methods) and testable behaviors. 

------

## Quick tour: minimal 2D pipeline (sketch)

> The snippet below uses contract names. Concrete package paths may differ in your tree.

```python
# Pseudocode aligned to the v5 contract
region = Region(name="demo")                                   # add a region
src = region.add_input_layer_2d(height=64, width=64, gain=1.0, epsilon_fire=1e-6)
dst = region.add_output_layer_2d(height=64, width=64, smoothing=0.0)

# Center-mapped, windowed wiring (unique sources return)
unique_sources = region.connect_layers_windowed(
    source_index=src, dest_index=dst,
    kernel_h=7, kernel_w=7, stride_h=1, stride_w=1, padding="same"
)

# Tick the region with a frame; metrics are canonical snake_case fields
metrics = region.tick_2d(port="image", frame=frame_64x64)
print(metrics.total_slots, metrics.total_synapses)
```

Window wiring follows the **center rule** and returns the number of unique source pixels that participated in ≥1 window; duplicates are deduped by design. 

------

## Parallelism (PAL) and determinism

GrowNet ships with a **Parallelism Abstraction Layer (PAL)** so call‑sites keep the same surface while we add backends:

- **Deterministic reductions** (ordered or fixed tree) and **counter‑based RNG** keep results stable across worker counts/devices.
- **Backends:** C++ (OpenMP when available), Java (bounded executors; Virtual Threads for orchestration), Python/Mojo façades with CPU tiling, Mojo hook for **GPU** in future work.
- All PAL integration respects the two‑phase tick and *one‑growth‑per‑tick* invariant. 

> Determinism gates: same seed + same inputs ⇒ identical state across `{max_workers ∈ {1,2,8}}` with ordered reduction. (See tests in your tree once enabled.)

------

## Inspectability & safety

- **Frozen slots.** `freeze_last_slot()` pauses learning on that slot; `unfreeze_last_slot()` resumes and *prefers it once* for a controlled restart. 
- **Best‑effort growth.** Growth failures never abort a tick; APIs avoid throwing during normal operation. 
- **Recorded mesh rules.** Growth re‑uses recorded wiring rules for deterministic autowiring of new neurons/layers. 

------

## Getting started

### Build & dependencies (sketch)

- **CMake (C++ core):** OpenMP is optional; if found, it’s used by PAL backends. (`-DGROWNET_WITH_OPENMP=ON` recommended.)
- **Python/Java/Mojo:** Follow your language’s standard build; the public API names mirror the contract so examples port cleanly. 

### First experiments

1. Wire an input 2D layer and an output 2D layer via `connect_layers_windowed(…, padding="same")`. 
2. Stream frames with `tick_2d(…)` and watch `RegionMetrics` (`delivered_events`, `total_slots`, `total_synapses`, optional spatial metrics). 
3. Enable growth via `GrowthPolicy` (thresholds, cooldowns) and inspect how capacity scales. 

------

## Language support matrix

| Language    | Strict capacity + fallback | Freeze/Unfreeze (prefer once) | Neuron growth (fallback streak + cooldown) | Region growth (OR-trigger + cooldown) | Windowed tracts (center rule + unique sources) | Mesh-rule replay | PAL determinism | Spatial metrics |
|-------------|----------------------------|--------------------------------|--------------------------------------------|----------------------------------------|-----------------------------------------------|------------------|-----------------|----------------|
| Python      | ✅                          | ✅                              | ✅                                          | ✅ (opt-in)                             | ✅                                             | ✅                | ✅               | ✅             |
| C++         | ✅                          | ✅                              | ✅                                          | ✅                                      | ✅                                             | ✅                | ✅ (OpenMP ordered) | ✅          |
| Java        | ✅                          | ✅                              | ✅                                          | ✅                                      | ✅                                             | ✅                | ✅ (Virtual Threads) | ✅        |
| Mojo        | ✅                          | ✅                              | ✅                                          | ✅                                      | ✅                                             | ✅                | ✅ (device knob) | ✅          |
| TypeScript  | ✅                          | ✅                              | ✅ (one growth per layer per tick)          | ✅                                      | ✅ (center mapping; `attachSourceNeuron`)      | ✅                | ✅ (WorkerPool ordered) | ✅     |
| Rust        | 🚧 Phase 1 scaffolding      | 🚧                              | 🚧                                          | 🚧                                      | 🚧 (tract scaffold)                            | 🚧                | ✅ (single-thread placeholder) | 🚧  |

> Rust status: core workspace sketched (Region/Layer/Neuron/SlotEngine, bus decay, fallback flag, request_layer_growth guard). Events/propagation and proximity policy land in Phase 2.

------

## TypeScript quickstart

**Server** (`src/typescript/grownet-ts`)

```bash
npm install        # or: pnpm install
npm run dev        # ESM dev via ts-node/esm
# or build & start:
npm run build && npm start
```

**Client** (`src/typescript/grownet-client`)

```bash
npm install
npm run dev
# build/preview:
npm run build && npm run preview
```

**Notes**
- Node.js **20+** recommended.
- Scripts: server uses `tsc`, `vitest`, `eslint` and exposes `dev|build|start|test|lint`.

------

## Rust (Phase 1)

A Rust workspace for Phase 1 (core data model + tick discipline + strict capacity/fallback + growth scaffolding) exists and will be integrated under `/rust/` in a follow-up PR.

**Scope covered**
- `Region`, `Layer`, `Neuron`, `SlotEngine` with FIRST anchor, strict capacity, and fallback marking.
- `LateralBus.decay()` parity (inhibition *= decay, modulation = 1.0, step += 1).
- `request_layer_growth()` enforcing one growth per region per tick (p=1.0 spillover).
- Deterministic RNG (SplitMix64).

**Next (Phase 2)**
- Event propagation
- Windowed center mapping & `Tract::attach_source_neuron`
- Proximity policy (STEP) with cooldowns & per-step guard
- PAL multi-threaded ordered reduction

------

## Build & test cheat sheet

- **Python**: `pytest` under `src/python/tests` (env `GROWNET_PAL_MAX_WORKERS` respected).
- **C++**: CMake; run gtests under `src/cpp/tests` (OpenMP optional).
- **Java**: JDK 21; `./mvnw -q -Dtest=*Test test` (Virtual Threads PAL).
- **Mojo**: `pip install mojo==0.25.x`; run tests in `src/mojo/tests`; you can use `MOJO_ENABLE_STACK_TRACE_ON_ERROR=1`.
- **TypeScript**: 
  - server: `npm run test` (vitest), `npm run lint` (eslint).
  - client: `npm run dev` (vite).
- **Rust** (Phase 1): `cargo test -p grownet-core` (after `/rust` integration).

------

## Docs & order

- Start here: `docs/READ_ORDER.md`
- Style: `docs/CODING_STYLE_MUST_READ.md`
- Growth rules: `docs/GROWTH.md`, `docs/GROWTH_CHEATSHEET.md`
- Spatial Focus / 2D binning: `docs/2D_Bins.md`, `docs/2D_Bins_Spatial_Focus.md`
- Benchmarks: `src/bench/README.md`


------

## Language support matrix

| Language    | Strict capacity + fallback | Freeze/Unfreeze (prefer once) | Neuron growth (fallback streak + cooldown) | Region growth (OR-trigger + cooldown) | Windowed tracts (center rule + unique sources) | Mesh-rule replay | PAL determinism | Spatial metrics |
|-------------|----------------------------|--------------------------------|--------------------------------------------|----------------------------------------|-----------------------------------------------|------------------|-----------------|----------------|
| Python      | ✅                          | ✅                              | ✅                                          | ✅ (opt-in)                             | ✅                                             | ✅                | ✅               | ✅             |
| C++         | ✅                          | ✅                              | ✅                                          | ✅                                      | ✅                                             | ✅                | ✅ (OpenMP ordered) | ✅          |
| Java        | ✅                          | ✅                              | ✅                                          | ✅                                      | ✅                                             | ✅                | ✅ (Virtual Threads) | ✅        |
| Mojo        | ✅                          | ✅                              | ✅                                          | ✅                                      | ✅                                             | ✅                | ✅ (device knob) | ✅          |
| TypeScript  | ✅                          | ✅                              | ✅ (one growth per layer per tick)          | ✅                                      | ✅ (center mapping; `attachSourceNeuron`)      | ✅                | ✅ (WorkerPool ordered) | ✅     |
| Rust        | 🚧 Phase 1 scaffolding      | 🚧                              | 🚧                                          | 🚧                                      | 🚧 (tract scaffold)                            | 🚧                | ✅ (single-thread placeholder) | 🚧  |

> Rust status: core workspace sketched (Region/Layer/Neuron/SlotEngine, bus decay, fallback flag, request_layer_growth guard). Events/propagation and proximity policy land in Phase 2.

------

## TypeScript quickstart

**Server** (`src/typescript/grownet-ts`)

```bash
npm install        # or: pnpm install
npm run dev        # ESM dev via ts-node/esm
# or build & start:
npm run build && npm start
```

**Client** (`src/typescript/grownet-client`)

```bash
npm install
npm run dev
# build/preview:
npm run build && npm run preview
```

**Notes**
- Node.js **20+** recommended.
- Scripts: server uses `tsc`, `vitest`, `eslint` and exposes `dev|build|start|test|lint`.

------

## Rust (Phase 1)

A Rust workspace for Phase 1 (core data model + tick discipline + strict capacity/fallback + growth scaffolding) exists and will be integrated under `/rust/` in a follow-up PR.

**Scope covered**
- `Region`, `Layer`, `Neuron`, `SlotEngine` with FIRST anchor, strict capacity, and fallback marking.
- `LateralBus.decay()` parity (inhibition *= decay, modulation = 1.0, step += 1).
- `request_layer_growth()` enforcing one growth per region per tick (p=1.0 spillover).
- Deterministic RNG (SplitMix64).

**Next (Phase 2)**
- Event propagation
- Windowed center mapping & `Tract::attach_source_neuron`
- Proximity policy (STEP) with cooldowns & per-step guard
- PAL multi-threaded ordered reduction

------

## Build & test cheat sheet

- **Python**: `pytest` under `src/python/tests` (env `GROWNET_PAL_MAX_WORKERS` respected).
- **C++**: CMake; run gtests under `src/cpp/tests` (OpenMP optional).
- **Java**: JDK 21; `./mvnw -q -Dtest=*Test test` (Virtual Threads PAL).
- **Mojo**: `pip install mojo==0.25.x`; run tests in `src/mojo/tests`; you can use `MOJO_ENABLE_STACK_TRACE_ON_ERROR=1`.
- **TypeScript**: 
  - server: `npm run test` (vitest), `npm run lint` (eslint).
  - client: `npm run dev` (vite).
- **Rust** (Phase 1): `cargo test -p grownet-core` (after `/rust` integration).

------

## Docs & order

- Start here: `docs/READ_ORDER.md`
- Style: `docs/CODING_STYLE_MUST_READ.md`
- Growth rules: `docs/GROWTH.md`, `docs/GROWTH_CHEATSHEET.md`
- Spatial Focus / 2D binning: `docs/2D_Bins.md`, `docs/2D_Bins_Spatial_Focus.md`
- Benchmarks: `src/bench/README.md`


------

## Roadmap

- **Full PAL enablement** on 2D Phase‑A/Phase‑B, windowed wiring, and optional proximity policies—**determinism first**, then performance. 
- **GPU path (Mojo)** behind PAL with identical numerical results (ordered or fixed‑tree reductions).
- **Extended presets:** topographic distance‑based weights (Gaussian/DoG) layered over windowed wiring, with per‑target normalization. 

------

## Contributing

- Follow the **naming rules**: snake_case (Python/Mojo), camelCase (Java), descriptive identifiers (no single/double‑letter names), and **no leading underscores** in public APIs. 
- Keep changes **contract‑compliant**: slot capacity, fallback marking, two‑phase tick, recorded mesh rules, and one‑growth‑per‑tick at the region level. 

------

## Status & disclaimer

GrowNet is an ongoing research system exploring a non‑gradient, growth‑first route toward broadly capable learning. It’s **not** a drop‑in replacement for current SOTA deep models yet; the contract’s purpose is to make the system testable, reproducible, and evolvable across languages as we iterate. 

------

### Appendix: Contract excerpts (v5 / v5.1 addendum)

- **Local learning; no backprop; two‑phase ticks; deterministic wiring; strict capacity; fallback; frozen slots.** 
- **Windowed wiring center rule; unique source count; `attach_source_neuron` for growth.** 
- **Growth policy; cooldowns; one growth per tick; metrics fields (snake_case).** 
