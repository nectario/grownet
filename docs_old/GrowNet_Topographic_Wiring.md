# GrowNet – Topographic Wiring Preset (Master PR Requirement)

**Objective:**
 Add a *generic* **Topographic** wiring preset that wraps the existing `connect_layers_windowed(...)`, then deterministically assigns **distance-based synaptic weights** (Gaussian or Difference-of-Gaussians), with optional per-target **incoming normalization**. Deliver parity across **Python, Java, C++ and Mojo**, with minimal demos and tests.

**Non-goals:**

- No changes to core growth rules, tick discipline, or slot selection.
- No new runtime fields on core objects (keep core pure).
- No “retina” terminology anywhere (use “Topographic” / “center-mapped” only).

------

## 1) Public API (same semantics in all languages)

### 1.1 Config type

`TopographicConfig` (fields and defaults)

| Field                  | Type   | Default      | Notes                                        |
| ---------------------- | ------ | ------------ | -------------------------------------------- |
| `kernel_h`, `kernel_w` | int    | 7, 7         | sliding window size                          |
| `stride_h`, `stride_w` | int    | 1, 1         | window stride                                |
| `padding`              | string | `"same"`     | `"same"` or `"valid"`                        |
| `feedback`             | bool   | `false`      | pass through to underlying connect           |
| `weight_mode`          | string | `"gaussian"` | `"gaussian"` or `"dog"`                      |
| `sigma_center`         | float  | `2.0`        | Gaussian σ for center                        |
| `sigma_surround`       | float  | `4.0`        | Only used for `"dog"`                        |
| `surround_ratio`       | float  | `0.5`        | A_surround / A_center for DoG                |
| `normalize_incoming`   | bool   | `true`       | normalize incoming weights per target neuron |

**Validation rules**

- `kernel_h, kernel_w >= 1`, `stride_h, stride_w >= 1`.
- `padding in {"same","valid"}` (case-insensitive).
- `sigma_center > 0`; if `weight_mode == "dog"` then `sigma_surround > sigma_center` and `surround_ratio >= 0`.

### 1.2 Function

```
connect_layers_topographic(region, source_layer_index, destination_layer_index, config) -> int
```

**Behavior:**

1. Call the existing
    `connect_layers_windowed(source_layer_index, destination_layer_index, config.kernel_h, config.kernel_w, config.stride_h, config.stride_w, config.padding, config.feedback)`
    to build deterministic edges.
2. For each edge `(source_pixel → destination_center)`:
   - Compute squared Euclidean distance `squared_distance` between the **source pixel** and the **destination center** in the layer’s 2D grid coordinates.
   - If `config.weight_mode == "gaussian"`:
      `weight_value = exp( - squared_distance / (2 * sigma_center^2) )`
   - Else (`"dog"`):
      `weight_value = max( 0, exp(-squared_distance / (2*sigma_center^2)) - surround_ratio * exp(-squared_distance / (2*sigma_surround^2)) )`
   - Set the synapse’s weight/strength to `weight_value`.
3. If `config.normalize_incoming`:
   - For each **destination neuron**, scale its **incoming** weights so they sum to **1.0** (if the sum is > 0). Use a numerically safe epsilon (e.g., `1e-12`) to avoid division by zero.
4. Return the **int** from step (1): **number of unique source pixels** that participated in ≥ 1 window (must match `connect_layers_windowed` return).

**Critical invariants (must preserve):**

- The underlying windowed wiring continues to apply the **center-mapping with dedupe** rule when the destination is a 2D output layer.
- The function is **deterministic** (no RNG).
- Does **not** modify mesh-rule or tract semantics beyond what `connect_layers_windowed` already records.

------

## 2) Cross-language implementation details

> **ADAPT markers** indicate places where your repo may use a different method name. Keep identifiers descriptive (no 1–2 character names), and follow each language’s style guide.

### 2.1 Python

**Files to add**

- `src/python/presets/topographic_wiring.py`
- `src/python/demos/topographic_demo.py`

**Required helpers (use existing repo surfaces if present):**

- Access 2D layer geometry: `layer.height`, `layer.width`  *(ADAPT if different)*.
- Iterate neurons: `layer.get_neurons()` → list of neuron objects. *(ADAPT)*
- Source neuron → outgoing synapses: `neuron.get_outgoing()` or `neuron.outgoing`. *(ADAPT)*
- Synapse fields: target index getter and **snake_case** weight setter:
  - expected: `synapse.get_target_index()` or `synapse.target_index` *(ADAPT)*
  - weight: `synapse.set_strength_value(value)` or `synapse.weight = value` *(ADAPT; earlier PRs used `get_strength_value` / `set_strength_value`)*

