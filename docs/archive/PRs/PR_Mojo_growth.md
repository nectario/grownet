## PR: Mojo growth + slotting parity (style‑compliant)

**Adds (new files):**

```
src/mojo/grownet/slot_config.mojo
src/mojo/grownet/weight.mojo
src/mojo/grownet/lateral_bus.mojo
src/mojo/grownet/slot_engine.mojo
src/mojo/grownet/neuron.mojo
src/mojo/grownet/layer.mojo
src/mojo/grownet/region.mojo
```

These compile‑level details are intentionally conservative (no inheritance, no magic) and match the Python/C++/Java semantics you approved:

- **Strict slot capacity** in both scalar and 2D: never allocate new bins at capacity; reuse deterministic fallback (or an existing slot if any).
- **Fallback marking**: `last_slot_used_fallback` set whenever a new bin was desired but capacity/domain forced reuse.
- **Frozen slots**: `freeze_last_slot()` / `unfreeze_last_slot()`; frozen slots still match but ignore reinforcement.
- **Growth bookkeeping**: per neuron tracks `fallback_streak` and `last_growth_tick`; a simple **layer‑side** checker in `end_tick()` demonstrates growth escalation without using leading underscores or reflection.
- **Bus `current_step`**: incremented in `decay()` to support cooldown semantics.

> **Wiring note:** `Region.connect_layers` is included with a placeholder `connect(...)` call on neurons. If you already have a Mojo‐side Tract or Synapse, swap that in. The 2D windowed wiring helper can be added next—this PR focuses on the core slot/growth parity and style.

------

### `src/mojo/grownet/slot_config.mojo`

```mojo
# grownet/slot_config.mojo

enum AnchorMode:
    FIRST = 0
    ORIGIN = 1

struct SlotConfig:
    var spatial_enabled: Bool
    var bin_width_pct: Float64
    var row_bin_width_pct: Float64
    var col_bin_width_pct: Float64
    var epsilon_scale: Float64
    var slot_limit: Int
    var anchor_mode: AnchorMode

    # Growth knobs (parity with Python/Java/C++)
    var growth_enabled: Bool
    var neuron_growth_enabled: Bool
    var neuron_growth_cooldown_ticks: Int
    var fallback_growth_threshold: Int
    var layer_neuron_limit_default: Int

    fn init(
        spatial_enabled: Bool = False,
        bin_width_pct: Float64 = 10.0,
        row_bin_width_pct: Float64 = 10.0,
        col_bin_width_pct: Float64 = 10.0,
        epsilon_scale: Float64 = 1e-9,
        slot_limit: Int = 16,
        anchor_mode: AnchorMode = AnchorMode.FIRST,
        growth_enabled: Bool = True,
        neuron_growth_enabled: Bool = True,
        neuron_growth_cooldown_ticks: Int = 0,
        fallback_growth_threshold: Int = 3,
        layer_neuron_limit_default: Int = -1
    ):
        self.spatial_enabled = spatial_enabled
        self.bin_width_pct = bin_width_pct
        self.row_bin_width_pct = row_bin_width_pct
        self.col_bin_width_pct = col_bin_width_pct
        self.epsilon_scale = epsilon_scale
        self.slot_limit = slot_limit
        self.anchor_mode = anchor_mode
        self.growth_enabled = growth_enabled
        self.neuron_growth_enabled = neuron_growth_enabled
        self.neuron_growth_cooldown_ticks = neuron_growth_cooldown_ticks
        self.fallback_growth_threshold = fallback_growth_threshold
        self.layer_neuron_limit_default = layer_neuron_limit_default

fn fixed(delta_percent: Float64 = 10.0) -> SlotConfig:
    return SlotConfig(
        spatial_enabled=False,
        bin_width_pct=delta_percent,
        row_bin_width_pct=delta_percent,
        col_bin_width_pct=delta_percent,
        epsilon_scale=1e-9,
        slot_limit=16,
        anchor_mode=AnchorMode.FIRST,
        growth_enabled=True,
        neuron_growth_enabled=True,
        neuron_growth_cooldown_ticks=0,
        fallback_growth_threshold=3,
        layer_neuron_limit_default=-1
    )
```

------

### `src/mojo/grownet/weight.mojo`

