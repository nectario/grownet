# PR — Proximity Autowiring Policy (deterministic, policy‑layer only)

**Goal**
 Add an **optional** proximity connectivity policy that runs **after Phase‑B** (post‑propagation + growth/autowire), using a **deterministic layout** and a **spatial hash** to connect nearby neurons under a **per‑tick budget** with **cooldowns**, and optional **stabilize/decay** rules.
 **No core types are changed**; the policy lives in a sidecar module. All identifiers are descriptive; **no leading underscores** in Python/Mojo public names; **no single/double‑character identifiers** anywhere. 

**Non‑goals**

- No change to tick discipline, slot selection, growth ladder, or tract/mesh semantics.
- No runtime 3D coordinates stored on core objects (layout is a pure function).
- No probabilistic behavior without a seeded **Region RNG**.

------

## 0) One‑line integration point (per language)

Invoke **once per tick** after Phase‑B and **before** `end_tick()` / `bus.decay()`:

- **Python**

  ```python
  from policy.proximity_connectivity import ProximityEngine
  if self.proximity_config and self.proximity_config.proximity_connect_enabled:
      ProximityEngine.apply(self, self.proximity_config)
  ```

- **Java**

  ```java
  if (proximityConfig != null && proximityConfig.isEnabled()) {
      ProximityEngine.apply(region, proximityConfig, DeterministicLayout::position);
  }
  ```

- **C++**

  ```cpp
  if (proximity_config && proximity_config->proximityConnectEnabled) {
      ProximityEngine::Apply(*this, *proximity_config);
  }
  ```

- **Mojo**

  ```mojo
  if self.proximity_config.proximity_connect_enabled:
      ProximityEngine.apply(self, self.proximity_config)
  ```

> Alternative: register `ProximityEngine.apply` as a **post‑propagation hook** and invoke the hook list here. 

------

## 1) Config — identical fields in all languages

`ProximityConfig`:

- `proximity_connect_enabled: bool = false`
- `proximity_radius: double = 1.0` *(layout units; see §2)*
- `proximity_function: enum { STEP, LINEAR, LOGISTIC } = STEP`
- `linear_exponent_gamma: double = 1.0`
- `logistic_steepness_k: double = 4.0`
- `proximity_max_edges_per_tick: int = 128`
- `proximity_cooldown_ticks: int = 5`
- `development_window_start: long = 0` *(inclusive)*
- `development_window_end: long = Long.MAX_VALUE` *(inclusive)*
- `stabilization_hits: int = 3`
- `decay_if_unused: bool = true`
- `decay_half_life_ticks: int = 200`
- `candidate_layers: optional set<int>` *(empty → all trainable layers)*
- `record_mesh_rules_on_cross_layer: bool = true`

Validation:

- `proximity_radius > 0`.
- If `proximity_function != STEP`, a **seeded Region RNG is required** (see §4 Determinism).

------

## 2) Deterministic layout (pure function; no core fields)

```
DeterministicLayout.position(region_name, layer_index, neuron_index, layer_height, layer_width) -> (x, y, z)
```

- In‑plane grid spacing: `grid_spacing = 1.2`
- Inter‑layer spacing: `layer_spacing = 4.0`
- 2D layers: `(row, col)` → centered plane.
- Non‑2D: deterministic ceil‑sqrt grid.
- **Units:** `proximity_radius` is measured in these **layout units** (so a radius of `~1.2` roughly spans adjacent pixels in‑plane; `~4.0` reaches the next layer’s plane).
- No randomness; same math in all languages. 

------

## 3) Spatial hash grid (fast neighbor search)

- Cell size = `proximity_radius`.
- Hash key: `floor(position / cell_size)` for `(x,y,z)`; each bucket holds neuron ids.
- `near(position)` scans **27 cells** (3×3×3); the engine then checks *true* Euclidean distance ≤ radius before considering an edge.
- Rebuilt **once per tick** for the candidate layers.

------

## 4) Engine behavior & determinism

**High‑level pseudocode** (descriptive names; Python/Mojo have **no** leading underscores):