**Demo (`topographic_demo.py`):**

- Build `16×16` input → `16×16` output.
- `config = TopographicConfig(kernel=(7,7), stride=(1,1), padding="same", weight_mode="gaussian", sigma_center=2.0, normalize_incoming=True)`.
- Call `connect_layers_topographic(...)`.
- Print:
  - unique sources returned,
  - min/avg/max incoming weight for a few destination indices (e.g., center, corner),
  - sum of incoming weights (should be 1.0 ± 1e-6).

### 2.2 Java

**Files to add**

- `src/java/ai/nektron/grownet/preset/TopographicConfig.java` (builder pattern)
- `src/java/ai/nektron/grownet/preset/TopographicWiring.java`
- `src/java/ai/nektron/grownet/demo/TopographicDemo.java`

**Needed repo surfaces (ADAPT):**

- `Region.connectLayersWindowed(int sourceLayerIndex, int destinationLayerIndex, int kernelHeight, int kernelWidth, int strideHeight, int strideWidth, String padding, boolean feedback)`
- `Layer.getHeight()/getWidth()` for 2D layers (or `OutputLayer2D` accessors)
- `Layer.getNeurons()` → list
- `Neuron.getOutgoing()` → list of Synapse
- `Synapse.getTargetIndex()` and `Synapse.setStrengthValue(double)`

**Demo main:**

- Same network as Python; log selected incoming sums.

### 2.3 C++

**Files to add**

- `src/cpp/include/TopographicWiring.h`
- `src/cpp/src/TopographicWiring.cpp`
- `src/cpp/demo_topographic.cpp`

**API (header):**

```cpp
struct TopographicConfig {
  int kernel_h = 7, kernel_w = 7;
  int stride_h = 1, stride_w = 1;
  std::string padding = "same";
  bool feedback = false;
  std::string weight_mode = "gaussian"; // or "dog"
  double sigma_center = 2.0;
  double sigma_surround = 4.0;
  double surround_ratio = 0.5;
  bool normalize_incoming = true;
};

int connectLayersTopographic(Region& region,
                             int source_layer_index,
                             int destination_layer_index,
                             const TopographicConfig& config);
```

**Needed repo surfaces (ADAPT):**

- `int Region::connectLayersWindowed(int sourceLayerIndex, int destinationLayerIndex, int kernelHeight, int kernelWidth, int strideHeight, int strideWidth, const std::string& padding, bool feedback)`
- 2D size: `layer->height()` / `layer->width()` or equivalent
- Access to neurons and outgoing edges: `layer->getNeurons()`, `neuron->outgoing()`
- `Synapse` weight setter: `synapse.set_strength_value(double)` or `synapse.setWeight(double)` (ADAPT)
- Getter for synapse target index: `synapse.target_index()` (ADAPT)

**Demo:**

- Same setup; print incoming sums for a few destination indexes.

### 2.4 Mojo

**Files to add**

- `src/mojo/topographic_wiring.mojo`
- `src/mojo/tests/topographic_demo.mojo`

**Mojo signatures (typed, snake_case, no leading underscores):**

```mojo
struct TopographicConfig:
    var kernel_h: Int = 7
    var kernel_w: Int = 7
    var stride_h: Int = 1
    var stride_w: Int = 1
    var padding: String = "same"
    var feedback: Bool = False
    var weight_mode: String = "gaussian"
    var sigma_center: Float64 = 2.0
    var sigma_surround: Float64 = 4.0
    var surround_ratio: Float64 = 0.5
    var normalize_incoming: Bool = True

fn connect_layers_topographic(
    region: any,
    source_layer_index: Int,
    destination_layer_index: Int,
    config: TopographicConfig
) -> Int:
    # 1) windowed connect
    let unique_source_count = region.connect_layers_windowed(
        source_layer_index, destination_layer_index,
        config.kernel_h, config.kernel_w,
        config.stride_h, config.stride_w,
        config.padding, config.feedback)

    # 2) distance-based weights
    # ADAPT: accessors for height/width, get_neurons(), synapse target/weight
    # 3) optional per-target normalization
    return unique_source_count
```

**Demo test:** construct 8×8 → 8×8, run and print per-target incoming sums.

------

## 3) Core algorithm (shared pseudocode)

