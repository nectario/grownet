# PR — Proximity Autowiring Policy (deterministic, policy‑layer only)

**Goal**
 Add an **optional** proximity connectivity policy that runs **after Phase‑B** (post‑propagation + growth/autowire), using a **deterministic layout** and a **spatial hash** to connect nearby neurons under a **per‑tick budget** with **cooldowns**, and optional **stabilize/decay** rules.
 **No core types are changed**; the policy lives in a sidecar module.
 All identifiers are **descriptive** and **no names start with `_`** in Python/Mojo.

------

## 0) One‑line integration point (per language)

Call this **once per tick** after Phase‑B and before `end_tick()` / `bus.decay()`:

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
  if (proximity_config && proximity_config->proximity_connect_enabled) {
      ProximityEngine::Apply(*this, *proximity_config);
  }
  ```

- **Mojo**

  ```mojo
  if self.proximity_config.proximity_connect_enabled:
      ProximityEngine.apply(self, self.proximity_config)
  ```

> If you prefer, register the engine as a **post‑propagation hook** and invoke the hook list here.

------

## 1) Config — identical fields in all languages

`ProximityConfig`:

- `proximity_connect_enabled: bool = false`
- `proximity_radius: double = 1.0`
- `proximity_function: enum { STEP, LINEAR, LOGISTIC } = STEP`
- `linear_exponent_gamma: double = 1.0`
- `logistic_steepness_k: double = 4.0`
- `proximity_max_edges_per_tick: int = 128`
- `proximity_cooldown_ticks: int = 5`
- `development_window_start: long = 0`  *(inclusive)*
- `development_window_end: long = Long.MAX_VALUE` *(inclusive)*
- `stabilization_hits: int = 3`
- `decay_if_unused: bool = true`
- `decay_half_life_ticks: int = 200`
- `candidate_layers: optional set<int>` *(empty → all trainable layers)*
- `record_mesh_rules_on_cross_layer: bool = true`

------

## 2) Deterministic layout (pure function, no fields on core types)

```
DeterministicLayout.position(region_name, layer_index, neuron_index, layer_height, layer_width) -> (x, y, z)
```

- `z = layer_index * layer_spacing` (default `4.0`)
- 2D layers: `(row, col)` mapped to centered plane with `grid_spacing = 1.2`
- non‑2D layers: deterministic centered grid (ceil sqrt rule)
- No randomness. All languages implement identical math.

------

## 3) Spatial hash grid (fast neighbor search)

- Cell size = `proximity_radius`.
- Key `(cell_x, cell_y, cell_z) = floor(position / cell_size)`; bucket map → list of neuron ids.
- `near(position, radius)` scans **27 neighbors** (3×3×3) via offsets `offset_x ∈ {−1,0,1}` etc.
- Implementation is **language‑local** and straightforward.

------

## 4) Engine behavior

**Pseudocode (descriptive identifiers, no leading underscores):**

```
apply(region, config):

  if not config.proximity_connect_enabled:
      return 0

  current_step = region.bus.current_step
  if current_step < config.development_window_start or current_step > config.development_window_end:
      return 0

  select candidate_layers from config or use all trainable layers

  # Build spatial grid once per tick
  grid = SpatialHash(cell_size = config.proximity_radius)
  for each layer_index in candidate_layers:
      layer = region.layers[layer_index]
      for each neuron_index in layer.neuron_indices:
          position = layout.position(region.name, layer_index, neuron_index, layer.height, layer.width)
          grid.insert((layer_index, neuron_index), position)

  edges_added = 0

  for each layer_index in candidate_layers:
      for each neuron_index in layer.neuron_indices:
          if in_cooldown(neuron_index, layer_index): continue
          origin_position = layout.position(...)
          for each (neighbor_layer_index, neighbor_neuron_index) in grid.near(origin_position, config.proximity_radius):
              if same neuron: continue
              if already_connected(source=(layer_index,neuron_index), dest=(neighbor_layer_index,neighbor_neuron_index)): continue
              neighbor_position = layout.position(...)
              distance_value = euclidean_distance(origin_position, neighbor_position)
              if distance_value > config.proximity_radius: continue
              probability_value = choose_probability(distance_value, config)
              if bernoulli(region_rng, probability_value):
                  connect_neurons(source, dest, record_mesh_rules_on_cross_layer)
                  set_cooldown_for(source, current_step); set_cooldown_for(dest, current_step)
                  edges_added += 1
                  if edges_added >= config.proximity_max_edges_per_tick:
                      return edges_added

  return edges_added