```
apply(region, config):
  if not config.proximity_connect_enabled: return 0

  step = region.bus.current_step
  if step < config.development_window_start or step > config.development_window_end: return 0

  candidate_layers = config.candidate_layers or all_trainable_layers(region)

  grid = SpatialHash(cell_size = config.proximity_radius)
  for layer_index in candidate_layers:
    for neuron_index in region.layer(layer_index).neuron_indices:
      pos = layout.position(region.name, layer_index, neuron_index, H, W)
      grid.insert((layer_index, neuron_index), pos)

  edges_added = 0
  for layer_index in candidate_layers:
    for neuron_index in region.layer(layer_index).neuron_indices:
      if in_cooldown(layer_index, neuron_index): continue
      origin_pos = layout.position(...)
      for (neighbor_layer, neighbor_neuron) in grid.near(origin_pos):
        if same_neuron: continue
        if already_connected(layer_index, neuron_index, neighbor_layer, neighbor_neuron): continue
        neighbor_pos = layout.position(...)
        dist = euclidean(origin_pos, neighbor_pos)
        if dist > config.proximity_radius: continue
        p = probability_from_distance(dist, config)   # STEP | LINEAR | LOGISTIC
        if bernoulli_with_region_rng(p):              # STEP needs no RNG (p∈{0,1}); others require seeded RNG
          connect_neurons(source, dest, record_mesh_rules_on_cross_layer=config.record_mesh_rules_on_cross_layer)
          set_cooldown_for(source, step); set_cooldown_for(dest, step)
          edges_added += 1
          if edges_added >= config.proximity_max_edges_per_tick: return edges_added

  return edges_added
```

**Probability functions**

- **STEP**: connect iff `distance ≤ radius` (p ∈ {0,1}) — **no RNG required**.
- **LINEAR**: `p = clamp(1 − distance / radius, 0, 1)^linear_exponent_gamma`.
- **LOGISTIC**: `p = 1 / (1 + exp(logistic_steepness_k * (distance − radius)))`.

**Determinism**

- **Mandatory**: for `LINEAR`/`LOGISTIC`, draws must come from the **Region RNG** (seeded).
- **Prohibited**: no fallback to global/random sources in any language (Python’s `random.random()` etc.).
- **Iteration order is fixed** (layer index, then neuron index) → consistent picks under the same RNG seed and budget. 

**Directionality**

- Proximity edges are **directed synapses**. The engine may form `A→B` this tick and `B→A` later if allowed by budget/cooldown (desired for reciprocal bundles).

**Mesh rules**

- If a new edge is **cross‑layer** and `record_mesh_rules_on_cross_layer=true`, record a mesh rule `(src_layer → dst_layer, p=1.0, deterministic)` so **future growth inherits** inbound/outbound topology. Same‑layer (lateral) edges do **not** create mesh rules.

**Optional stabilize/decay**

- If the synapse API exposes usage (e.g., `last_seen_tick`), you may:
   `strength *= 0.5^(delta_ticks / decay_half_life_ticks)` per tick of inactivity; delete under epsilon.
- If usage is not exposed, **do not modify weights** (topology remains deterministic).

------

## 5) Public API surfaces to **ADAPT** (per repo)

Prefer your canonical helpers if present:

- `region.has_edge(src_layer, src_neuron, dst_layer, dst_neuron)`
- `region.connect_neurons(src_layer, src_neuron, dst_layer, dst_neuron, feedback=false)`
- `region.record_mesh_rule_for(src_layer, dst_layer, probability=1.0, feedback=false)`
- `region.bus.get_current_step()` (or `bus.current_step`)
- `region.rng` access (seeded; deterministic)

Fallbacks (only for test scaffolding) may scan synapses; mark those with **ADAPT** and replace with canonical methods during wiring.

------

## 6) File plan (all languages)

**Python**

```
src/python/policy/proximity_connectivity.py       # ProximityConfig + DeterministicLayout + SpatialHash + ProximityEngine
src/python/tests/test_proximity_policy.py         # disabled/step/budget/cooldown/determinism/directionality
```

**Java**

```
src/java/ai/nektron/grownet/policy/ProximityConfig.java
src/java/ai/nektron/grownet/policy/DeterministicLayout.java
src/java/ai/nektron/grownet/policy/SpatialHash.java
src/java/ai/nektron/grownet/policy/ProximityEngine.java
src/test/java/ai/nektron/grownet/ProximityPolicyTests.java
```

**C++**

```
src/cpp/include/ProximityConfig.h
src/cpp/include/DeterministicLayout.h
src/cpp/include/SpatialHash.h
src/cpp/src/ProximityEngine.cpp                 # ProximityEngine::Apply(Region&)
tests/proximity_policy_test.cpp
```

**Mojo**

```
src/mojo/policy/proximity_connectivity.mojo     # struct + fn; typed params; snake_case
src/mojo/tests/proximity_policy_test.mojo
```

> Loops use `layer_index`, `neuron_index`, `offset_x/y/z`, `outgoing_synapse_index`, etc.—**never** `i/j/k` or `dx/dy/dz`. 

------

## 7) Minimal reference implementation (Python skeleton)

> Deterministic only: **no RNG fallback**. Use `region.rng.random()` for probabilistic modes, STEP works without RNG.