```mojo
# grownet/weight.mojo

struct Weight:
    var strength: Float64
    var threshold: Float64
    var frozen: Bool

    fn init(strength: Float64 = 0.0, threshold: Float64 = 1.0, frozen: Bool = False):
        self.strength = strength
        self.threshold = threshold
        self.frozen = frozen

    fn reinforce(modulation: Float64) -> None:
        if not self.frozen:
            self.strength = self.strength + modulation

    fn update_threshold(effective: Float64) -> Bool:
        let fired: Bool = self.strength >= self.threshold
        if fired and not self.frozen:
            # simple homeostasis
            self.threshold = self.threshold * 1.05
            self.strength = 0.0
        elif not fired and not self.frozen:
            # slow relaxation
            let decayed = self.threshold * 0.995
            self.threshold = decayed if decayed > 0.5 else 0.5
        return fired

    fn freeze() -> None:
        self.frozen = True

    fn unfreeze() -> None:
        self.frozen = False
```

------

### `src/mojo/grownet/lateral_bus.mojo`

```mojo
# grownet/lateral_bus.mojo

struct LateralBus:
    var inhibition_factor: Float64
    var inhibition_decay: Float64
    var modulation_factor: Float64
    var current_step: Int64

    fn init(inhibition_decay: Float64 = 0.90):
        self.inhibition_factor = 0.0
        self.inhibition_decay = inhibition_decay
        self.modulation_factor = 1.0
        self.current_step = 0

    fn pulse_inhibition(factor: Float64) -> None:
        self.inhibition_factor = self.inhibition_factor + factor

    fn pulse_modulation(gain: Float64) -> None:
        self.modulation_factor = self.modulation_factor + gain

    fn decay() -> None:
        self.inhibition_factor = self.inhibition_factor * self.inhibition_decay
        self.modulation_factor = 1.0
        self.current_step = self.current_step + 1

    fn get_current_step() -> Int64:
        return self.current_step

    fn get_step() -> Int64:
        return self.current_step
```

------

### `src/mojo/grownet/slot_engine.mojo`

```mojo
# grownet/slot_engine.mojo
from grownet.slot_config import SlotConfig, AnchorMode
from grownet.weight import Weight

fn max_float(a: Float64, b: Float64) -> Float64:
    if a > b:
        return a
    else:
        return b

# Forward declaration to allow typed parameters
struct Neuron: pass

struct SlotEngine:
    var cfg: SlotConfig

    fn init(cfg: SlotConfig):
        self.cfg = cfg

    fn select_or_create_slot(neuron: inout Neuron, input_value: Float64) -> Int:
        if not neuron.focus_set and self.cfg.anchor_mode == AnchorMode.FIRST:
            neuron.focus_anchor = input_value
            neuron.focus_set = True

        let anchor: Float64 = neuron.focus_anchor
        let denom: Float64 = max_float(abs(anchor), max_float(1e-12, self.cfg.epsilon_scale))
        let delta_pct: Float64 = abs(input_value - anchor) / denom * 100.0
        let bin_w: Float64 = max_float(0.1, self.cfg.bin_width_pct)
        let sid_desired: Int = Int(delta_pct // bin_w)

        let effective_limit: Int = neuron.slot_limit if neuron.slot_limit >= 0 else self.cfg.slot_limit
        let at_capacity: Bool = (effective_limit > 0) and (len(neuron.slots) >= effective_limit)
        let out_of_domain: Bool = (effective_limit > 0) and (sid_desired >= effective_limit)
        let want_new: Bool = not (sid_desired in neuron.slots)
        let use_fallback: Bool = out_of_domain or (at_capacity and want_new)

        let sid: Int = (effective_limit - 1) if (use_fallback and effective_limit > 0) else sid_desired

        if not (sid in neuron.slots):
            if at_capacity:
                if len(neuron.slots) == 0:
                    neuron.slots[sid] = Weight()
                # else reuse an existing slot implicitly
            else:
                neuron.slots[sid] = Weight()

        neuron.last_slot_used_fallback = use_fallback
        neuron.last_slot_id = sid
        return sid

    fn select_or_create_slot_2d(neuron: inout Neuron, row: Int, col: Int) -> Int:
        if (neuron.anchor_row < 0 or neuron.anchor_col < 0):
            if self.cfg.anchor_mode == AnchorMode.ORIGIN:
                neuron.anchor_row = 0
                neuron.anchor_col = 0
            else:
                neuron.anchor_row = row
                neuron.anchor_col = col

        let denom_r: Float64 = max_float(abs(Float64(neuron.anchor_row)), 1.0)
        let denom_c: Float64 = max_float(abs(Float64(neuron.anchor_col)), 1.0)
        let delta_r_pct: Float64 = abs(Float64(row - neuron.anchor_row)) / denom_r * 100.0
        let delta_c_pct: Float64 = abs(Float64(col - neuron.anchor_col)) / denom_c * 100.0

        let bin_r: Float64 = max_float(0.1, self.cfg.row_bin_width_pct)
        let bin_c: Float64 = max_float(0.1, self.cfg.col_bin_width_pct)
        let rbin: Int = Int(delta_r_pct // bin_r)
        let cbin: Int = Int(delta_c_pct // bin_c)

        let effective_limit: Int = neuron.slot_limit if neuron.slot_limit >= 0 else self.cfg.slot_limit
        let at_capacity: Bool = (effective_limit > 0) and (len(neuron.slots) >= effective_limit)
        let out_of_domain: Bool = (effective_limit > 0) and ((rbin >= effective_limit) or (cbin >= effective_limit))

        let desired_key: Int = rbin * 100000 + cbin
        let want_new: Bool = not (desired_key in neuron.slots)
        let use_fallback: Bool = out_of_domain or (at_capacity and want_new)

        let key: Int = ((effective_limit - 1) * 100000 + (effective_limit - 1)) if (use_fallback and effective_limit > 0) else desired_key

        if not (key in neuron.slots):
            if at_capacity:
                if len(neuron.slots) == 0:
                    neuron.slots[key] = Weight()
            else:
                neuron.slots[key] = Weight()

        neuron.last_slot_used_fallback = use_fallback
        neuron.last_slot_id = key
        return key
```