```

**Probability functions**

- **STEP**: connect if `distance ≤ radius`.
- **LINEAR**: `probability = clamp(1 − distance / radius, 0, 1) ^ linear_exponent_gamma`.
- **LOGISTIC**: `probability = 1 / (1 + exp(logistic_steepness_k * (distance − radius)))`.

**Stabilize/decay (optional)**

- If `decay_if_unused == true` and the synapse API exposes `last_seen_tick` or `hit_count`, decay unused edges by:
   `strength *= 0.5^(delta_ticks / decay_half_life_ticks)`.
   Delete if below `epsilon`.
- If the API does not expose usage, skip decay (still deterministic).

**Determinism & mesh rules**

- Use the **Region RNG** (existing seed) for Bernoulli draws.
- If a new edge crosses layers and `record_mesh_rules_on_cross_layer == true`, record a mesh rule `(source_layer → dest_layer, p = 1.0)` so future growth inherits wiring deterministically.

------

## 5) File plan (by language)

### Python

```
src/python/policy/proximity_connectivity.py       # ProximityConfig, DeterministicLayout, SpatialHash, ProximityEngine
src/python/tests/test_proximity_policy.py
```

**Python skeleton (all names public‑style, no short identifiers):**

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
    def position(region_name: str, layer_index: int, neuron_index: int, layer_height: int = 0, layer_width: int = 0) -> Tuple[float, float, float]:
        if layer_height > 0 and layer_width > 0:
            row_index, col_index = divmod(neuron_index, layer_width)
            x_coord = (col_index - (layer_width - 1) / 2.0) * DeterministicLayout.grid_spacing
            y_coord = ((layer_height - 1) / 2.0 - row_index) * DeterministicLayout.grid_spacing
            z_coord = float(layer_index) * DeterministicLayout.layer_spacing
            return (x_coord, y_coord, z_coord)
        # fallback grid for non‑2D layers
        grid_side = int((neuron_index + 1) ** 0.5)
        if grid_side * grid_side < neuron_index + 1:
            grid_side += 1
        row_index = neuron_index // grid_side
        col_index = neuron_index % grid_side
        x_coord = (col_index - (grid_side - 1) / 2.0) * DeterministicLayout.grid_spacing
        y_coord = ((grid_side - 1) / 2.0 - row_index) * DeterministicLayout.grid_spacing
        z_coord = float(layer_index) * DeterministicLayout.layer_spacing
        return (x_coord, y_coord, z_coord)

class SpatialHash:
    def __init__(self, cell_size: float):
        self.cell_size = cell_size
        self.cells: Dict[Tuple[int, int, int], list] = {}

    def key_for_position(self, position: Tuple[float, float, float]) -> Tuple[int, int, int]:
        return (floor(position[0] / self.cell_size),
                floor(position[1] / self.cell_size),
                floor(position[2] / self.cell_size))

    def insert(self, item_key, position) -> None:
        hash_key = self.key_for_position(position)
        self.cells.setdefault(hash_key, []).append(item_key)

    def near(self, position, radius) -> Iterable:
        base = self.key_for_position(position)
        for offset_z in (-1, 0, 1):
            for offset_y in (-1, 0, 1):
                for offset_x in (-1, 0, 1):
                    neighbor_key = (base[0] + offset_x, base[1] + offset_y, base[2] + offset_z)
                    if neighbor_key in self.cells:
                        for item_key in self.cells[neighbor_key]:
                            yield item_key

class ProximityEngine:
    # transient state per region (cooldowns etc.)
    region_state: Dict[str, Dict] = {}

    @staticmethod
    def region_key(region) -> str:
        return getattr(region, "name", f"region_{id(region)}")

    @staticmethod
    def neuron_global_id(layer_index: int, neuron_index: int) -> Tuple[int, int]:
        return (layer_index, neuron_index)

    @staticmethod
    def euclidean_distance(a_position, b_position) -> float:
        delta_x = a_position[0] - b_position[0]
        delta_y = a_position[1] - b_position[1]
        delta_z = a_position[2] - b_position[2]
        return (delta_x * delta_x + delta_y * delta_y + delta_z * delta_z) ** 0.5

    @staticmethod
    def probability_from_distance(distance_value: float, config: ProximityConfig) -> float:
        if config.proximity_function == "STEP":
            return 1.0 if distance_value <= config.proximity_radius else 0.0
        unit = max(0.0, 1.0 - distance_value / max(config.proximity_radius, 1e-12))
        if config.proximity_function == "LINEAR":
            return unit ** max(config.linear_exponent_gamma, 1e-12)
        # LOGISTIC
        return 1.0 / (1.0 + exp(config.logistic_steepness_k * (distance_value - config.proximity_radius)))

    @staticmethod
    def apply(region, config: ProximityConfig) -> int:
        if not config.proximity_connect_enabled:
            return 0
        current_step = region.bus.get_current_step() if hasattr(region.bus, "get_current_step") else getattr(region.bus, "current_step", 0)
        if current_step < config.development_window_start or current_step > config.development_window_end:
            return 0

        region_key_value = ProximityEngine.region_key(region)
        state = ProximityEngine.region_state.setdefault(region_key_value, {"last_attempt_step": {}})

        grid = SpatialHash(config.proximity_radius)
        candidate_layers = list(config.candidate_layers) if config.candidate_layers else list(range(len(region.layers)))

        for layer_index in candidate_layers:
            layer = region.layers[layer_index]
            height = getattr(layer, "height", 0)
            width = getattr(layer, "width", 0)
            neuron_list = layer.get_neurons()
            for neuron_index in range(len(neuron_list)):
                position = DeterministicLayout.position(region_key_value, layer_index, neuron_index, height, width)
                grid.insert((layer_index, neuron_index), position)

        region_random = getattr(region, "rng", None)

        def draw_bernoulli(probability_value: float) -> bool:
            if probability_value <= 0.0:
                return False
            if probability_value >= 1.0:
                return True
            if region_random is not None:
                return region_random.random() < probability_value
            import random
            return random.random() < probability_value

        edges_added = 0

        for layer_index in candidate_layers:
            layer = region.layers[layer_index]
            height = getattr(layer, "height", 0)
            width = getattr(layer, "width", 0)
            neuron_list = layer.get_neurons()
            for neuron_index in range(len(neuron_list)):
                global_id = ProximityEngine.neuron_global_id(layer_index, neuron_index)
                last_step = state["last_attempt_step"].get(global_id, -10**9)
                if (current_step - last_step) < config.proximity_cooldown_ticks:
                    continue
                origin_position = DeterministicLayout.position(region_key_value, layer_index, neuron_index, height, width)
                for neighbor_layer_index, neighbor_neuron_index in grid.near(origin_position, config.proximity_radius):
                    if neighbor_layer_index == layer_index and neighbor_neuron_index == neuron_index:
                        continue
                    if ProximityEngine.already_connected(region, layer_index, neuron_index, neighbor_layer_index, neighbor_neuron_index):
                        continue
                    neighbor_layer = region.layers[neighbor_layer_index]
                    neighbor_height = getattr(neighbor_layer, "height", 0)
                    neighbor_width = getattr(neighbor_layer, "width", 0)
                    neighbor_position = DeterministicLayout.position(region_key_value, neighbor_layer_index, neighbor_neuron_index, neighbor_height, neighbor_width)
                    distance_value = ProximityEngine.euclidean_distance(origin_position, neighbor_position)
                    if distance_value > config.proximity_radius:
                        continue
                    probability_value = ProximityEngine.probability_from_distance(distance_value, config)
                    if draw_bernoulli(probability_value):
                        ProximityEngine.connect_neurons(region, layer_index, neuron_index, neighbor_layer_index, neighbor_neuron_index, config.record_mesh_rules_on_cross_layer)
                        state["last_attempt_step"][global_id] = current_step
                        state["last_attempt_step"][ProximityEngine.neuron_global_id(neighbor_layer_index, neighbor_neuron_index)] = current_step
                        edges_added += 1
                        if edges_added >= config.proximity_max_edges_per_tick:
                            return edges_added
        return edges_added

    @staticmethod
    def already_connected(region, src_layer_index: int, src_neuron_index: int, dst_layer_index: int, dst_neuron_index: int) -> bool:
        source_neuron = region.layers[src_layer_index].get_neurons()[src_neuron_index]
        for synapse in source_neuron.get_outgoing():
            same_target = (synapse.get_target_index() == dst_neuron_index)
            same_layer = (getattr(synapse, "target_layer", dst_layer_index) == dst_layer_index)
            if same_target and same_layer:
                return True
        return False

    @staticmethod
    def connect_neurons(region, src_layer_index: int, src_neuron_index: int, dst_layer_index: int, dst_neuron_index: int, record_mesh_rule: bool) -> None:
        source_neuron = region.layers[src_layer_index].get_neurons()[src_neuron_index]
        # ADAPT this construction to your Synapse API
        if hasattr(region, "create_synapse"):
            new_synapse = region.create_synapse(dst_layer_index, dst_neuron_index, feedback=False)
        else:
            from src.python.synapse import Synapse  # ADAPT import path
            new_synapse = Synapse(dst_neuron_index, False)
            setattr(new_synapse, "target_layer", dst_layer_index)
        source_neuron.get_outgoing().append(new_synapse)
        if record_mesh_rule and src_layer_index != dst_layer_index and hasattr(region, "record_mesh_rule_for"):
            region.record_mesh_rule_for(src_layer_index, dst_layer_index, probability=1.0, feedback=False)
```