```python
from dataclasses import dataclass
from math import floor, exp
from typing import Dict, Tuple, Iterable

@dataclass
class ProximityConfig:
    proximity_connect_enabled: bool = False
    proximity_radius: float = 1.0
    proximity_function: str = "STEP"      # "STEP" | "LINEAR" | "LOGISTIC"
    linear_exponent_gamma: float = 1.0
    logistic_steepness_k: float = 4.0
    proximity_max_edges_per_tick: int = 128
    proximity_cooldown_ticks: int = 5
    development_window_start: int = 0
    development_window_end: int = 2**63 - 1
    stabilization_hits: int = 3
    decay_if_unused: bool = True
    decay_half_life_ticks: int = 200
    candidate_layers: Tuple[int, ...] = tuple()
    record_mesh_rules_on_cross_layer: bool = True

class DeterministicLayout:
    layer_spacing = 4.0
    grid_spacing = 1.2
    @staticmethod
    def position(region_name: str, layer_index: int, neuron_index: int, layer_height: int = 0, layer_width: int = 0):
        if layer_height > 0 and layer_width > 0:
            row_index, col_index = divmod(neuron_index, layer_width)
            x = (col_index - (layer_width - 1) / 2.0) * DeterministicLayout.grid_spacing
            y = ((layer_height - 1) / 2.0 - row_index) * DeterministicLayout.grid_spacing
            z = float(layer_index) * DeterministicLayout.layer_spacing
            return (x, y, z)
        grid_side = int((neuron_index + 1) ** 0.5)
        if grid_side * grid_side < neuron_index + 1: grid_side += 1
        row_index = neuron_index // grid_side
        col_index = neuron_index % grid_side
        x = (col_index - (grid_side - 1) / 2.0) * DeterministicLayout.grid_spacing
        y = ((grid_side - 1) / 2.0 - row_index) * DeterministicLayout.grid_spacing
        z = float(layer_index) * DeterministicLayout.layer_spacing
        return (x, y, z)

class SpatialHash:
    def __init__(self, cell_size: float):
        self.cell_size = cell_size
        self.cells: Dict[Tuple[int, int, int], list] = {}
    def key_for_position(self, p): return (floor(p[0]/self.cell_size), floor(p[1]/self.cell_size), floor(p[2]/self.cell_size))
    def insert(self, item_key, pos): self.cells.setdefault(self.key_for_position(pos), []).append(item_key)
    def near(self, pos): 
        base = self.key_for_position(pos)
        for oz in (-1, 0, 1):
            for oy in (-1, 0, 1):
                for ox in (-1, 0, 1):
                    k = (base[0]+ox, base[1]+oy, base[2]+oz)
                    if k in self.cells:
                        for item in self.cells[k]: yield item

class ProximityEngine:
    region_state: Dict[str, Dict] = {}
    @staticmethod
    def apply(region, config: ProximityConfig) -> int:
        if not config.proximity_connect_enabled: return 0
        current = region.bus.get_current_step() if hasattr(region.bus, "get_current_step") else getattr(region.bus, "current_step", 0)
        if current < config.development_window_start or current > config.development_window_end: return 0

        key = getattr(region, "name", f"region_{id(region)}")
        state = ProximityEngine.region_state.setdefault(key, {"last_attempt_step": {}})

        candidate_layers = list(config.candidate_layers) if config.candidate_layers else list(range(len(region.layers)))
        grid = SpatialHash(config.proximity_radius)
        for layer_index in candidate_layers:
            layer = region.layers[layer_index]
            height, width = getattr(layer, "height", 0), getattr(layer, "width", 0)
            for neuron_index, _neuron in enumerate(layer.get_neurons()):
                grid.insert((layer_index, neuron_index), DeterministicLayout.position(key, layer_index, neuron_index, height, width))

        rng = getattr(region, "rng", None)
        def prob(dist: float) -> float:
            if config.proximity_function == "STEP": return 1.0 if dist <= config.proximity_radius else 0.0
            unit = max(0.0, 1.0 - dist / max(config.proximity_radius, 1e-12))
            if config.proximity_function == "LINEAR": return unit ** max(config.linear_exponent_gamma, 1e-12)
            return 1.0 / (1.0 + exp(config.logistic_steepness_k * (dist - config.proximity_radius)))

        edges_added = 0
        for layer_index in candidate_layers:
            layer = region.layers[layer_index]
            height, width = getattr(layer, "height", 0), getattr(layer, "width", 0)
            for neuron_index, _neuron in enumerate(layer.get_neurons()):
                last = state["last_attempt_step"].get((layer_index, neuron_index), -10**9)
                if (current - last) < config.proximity_cooldown_ticks: continue
                origin = DeterministicLayout.position(key, layer_index, neuron_index, height, width)
                for neighbor_layer, neighbor_neuron in grid.near(origin):
                    if neighbor_layer == layer_index and neighbor_neuron == neuron_index: continue
                    if region.has_edge(layer_index, neuron_index, neighbor_layer, neighbor_neuron): continue  # ADAPT if needed
                    nh_layer = region.layers[neighbor_layer]
                    neighbor = DeterministicLayout.position(key, neighbor_layer, neighbor_neuron,
                                                            getattr(nh_layer, "height", 0), getattr(nh_layer, "width", 0))
                    dx, dy, dz = origin[0]-neighbor[0], origin[1]-neighbor[1], origin[2]-neighbor[2]
                    dist = (dx*dx + dy*dy + dz*dz) ** 0.5
                    if dist > config.proximity_radius: continue
                    p = prob(dist)
                    if p < 1.0:
                        if rng is None: raise RuntimeError("ProximityEngine: probabilistic mode requires a seeded region RNG")
                        if rng.random() >= p: continue
                    region.connect_neurons(layer_index, neuron_index, neighbor_layer, neighbor_neuron, False)  # ADAPT if needed
                    if config.record_mesh_rules_on_cross_layer and layer_index != neighbor_layer:
                        region.record_mesh_rule_for(layer_index, neighbor_layer, 1.0, False)                 # ADAPT if needed
                    state["last_attempt_step"][(layer_index, neuron_index)] = current
                    state["last_attempt_step"][(neighbor_layer, neighbor_neuron)] = current
                    edges_added += 1
                    if edges_added >= config.proximity_max_edges_per_tick: return edges_added
        return edges_added
```