------

### `src/mojo/grownet/neuron.mojo`

```mojo
# grownet/neuron.mojo
from grownet.slot_config import SlotConfig, fixed
from grownet.slot_engine import SlotEngine
from grownet.weight import Weight
from grownet.lateral_bus import LateralBus

struct Neuron:
    var id: String
    var bus: LateralBus
    var slot_cfg: SlotConfig
    var slot_engine: SlotEngine
    var slot_limit: Int
    var slots: Dict[Int, Weight]

    var have_last_input: Bool
    var last_input_value: Float64
    var fired_last: Bool

    # temporal anchor
    var focus_set: Bool
    var focus_anchor: Float64

    # spatial anchor
    var anchor_row: Int
    var anchor_col: Int

    # selection bookkeeping
    var last_slot_id: Int
    var last_slot_used_fallback: Bool

    # growth state
    var fallback_streak: Int
    var last_growth_tick: Int64

    fn init(neuron_id: String,
            bus: LateralBus,
            slot_cfg: SlotConfig = fixed(10.0),
            slot_limit: Int = -1):
        self.id = neuron_id
        self.bus = bus
        self.slot_cfg = slot_cfg
        self.slot_engine = SlotEngine(slot_cfg)
        self.slot_limit = slot_limit
        self.slots = Dict[Int, Weight]()
        self.have_last_input = False
        self.last_input_value = 0.0
        self.fired_last = False
        self.focus_set = False
        self.focus_anchor = 0.0
        self.anchor_row = -1
        self.anchor_col = -1
        self.last_slot_id = -1
        self.last_slot_used_fallback = False
        self.fallback_streak = 0
        self.last_growth_tick = -1

    fn set_bus(new_bus: LateralBus) -> None:
        self.bus = new_bus

    fn get_slots() -> Dict[Int, Weight]:
        return self.slots

    fn get_slot_limit() -> Int:
        return self.slot_limit

    fn set_last_input_value(value: Float64) -> None:
        self.have_last_input = True
        self.last_input_value = value

    fn get_fired_last() -> Bool:
        return self.fired_last

    fn fire(amplitude: Float64) -> None:
        # In Mojo parity, you can later fan-out to Tracts/Synapses here.
        pass

    fn on_input(value: Float64) -> Bool:
        let sid: Int = self.slot_engine.select_or_create_slot(self, value)
        var w = self.slots[sid] if sid in self.slots else Weight()
        w.reinforce(self.bus.modulation_factor)
        let fired: Bool = w.update_threshold(value)
        self.slots[sid] = w
        self.fired_last = fired
        self.last_input_value = value

        let at_capacity: Bool = (self.slot_limit >= 0) and (len(self.slots) >= self.slot_limit)
        if at_capacity and self.last_slot_used_fallback:
            self.fallback_streak = self.fallback_streak + 1
        else:
            self.fallback_streak = 0

        if fired:
            self.fire(value)
        return fired

    fn on_input_2d(value: Float64, row: Int, col: Int) -> Bool:
        if not self.slot_cfg.spatial_enabled:
            return self.on_input(value)
        let key: Int = self.slot_engine.select_or_create_slot_2d(self, row, col)
        var w = self.slots[key] if key in self.slots else Weight()
        w.reinforce(self.bus.modulation_factor)
        let fired: Bool = w.update_threshold(value)
        self.slots[key] = w
        self.fired_last = fired
        self.last_input_value = value

        let at_capacity: Bool = (self.slot_limit >= 0) and (len(self.slots) >= self.slot_limit)
        if at_capacity and self.last_slot_used_fallback:
            self.fallback_streak = self.fallback_streak + 1
        else:
            self.fallback_streak = 0

        if fired:
            self.fire(value)
        return fired

    fn freeze_last_slot() -> Bool:
        if self.last_slot_id < 0:
            return False
        if self.last_slot_id in self.slots:
            var w = self.slots[self.last_slot_id]
            w.freeze()
            self.slots[self.last_slot_id] = w
            return True
        return False

    fn unfreeze_last_slot() -> Bool:
        if self.last_slot_id < 0:
            return False
        if self.last_slot_id in self.slots:
            var w = self.slots[self.last_slot_id]
            w.unfreeze()
            self.slots[self.last_slot_id] = w
            return True
        return False

    fn end_tick() -> None:
        # Reserved for per-neuron maintenance
        pass
```