```text
connect_layers_topographic(region, source_layer_index, destination_layer_index, config):

  # Step 1: build topology (existing rule)
  unique_source_count = region.connect_layers_windowed(
      source_layer_index,
      destination_layer_index,
      config.kernel_h, config.kernel_w,
      config.stride_h, config.stride_w,
      config.padding, config.feedback)

  # Step 2: assign weights for edges (source pixel -> destination center)
  source_height,  source_width  = source_layer.height,  source_layer.width
  dest_height,    dest_width    = destination_layer.height, destination_layer.width   # require 2D destination when center-mapped

  for each source_neuron in source_layer.neurons:
      source_row_index  = source_neuron.index // source_width
      source_col_index  = source_neuron.index %  source_width
      for each outgoing_synapse in source_neuron.outgoing that targets destination_layer:
          center_index         = outgoing_synapse.get_target_index()
          center_row_index     = center_index // dest_width
          center_col_index     = center_index %  dest_width
          delta_row            = (source_row_index - center_row_index)
          delta_col            = (source_col_index - center_col_index)
          squared_distance     = delta_row*delta_row + delta_col*delta_col
          if config.weight_mode == "gaussian":
              weight_value     = exp(-squared_distance / (2 * config.sigma_center * config.sigma_center))
          else: # "dog"
              weight_center    = exp(-squared_distance / (2 * config.sigma_center   * config.sigma_center))
              weight_surround  = exp(-squared_distance / (2 * config.sigma_surround * config.sigma_surround))
              weight_value     = max(0, weight_center - config.surround_ratio * weight_surround)
          outgoing_synapse.set_strength_value(weight_value)

  # Step 3: optional per-target normalization
  if config.normalize_incoming:
      for center_index in 0..(dest_height*dest_width - 1):
          sum_of_incoming = sum of weights of all incoming synapses to center_index
          if sum_of_incoming > 0:
              scale_factor = 1.0 / sum_of_incoming
              for each incoming_synapse to center_index:
                  incoming_synapse.set_strength_value(incoming_synapse.get_strength_value() * scale_factor)

  return unique_source_count
```

**Performance target:** O(E) where E = number of created edges. No additional topology construction beyond step 1. Memory use minimal (reuse existing synapse lists).

------

## 4) Tests (additions)

Create or extend tests under each language to cover:

1. **Topology unchanged**
   - `connect_layers_topographic` returns the **same unique source count** as `connect_layers_windowed` for the same params.
2. **Weight shape – Gaussian**
   - For a destination center neuron, weight to the **same location** (`distance = 0`) is **maximum**.
   - For two concentric distances (e.g., `distance = 1` vs `distance = 2`), `weight(1) > weight(2)`.
3. **Weight shape – DoG**
   - At `distance = 0`, positive center (if `surround_ratio < 1`).
   - There exists a distance where the DoG weight is near zero; since we clamp to non-negative, assert **non-negative** weights.
4. **Normalization (if enabled)**
   - Sum of incoming weights to each destination center is **1.0 ± 1e-6**.
5. **Determinism**
   - Running twice yields identical weight sets.
6. **Edge dedupe still holds**
   - No duplicate `(source_pixel, destination_center)` edges (already covered by existing windowed wiring; include a sanity check).

*(Mojo/Java/C++ tests can reuse the edge-enumeration helpers you already have; if not, add simple accessors in test fixtures only.)*

------

## 5) Demos (one per language)

Deliver a tiny demo per language:

- Build `Input2D(16×16) → Output2D(16×16)`.
- Call `connect_layers_topographic` with Gaussian and with DoG (two runs).
- Print:
  - unique source count,
  - incoming sum for a few centers (e.g., `(row=0,col=0)`, `(row=dest_height/2,col=dest_width/2)`, `(row=dest_height-1,col=dest_width-1)`),
  - for one chosen source pixel, list `[(center_index, weight_value)]` of its outgoing edges (sorted by weight descending).

Ensure the demos **compile and run** without external assets.

------

## 6) Coding style & parity checklist

- **No single/double-character identifiers** anywhere (loops included).
- Python/Mojo: snake_case for functions/vars, **no leading underscores** on public names.
- Mojo: `struct` + `fn` with typed params.
- Deterministic only (no randomness).
- Keep **windowed tracts** and **mesh rules** untouched; we only **set weights** on edges they create.
- Return value semantics preserved.

------

## 7) PR content structure

```
PR_TOPOGRAPHIC_NOTES.md  # short rationale + how to use

src/python/presets/topographic_wiring.py
src/python/demos/topographic_demo.py
src/python/tests/test_topographic_wiring.py     # lightweight assertions

src/java/ai/nektron/grownet/preset/TopographicConfig.java
src/java/ai/nektron/grownet/preset/TopographicWiring.java
src/java/ai/nektron/grownet/demo/TopographicDemo.java
src/test/java/ai/nektron/grownet/TopographicWiringTests.java

src/cpp/include/TopographicWiring.h
src/cpp/src/TopographicWiring.cpp
src/cpp/demo_topographic.cpp
tests/topographic_wiring_test.cpp               # gtest

src/mojo/topographic_wiring.mojo
src/mojo/tests/topographic_demo.mojo
src/mojo/tests/topographic_wiring_test.mojo
```

