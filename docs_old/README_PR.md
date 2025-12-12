# PR — Proximity Autowiring Policy (deterministic, policy‑layer only) — v2

**Goal**  
Add an **optional** proximity connectivity policy that runs **after Phase‑B** (post‑propagation + growth/autowire),
using a **deterministic layout** and a **spatial hash** to connect nearby neurons under a **per‑tick budget** with
**cooldowns**, and optional **stabilize/decay** rules. **No core types are changed**; the policy lives in a sidecar module.
All identifiers are **descriptive** and, for Python/Mojo, **no names start with `_`**.

---

## 0) One‑line integration point (per language)

Call once per tick **after Phase‑B** and **before** `end_tick()` / `bus.decay()`:

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

> Alternative: register `ProximityEngine.apply` as a **post‑propagation hook** and invoke hooks here.

---

## 1) Config — identical fields in all languages

`ProximityConfig`:
- `proximity_connect_enabled: bool = false`
- `proximity_radius: double = 1.0`  *(layout units; see §2)*
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

---

## 2) Deterministic layout (pure function, no fields on core types)

```
DeterministicLayout.position(region_name, layer_index, neuron_index, layer_height, layer_width) -> (x, y, z)
```

- `z = layer_index * layer_spacing` (default `4.0`)
- 2D layers: `(row, col)` mapped to centered plane with `grid_spacing = 1.2`
- Non‑2D layers: deterministic centered grid (ceil‑sqrt rule)
- **Units:** `proximity_radius` uses these **layout units**; default spacing keeps layers separated.
- No randomness. All languages implement identical math.

---

## 3) Spatial hash grid (fast neighbor search)

- Cell size = `proximity_radius`.
- Hash key = `floor(position / cell_size)` for `(x, y, z)`; bucket map → list of neuron ids.
- `near(position, radius)` scans **27 neighboring cells** (3×3×3) via offsets `(−1..+1)`.
- The engine still filters by **actual Euclidean distance ≤ radius**.

---

## 4) Engine behavior

**Pseudocode (descriptive identifiers; Python/Mojo have no leading underscores):**
```text
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
  `strength *= 0.5^(delta_ticks / decay_half_life_ticks)`. Delete if below epsilon.
- If the API does not expose usage, **do not** modify weights (topology only; still deterministic).

**Determinism & mesh rules**
- Use the **Region RNG** (existing seed) for LINEAR/LOGISTIC Bernoulli draws (STEP needs no RNG).
- If a new edge crosses layers and `record_mesh_rules_on_cross_layer == true`, record a mesh rule
  `(source_layer → dest_layer, p = 1.0)` so future growth inherits wiring deterministically.

**Directionality**
- Proximity edges are **directed synapses**. The engine may create `A→B` and, on a later pass, `B→A` if allowed
  by budget/cooldown (desirable for reciprocal bundles).

---

## 5) File plan (per language)

- **Python**
  ```
  src/python/policy/proximity_connectivity.py       # ProximityConfig, DeterministicLayout, SpatialHash, ProximityEngine
  src/python/tests/test_proximity_policy.py
  ```

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
  src/mojo/policy/proximity_connectivity.mojo
  src/mojo/tests/proximity_policy_test.mojo
  ```

> Loops must use names like `layer_index`, `neuron_index`, `offset_x`, `offset_y`, `offset_z`, `outgoing_synapse_index`—**never** `i/j/k` or `dx/dy/dz`.

---

## 6) Tests

1. **Disabled policy** → `edges_added == 0`.
2. **Budget respected** → `edges_added ≤ proximity_max_edges_per_tick`.
3. **Cooldown honored** → same pair not retried within `proximity_cooldown_ticks`.
4. **Determinism** → identical edges with same Region RNG seed.
5. **No RNG in probabilistic modes** → raise clear error; STEP works without RNG.
6. **Directionality** → on two neurons within radius, engine can create `A→B` then (later) `B→A`.

---

## 7) Docs

- Add “**Proximity Autowiring (Optional Policy)**” to `docs/GROWTH.md`: when it runs, determinism,
  budget, cooldown, and mesh‑rule note (cross‑layer only).
- Add a line in `READ_ORDER.md` after growth/autowire.
- Add an FAQ: “How do I enable proximity autowiring?” with a minimal config snippet.

---

## Style & parity guardrails

- **No leading underscores** in Python/Mojo public names; **no single/double‑character identifiers** anywhere.
- Python/Mojo public API in **snake_case**; Mojo uses `struct` + `fn` with typed parameters.
- **Deterministic only**; Region RNG is mandatory for probabilistic modes.

---

## Tiny runbook (CLI)

1. `git checkout -b pr/proximity-policy`
2. Add files, wire one‑line integration after Phase‑B.
3. `pre-commit run --all-files` → style gates
4. Build & run tests for Python/Java/C++/Mojo
5. Open PR