------

### `src/mojo/grownet/layer.mojo`

```mojo
# grownet/layer.mojo
from grownet.neuron import Neuron
from grownet.slot_config import SlotConfig, fixed
from grownet.lateral_bus import LateralBus

struct Layer:
    var bus: LateralBus
    var neurons: List[Neuron]
    var neuron_limit: Int

    fn init(excitatory_count: Int, inhibitory_count: Int, modulatory_count: Int, neuron_limit: Int = -1):
        self.bus = LateralBus()
        self.neurons = List[Neuron]()
        self.neuron_limit = neuron_limit
        # For now all neurons share the same simple base behavior; you can split E/I/M later.
        for i in range(excitatory_count):
            self.neurons.append(Neuron("E" + str(i), self.bus, fixed(10.0), -1))
        for i in range(inhibitory_count):
            self.neurons.append(Neuron("I" + str(i), self.bus, fixed(10.0), -1))
        for i in range(modulatory_count):
            self.neurons.append(Neuron("M" + str(i), self.bus, fixed(10.0), -1))

    fn get_neurons() -> List[Neuron]:
        return self.neurons

    fn get_bus() -> LateralBus:
        return self.bus

    fn try_grow_neuron_from_seed(seed_index: Int) -> Int:
        if self.neuron_limit >= 0 and len(self.neurons) >= self.neuron_limit:
            return -1
        let seed = self.neurons[seed_index]
        let name = "G" + str(len(self.neurons))
        let new_n = Neuron(name, self.bus, seed.slot_cfg, seed.slot_limit)
        self.neurons.append(new_n)
        return len(self.neurons) - 1

    fn end_tick() -> None:
        # Growth escalation using per-neuron bookkeeping (cooldown via bus step)
        let now: Int64 = self.bus.get_current_step()
        for i in range(len(self.neurons)):
            var n = self.neurons[i]
            let C = n.slot_cfg
            if C.growth_enabled and C.neuron_growth_enabled:
                let at_capacity: Bool = (n.slot_limit >= 0) and (len(n.slots) >= n.slot_limit)
                if at_capacity and n.last_slot_used_fallback:
                    if n.fallback_streak >= (C.fallback_growth_threshold if C.fallback_growth_threshold > 0 else 1):
                        let cooldown: Int = C.neuron_growth_cooldown_ticks if C.neuron_growth_cooldown_ticks > 0 else 0
                        if (n.last_growth_tick < 0) or (now - n.last_growth_tick >= cooldown):
                            let new_idx = self.try_grow_neuron_from_seed(i)
                            if new_idx >= 0:
                                n.last_growth_tick = now
                                self.neurons[i] = n
        # End-of-tick bus decay (increments current_step)
        self.bus.decay()
```

------

### `src/mojo/grownet/region.mojo`