*(Java/C++/Mojo mirrors this exactly; names remain descriptive and public.)*

### Java / C++ / Mojo file lists

- **Java**

  ```
  src/java/ai/nektron/grownet/policy/ProximityConfig.java
  src/java/ai/nektron/grownet/policy/DeterministicLayout.java
  src/java/ai/nektron/grownet/policy/SpatialHash.java
  src/java/ai/nektron/grownet/policy/ProximityEngine.java
  src/test/java/ai/nektron/grownet/ProximityPolicyTests.java
  ```

- **C++**

  ```
  src/cpp/include/ProximityConfig.h
  src/cpp/include/DeterministicLayout.h
  src/cpp/include/SpatialHash.h
  src/cpp/src/ProximityEngine.cpp
  tests/proximity_policy_test.cpp
  ```

- **Mojo**

  ```
  src/mojo/policy/proximity_connectivity.mojo  # struct ProximityConfig, layout, grid, engine
  src/mojo/tests/proximity_policy_test.mojo
  ```

All loops should use names like `layer_index`, `neuron_index`, `offset_x`, `offset_y`, `offset_z`, `outgoing_synapse_index`, etc.—**never** `i/j/k` or `dx/dy/dz`.

------

## 6) Tests

1. **Disabled policy** → `edges_added == 0`.
2. **Budget respected** → `edges_added ≤ proximity_max_edges_per_tick`.
3. **STEP vs LINEAR vs LOGISTIC**: shape checks (LINEAR with exponent > 1 concentrates near small distances; LOGISTIC smoother near the boundary).
4. **Cooldown honored**: same pair is not retried within `proximity_cooldown_ticks`.
5. **Determinism**: identical edges with same Region RNG seed.
6. **Optional stabilize/decay**: if the synapse API exposes usage timestamps, verify decay and deletion; otherwise skip.