**Commit guidelines**

- Commit 1: “Topographic preset: API & Python implementation + demo/tests”
- Commit 2: “Java Topographic preset + demo/tests”
- Commit 3: “C++ Topographic preset + demo/tests”
- Commit 4: “Mojo Topographic preset + demo/tests”
- Commit 5: “Docs: PR notes + READMEs (if any)”

------

## 8) Edge cases & safeguards

- If the destination is **not** a 2D layer, still allow the call but compute centers as flat indices with
   `(row_index = index // width, col_index = index % width)` if the layer exposes `height/width`; otherwise **throw/raise** a clear error: “Topographic wiring requires a 2D destination layer”.
- If `kernel` is larger than the source and `padding="valid"`, zero windows — return `0`; do nothing.
- If `normalize_incoming` and a target has **no incoming edges**, skip (keep `0`).
- Use **double precision** for exponential calculations; store in native weight type.
- Numeric epsilon when dividing (e.g., `1e-12`).

------

## 9) Ready-to-paste code stubs (short)

> These stubs show the essential structure with descriptive names. The full implementations follow the same pattern.

### Python – `topographic_wiring.py` (skeleton)

```python
from dataclasses import dataclass
import math

@dataclass
class TopographicConfig:
    kernel_h: int = 7
    kernel_w: int = 7
    stride_h: int = 1
    stride_w: int = 1
    padding: str = "same"
    feedback: bool = False
    weight_mode: str = "gaussian"   # "gaussian" | "dog"
    sigma_center: float = 2.0
    sigma_surround: float = 4.0
    surround_ratio: float = 0.5
    normalize_incoming: bool = True

def connect_layers_topographic(region, source_layer_index: int, destination_layer_index: int, config: TopographicConfig) -> int:
    # 1) topology
    unique_source_count = region.connect_layers_windowed(
        source_layer_index, destination_layer_index,
        config.kernel_h, config.kernel_w,
        config.stride_h, config.stride_w,
        config.padding, config.feedback)

    source_layer = region.layers[source_layer_index]
    destination_layer = region.layers[destination_layer_index]
    source_height, source_width = int(source_layer.height), int(source_layer.width)
    dest_height, dest_width = int(destination_layer.height), int(destination_layer.width)

    # 2) weights
    for source_neuron_index, source_neuron in enumerate(source_layer.get_neurons()):
        source_row_index, source_col_index = divmod(source_neuron_index, source_width)
        for synapse in source_neuron.get_outgoing():   # ADAPT if name differs
            target_index = synapse.get_target_index()  # ADAPT
            center_row_index, center_col_index = divmod(target_index, dest_width)
            delta_row = float(source_row_index - center_row_index)
            delta_col = float(source_col_index - center_col_index)
            squared_distance = delta_row * delta_row + delta_col * delta_col
            if config.weight_mode == "gaussian":
                weight_value = math.exp(-squared_distance / (2.0 * config.sigma_center * config.sigma_center))
            else:
                weight_center   = math.exp(-squared_distance / (2.0 * config.sigma_center   * config.sigma_center))
                weight_surround = math.exp(-squared_distance / (2.0 * config.sigma_surround * config.sigma_surround))
                weight_value = max(0.0, weight_center - config.surround_ratio * weight_surround)
            synapse.set_strength_value(weight_value)   # ADAPT

    # 3) normalization
    if config.normalize_incoming:
        incoming_weight_sums = [0.0] * (dest_height * dest_width)
        # first pass - accumulate
        for source_neuron in source_layer.get_neurons():
            for synapse in source_neuron.get_outgoing():
                incoming_weight_sums[synapse.get_target_index()] += synapse.get_strength_value()
        # second pass - scale
        for source_neuron in source_layer.get_neurons():
            for synapse in source_neuron.get_outgoing():
                sum_for_target = incoming_weight_sums[synapse.get_target_index()]
                if sum_for_target > 1e-12:
                    synapse.set_strength_value(synapse.get_strength_value() / sum_for_target)

    return unique_source_count
```

### Mojo – `topographic_wiring.mojo` (skeleton)