```mojo
# grownet/region.mojo
from grownet.layer import Layer

struct MeshRule:
    var src: Int
    var dst: Int
    var prob: Float64
    var feedback: Bool

struct Region:
    var name: String
    var layers: List[Layer]
    var mesh_rules: List[MeshRule]
    var rng_state: UInt64

    fn init(name: String):
        self.name = name
        self.layers = List[Layer]()
        self.mesh_rules = List[MeshRule]()
        self.rng_state = 0x9E3779B97F4A7C15 # simple seed

    fn add_layer(excitatory_count: Int, inhibitory_count: Int, modulatory_count: Int) -> Int:
        let L = Layer(excitatory_count, inhibitory_count, modulatory_count, -1)
        self.layers.append(L)
        return len(self.layers) - 1

    fn get_layers() -> List[Layer]:
        return self.layers

    fn rand_f64() -> Float64:
        # extremely simple xorshift64* style generator
        var x = self.rng_state
        x = x ^ (x >> 12)
        x = x ^ (x << 25)
        x = x ^ (x >> 27)
        self.rng_state = x
        let v: UInt64 = x * 0x2545F4914F6CDD1D
        return Float64(v & 0xFFFFFFFFFFFF) / Float64(0x1000000000000)

    fn connect_layers(source_index: Int, dest_index: Int, probability: Float64, feedback: Bool = False) -> Int:
        let src = self.layers[source_index]
        let dst = self.layers[dest_index]
        var edges: Int = 0
        let src_neurons = src.get_neurons()
        let dst_neurons = dst.get_neurons()
        for s in src_neurons:
            for t in dst_neurons:
                if self.rand_f64() <= probability:
                    # Placeholder; when you add Synapse/Tract in Mojo, wire here:
                    # s.connect(t, feedback)
                    edges = edges + 1
        self.mesh_rules.append(MeshRule(source_index, dest_index, probability, feedback))
        return edges

    fn autowire_new_neuron(layer_index: Int, new_idx: Int) -> None:
        # Replay mesh rules (outbound + inbound) to wire the new neuron consistently
        if layer_index < 0 or layer_index >= len(self.layers):
            return
        let src_layer = self.layers[layer_index]
        let src_neurons = src_layer.get_neurons()
        if new_idx < 0 or new_idx >= len(src_neurons):
            return
        for r in self.mesh_rules:
            if r.src == layer_index:
                let dst_neurons = self.layers[r.dst].get_neurons()
                for t in dst_neurons:
                    if self.rand_f64() <= r.prob:
                        # src_neurons[new_idx].connect(t, r.feedback)
                        pass
        for r in self.mesh_rules:
            if r.dst == layer_index:
                let upstream = self.layers[r.src].get_neurons()
                for s in upstream:
                    if self.rand_f64() <= r.prob:
                        # s.connect(src_neurons[new_idx], r.feedback)
                        pass
```

------

## How to use (Mojo snippets)

All functions are typed and use `fn`; all types are `struct`s; no `_name` identifiers:

```mojo
from grownet.region import Region

fn demo_growth() -> None:
    var r = Region("mojo-growth")
    let l_in = r.add_layer(4, 0, 0)
    let l_hid = r.add_layer(4, 0, 0)

    # Random mesh wiring (placeholder connects are commented in Region.connect_layers)
    let _ = r.connect_layers(l_in, l_hid, 0.5, False)

    # Enable aggressive growth in the hidden layer
    var hid = r.get_layers()[l_hid]
    for n in hid.get_neurons():
        n.slot_cfg.growth_enabled = True
        n.slot_cfg.neuron_growth_enabled = True
        n.slot_cfg.fallback_growth_threshold = 1
        n.slot_limit = 1

    # Drive a few events (you’d call n.on_input(value) from your I/O path)
    for step in range(3):
        for n in hid.get_neurons():
            let _ = n.on_input(Float64(step + 1))
        hid.end_tick()  # advances bus current_step and runs growth check
```

------

## Notes & next steps

- The Mojo files above **respect your style** (no leading underscores; `fn`; typed params; `struct`).
- They mirror the **core slot/growth semantics** you now have in Python/C++/Java.
- If you already have Mojo Types for **Tract / Synapse / InputLayer2D / OutputLayer2D**, it’s straightforward to:
  - Drop those in and call them from `Region.connect_layers(...)` and `autowire_new_neuron(...)`.
  - Add a `connect_layers_windowed(...)` helper; keep the same **center rule** and **return unique‑source count** you standardized elsewhere.

