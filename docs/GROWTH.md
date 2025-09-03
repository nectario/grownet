# GROWTH.md — How GrowNet grows

GrowNet follows a simple escalation rule:

1. Grow slots until the per‑neuron `slot_limit` is reached.
2. If novelty still pushes into the fallback bin repeatedly, grow a neuron in that layer.
3. If a layer reaches its neuron limit and novelty pressure persists, grow a new layer (optional, off by default).

## When do we add a neuron?

On each input, the neuron selects/creates a slot. If capacity is saturated, the engine reuses a deterministic fallback bin.
If the neuron hits that fallback bin `fallback_growth_threshold` times in a row (default 3), and growth is enabled, the
layer will add a new neuron.

- Cooldown: `neuron_growth_cooldown_ticks` (default 10) to avoid thrash.
- Toggles: `growth_enabled=True`, `neuron_growth_enabled=True` (defaults).
- Limits: `Layer.neuron_limit` (or `SlotConfig.layer_neuron_limit_default`) can cap the layer’s size.

## Wiring the new neuron

- For random mesh connections created via `Region.connect_layers(...)`, the region stores a rule.
  When a neuron is added, we wire:
  - Outbound: new source → all neurons in each recorded dest layer (Bernoulli with recorded probability).
  - Inbound: all neurons in each recorded src layer → new target (same probability).
- For tract/windowed pipelines created via `Region.connect_layers_windowed(...)`, the region stores the `Tract` object
  and calls `attach_source_neuron(new_idx)` so events flow into downstream exactly like peers if the layer was a source.

This keeps growth deterministic and transparent.

## Layer growth (optional)

If `layer_growth_enabled=True` and the layer hits `neuron_limit`, the region calls `request_layer_growth(...)`. The default
implementation adds a small spillover layer and wires `saturated → new` with a modest probability. You can refine this
in follow‑ups (e.g., duplicate inbound mesh rules to the new layer).

## Knobs (per‑neuron via `slot_cfg`)

- `growth_enabled` (bool, default True)
- `neuron_growth_enabled` (bool, default True)
- `fallback_growth_threshold` (int, default 3)
- `neuron_growth_cooldown_ticks` (int, default 10)
- `layer_growth_enabled` (bool, default False)
- `layer_neuron_limit_default` (int, default -1 = unlimited)
- Layers may override `neuron_limit` at construction.

Parity notes
- C++ and Java mirror Python semantics: strict slot capacity (never allocate at cap), fallback streak triggers neuron growth with cooldown using the bus step counter, and new neurons are auto‑wired using recorded mesh rules. Region pruning remains a no‑op stub in C++/Java until full pruning lands.

## Region Growth (automatic layer creation)

After slot and neuron growth, GrowNet can add a new layer automatically when novelty pressure remains high.

Triggers (either):
- `avg_slots_per_neuron ≥ avg_slots_threshold`, or
- `%{ neurons at capacity AND using fallback } ≥ percent_neurons_at_cap_threshold`.

Safety:
- `layer_cooldown_ticks` ensures layers aren’t added too frequently.
- `max_total_layers` caps total layers in the region.

Action:
- Add a small E‑only spillover layer (`new_layer_excitatory_count`, default 4).
- Wire previous → new with probability `wire_probability` (default 1.0, deterministic).
- Reuse the same deterministic rules as `connect_layers(...)`.

Enable (Python):
```python
from growth import GrowthPolicy
policy = GrowthPolicy(
    enable_layer_growth=True,
    max_total_layers=16,
    avg_slots_threshold=2.0,
    percent_neurons_at_cap_threshold=50.0,
    layer_cooldown_ticks=5,
    new_layer_excitatory_count=4,
    wire_probability=1.0,
)
region.set_growth_policy(policy)
```