```mojo
struct TopographicConfig:
    var kernel_h: Int = 7
    var kernel_w: Int = 7
    var stride_h: Int = 1
    var stride_w: Int = 1
    var padding: String = "same"
    var feedback: Bool = False
    var weight_mode: String = "gaussian"
    var sigma_center: Float64 = 2.0
    var sigma_surround: Float64 = 4.0
    var surround_ratio: Float64 = 0.5
    var normalize_incoming: Bool = True

fn connect_layers_topographic(
    region: any,
    source_layer_index: Int,
    destination_layer_index: Int,
    config: TopographicConfig
) -> Int:
    let unique_source_count = region.connect_layers_windowed(
        source_layer_index, destination_layer_index,
        config.kernel_h, config.kernel_w,
        config.stride_h, config.stride_w,
        config.padding, config.feedback)

    let source_layer = region.layers[source_layer_index]
    let destination_layer = region.layers[destination_layer_index]
    let source_height = source_layer.height
    let source_width  = source_layer.width
    let dest_height   = destination_layer.height
    let dest_width    = destination_layer.width

    # weights
    var source_neuron_index = 0
    let source_neurons = source_layer.get_neurons()
    while source_neuron_index < source_neurons.len:
        let source_row_index = source_neuron_index / source_width
        let source_col_index = source_neuron_index % source_width
        var outgoing_synapse_index = 0
        let outgoing_synapses = source_neurons[source_neuron_index].outgoing
        while outgoing_synapse_index < outgoing_synapses.len:
            let target_index = outgoing_synapses[outgoing_synapse_index].target_index
            let center_row_index = target_index / dest_width
            let center_col_index = target_index % dest_width
            let delta_row = Float64(source_row_index - center_row_index)
            let delta_col = Float64(source_col_index - center_col_index)
            let squared_distance = delta_row*delta_row + delta_col*delta_col
            var weight_value: Float64 = 0.0
            if config.weight_mode == "gaussian":
                weight_value = exp(-squared_distance / (2.0 * config.sigma_center * config.sigma_center))
            else:
                let weight_center   = exp(-squared_distance / (2.0 * config.sigma_center   * config.sigma_center))
                let weight_surround = exp(-squared_distance / (2.0 * config.sigma_surround * config.sigma_surround))
                let weight_difference = weight_center - config.surround_ratio * weight_surround
                weight_value = if weight_difference > 0.0 then weight_difference else 0.0
            outgoing_synapses[outgoing_synapse_index].set_strength_value(weight_value)   # ADAPT if setter differs
            outgoing_synapse_index = outgoing_synapse_index + 1
        source_neuron_index = source_neuron_index + 1

    if config.normalize_incoming:
        var incoming_weight_sums = [Float64](repeating: 0.0, count: dest_height * dest_width)

        source_neuron_index = 0
        while source_neuron_index < source_neurons.len:
            let synapses_for_sum = source_neurons[source_neuron_index].outgoing
            var synapse_index_for_sum = 0
            while synapse_index_for_sum < synapses_for_sum.len:
                let target_index = synapses_for_sum[synapse_index_for_sum].target_index
                incoming_weight_sums[target_index] = incoming_weight_sums[target_index] + synapses_for_sum[synapse_index_for_sum].get_strength_value()
                synapse_index_for_sum = synapse_index_for_sum + 1
            source_neuron_index = source_neuron_index + 1

        source_neuron_index = 0
        while source_neuron_index < source_neurons.len:
            var synapses_for_scale = source_neurons[source_neuron_index].outgoing
            var synapse_index_for_scale = 0
            while synapse_index_for_scale < synapses_for_scale.len:
                let target_index = synapses_for_scale[synapse_index_for_scale].target_index
                let sum_for_target = incoming_weight_sums[target_index]
                if sum_for_target > 1e-12:
                    synapses_for_scale[synapse_index_for_scale].set_strength_value(
                        synapses_for_scale[synapse_index_for_scale].get_strength_value() / sum_for_target)
                synapse_index_for_scale = synapse_index_for_scale + 1
            source_neuron_index = source_neuron_index + 1

    return unique_source_count
```

*(Java/C++ implementations are analogous; follow the API and use descriptive names.)*

------

## 10) Definition of Done

- Function `connect_layers_topographic` and `TopographicConfig` exist in all four languages.
- Demos compile/run; print expected stats; no runtime “ADAPT” TODOs remain.
- Tests added and green:
  - unique source return parity,
  - Gaussian / DoG weight properties,
  - per-target normalization correctness,
  - determinism across runs.
- Style passes (no short identifiers; snake_case for Python/Mojo; typed Mojo).
- No changes to core growth/tick/tract semantics.
- PR notes file **PR_TOPOGRAPHIC_NOTES.md** added with one-pager usage + examples.