------

## 8) Tests (all languages; adapt names to your harness)

1. **Disabled policy** → `edges_added == 0`.
2. **Budget respected** → with dense local neighborhood and `proximity_max_edges_per_tick = k`, assert `edges_added == k`.
3. **Cooldown honored** → same pair not retried within `proximity_cooldown_ticks`.
4. **Determinism** → same seed, same candidate set, same radius → identical edge set across runs.
5. **No RNG in probabilistic modes** → with `LINEAR` or `LOGISTIC` and `region.rng == None`, assert a **clear error**; with a seeded RNG, assert it passes.
6. **Directionality** → two neurons within radius: first pass adds one direction (budget 1); second pass may add the reverse (budget permitting). 

------

## 9) Demos (one per language)

Create a minimal `8×8 → 8×8` region and run:

- `proximity_function="STEP"`, `radius ≈ 1.5 * grid_spacing`, budget 8
- Print: edges added, sample `(src_layer, src_neuron) → (dst_layer, dst_neuron)` pairs.
- Toggle to `LINEAR` with small gamma (`1.0`) and again with larger gamma (`2.0`) to show near‑center concentration.
- Keep code **deterministic** (seeded RNG) and runtime **pure** (policy module only).

------

## 10) Docs & style

- Add **“Proximity Autowiring (Optional Policy)”** to `docs/GROWTH.md`: when it runs, how it stays deterministic, how mesh rules are recorded for cross‑layer edges only, how budgets/cooldowns stabilize growth.
- Add a line to `READ_ORDER.md` after growth/autowire.
- Add an FAQ entry: “How do I enable proximity autowiring?” with a 5‑line snippet.
- Ensure style gates pass: **no leading underscores** (Python/Mojo), **no single/double‑character identifiers** anywhere, Mojo uses `struct` + `fn` with typed params. 

------

## 11) Performance notes

- Build spatial hash **once per tick**; O(N) insert + O(N) neighborhood probes.
- Budget + cooldown bound work per tick, preventing graph explosion.
- All computation is **CPU‑deterministic**; no I/O; no extra allocations on core types.

------

## 12) Risk & mitigation

- **Edge flood** if radius too large: mitigated by budget + cooldown + development window.
- **Cross‑layer over‑connect**: set `record_mesh_rules_on_cross_layer=false` or tighten radius/layers via `candidate_layers`.
- **Non‑determinism**: prevented by prohibiting RNG fallbacks and fixing iteration order.

------

## 13) Definition of Done

- `ProximityConfig`, `DeterministicLayout`, `SpatialHash`, `ProximityEngine.apply(...)` exist in all four languages.
- One‑line integration is wired after Phase‑B in each `Region.tick` path.
- Tests green in all languages: disabled/budget/cooldown/determinism/no‑RNG‑fallback/directionality.
- Docs updated; style gates pass.
- Core types untouched; mesh & tracts semantics preserved.

------

## 14) Runbook (CLI)

1. `git checkout -b pr/proximity-policy`
2. Create files listed in §6; paste code (adapting **ADAPT** points to your repo’s method names).
3. Wire the **one‑liner** in each language’s tick (post‑Phase‑B).
4. Run gates & tests:
   - `pre-commit run --all-files`
   - `pytest -q`
   - `mvn -q -Dtest=ProximityPolicyTests test` (or Gradle)
   - `cmake -S . -B build && cmake --build build -j && ctest --test-dir build --output-on-failure`
   - `mojo run src/mojo/tests/proximity_policy_test.mojo`
5. Open PR using this text.