------

## 7) Docs

- Add a short section to `docs/GROWTH.md`: “**Proximity Autowiring (Optional Policy)**” including when it runs and guardrails (deterministic, budgeted, not counted as growth, mesh rules recorded for cross‑layer edges if enabled).
- Add a line in `READ_ORDER.md` after the growth/autowire section.
- Add an FAQ entry: “How do I enable proximity autowiring?” with a minimal config snippet.

------

## Style & parity guardrails

- **No leading underscores** in **Python and Mojo** function, class, or variable names—across all new code.
- **No single/double‑character identifiers** anywhere (including loops and temporaries).
- Python/Mojo: **snake_case** public API; Mojo uses `struct` + `fn` with typed parameters.
- **Deterministic only**; uses Region RNG if a probability draw is required.
- **Core remains pure**; the policy is optional and lives in a sidecar module.

------

# Codex: CLI or Web?

**Use Codex CLI** for this PR. Here’s why:

- **Multi‑language tree edits** (Python, Java, C++, Mojo) with new files and test wiring are easier to stage and verify locally.
- You can **run pre‑commit**, linters, and unit tests before pushing (ensures short‑identifier guard and no‑underscore rules pass).
- CLI handles **large diffs** and path‑sensitive operations (creating directories, adding CMake/Maven test files) more reliably than a web prompt.

**When Codex Web is okay:** tiny patches to a single language/file, or exploratory refactors. For this, it’s a full, multi‑file PR—go CLI.

------

## Tiny runbook for Codex CLI

1. **Create a working branch**: `git checkout -b pr/proximity-policy`.
2. **Hand Codex this PR text** and your repo root; scope tasks:
   - Add the files listed above in each language.
   - Wire the one‑line call in the tick after Phase‑B.
   - Add tests and register them with your build (Maven/CTest/Mojo test runner).
3. **Run gates**:
   - `pre-commit run --all-files` (short‑identifier + no‑underscore rules should pass).
   - Build and run tests for each language.
4. **Open the PR** with a summary referencing this document.

