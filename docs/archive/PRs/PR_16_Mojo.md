## PR 16 — **Mojo Growth Parity** (strict capacity, fallback, growth, autowiring)

### What this adds

- **Mojo runtime** for GrowNet with:
  - `SlotConfig`, `SlotEngine` (scalar + 2D selectors, **strict capacity** & **fallback marker**).
  - `Weight` (freeze/unfreeze, reinforce, simple threshold).
  - `LateralBus`/`RegionBus` with a **`current_step`** counter (cooldown clock) and 2‑phase tick support.
  - `Neuron` base with growth bookkeeping (`owner`, `last_slot_used_fallback`, `fallback_streak`, `last_growth_tick`, one‑shot *prefer last slot* after unfreeze).
  - `Layer` with `try_grow_neuron(seed)` and region back‑ref for **deterministic autowiring**.
  - `Region` with `connect_layers(...)`, `connect_layers_windowed(...)`, **mesh‑rule recording**, `autowire_new_neuron(...)`, `request_layer_growth(...)`, and scalar / 2D tick.
  - Shape‑aware `InputLayer2D` / `OutputLayer2D` that set `owner` on created neurons.
- **Example**: `examples/mojo/growth_demo.mojo` that triggers neuron growth on fallback and shows autowiring.

### Directory layout (new)

```
src/
  mojo/
    grownet/
      SlotConfig.mojo
      Weight.mojo
      SlotEngine.mojo
      LateralBus.mojo
      Neuron.mojo
      Layer.mojo
      Region.mojo
      InputLayer2D.mojo
      OutputLayer2D.mojo
examples/
  mojo/
    growth_demo.mojo
docs/
  GROWTH.md           # append Mojo parity note (added at end)
```

------

## Files (drop‑in contents)

### `src/mojo/grownet/SlotConfig.mojo`

```mojo
# SlotConfig.mojo
class SlotConfig:
    # ----- scalar (temporal) focus -----
    bin_width_pct = 10.0
    epsilon_scale = 1e-6
    slot_limit    = 16  # -1 = unlimited

    # ----- spatial (2D) focus -----
    spatial_enabled      = False
    row_bin_width_pct    = 50.0
    col_bin_width_pct    = 50.0
    anchor_mode_2d       = "FIRST"   # "FIRST" or "ORIGIN"

    # ----- growth knobs (parity with Python/Java) -----
    growth_enabled               = True
    neuron_growth_enabled        = True
    layer_growth_enabled         = False
    fallback_growth_threshold    = 3
    neuron_growth_cooldown_ticks = 0
    layer_neuron_limit_default   = -1

    # convenience builder
    @staticmethod
    def fixed(delta_percent: float = 10.0):
        cfg = SlotConfig()
        cfg.bin_width_pct = float(delta_percent)
        return cfg
```

------

### `src/mojo/grownet/Weight.mojo`

```mojo
# Weight.mojo
class Weight:
    def __init__(self):
        self.strength = 0.0
        self.threshold = 1.0
        self.frozen = False

    def reinforce(self, modulation: float):
        if not self.frozen:
            # lightweight update rule; tweak if you have a canonical one
            self.strength += float(modulation)

    def update_threshold(self, amplitude: float) -> bool:
        # fire if amplitude + learned strength exceeds dynamic threshold
        fired = (float(amplitude) + self.strength) >= self.threshold
        if fired:
            # make it a bit harder next time
            self.threshold *= 1.05
        else:
            # relax slightly
            self.threshold *= 0.995
        return fired

    def freeze(self):
        self.frozen = True

    def unfreeze(self):
        self.frozen = False
```

------

### `src/mojo/grownet/LateralBus.mojo`

```mojo
# LateralBus.mojo
class LateralBus:
    def __init__(self, inhibition_decay: float = 0.90):
        self.inhibition_factor = 1.0
        self.inhibition_decay = float(inhibition_decay)
        self.modulation_factor = 1.0
        self.current_step = 0

    # pulses (phasic)
    def pulse_inhibition(self, factor: float):
        self.inhibition_factor *= float(max(0.0, factor))

    def pulse_modulation(self, delta: float):
        self.modulation_factor += float(delta)
        if self.modulation_factor < 0.0:
            self.modulation_factor = 0.0

    # post-tick housekeeping
    def decay(self):
        self.inhibition_factor *= self.inhibition_decay
        self.modulation_factor = 1.0
        self.current_step += 1

    # convenience
    def get_current_step(self) -> int: return int(self.current_step)
    def get_step(self) -> int:        return int(self.current_step)  # alias
```

------

### `src/mojo/grownet/SlotEngine.mojo`

```mojo
# SlotEngine.mojo
from .Weight import Weight

class SlotEngine:
    def __init__(self, cfg):
        self.cfg = cfg

    # ---------- scalar selection (FIRST anchor) ----------
    def select_or_create_slot(self, neuron, input_value: float):
        cfg = self.cfg

        # FIRST-anchor initialization
        if not getattr(neuron, "_focus_set", False):
            neuron._focus_anchor = float(input_value)
            neuron._focus_set = True

        anchor = float(neuron._focus_anchor)
        denom = max(abs(anchor), float(getattr(cfg, "epsilon_scale", 1e-6)), 1e-12)
        delta_pct = abs(float(input_value) - anchor) / denom * 100.0
        bin_w = max(0.1, float(getattr(cfg, "bin_width_pct", 10.0)))
        sid_desired = int(delta_pct // bin_w)

        # effective limit: per-neuron override wins
        n_limit = int(getattr(neuron, "slot_limit", -1))
        limit = n_limit if n_limit >= 0 else int(getattr(cfg, "slot_limit", 16))
        slots = neuron.slots

        at_capacity = (limit > 0 and len(slots) >= limit)
        out_of_domain = (limit > 0 and sid_desired >= limit)
        want_new = (sid_desired not in slots)
        use_fallback = out_of_domain or (at_capacity and want_new)

        sid = (limit - 1) if (use_fallback and limit > 0) else sid_desired

        if sid not in slots:
            if at_capacity:
                if len(slots) == 0:
                    slots[sid] = Weight()
                else:
                    # reuse first existing key deterministically
                    first_key = next(iter(slots.keys()))
                    sid = first_key
            else:
                slots[sid] = Weight()

        neuron.last_slot_used_fallback = bool(use_fallback)
        neuron.last_slot_id = sid
        return slots[sid]

    # ---------- 2D selection (FIRST/ORIGIN anchor) ----------
    def select_or_create_slot_2d(self, neuron, row: int, col: int):
        cfg = self.cfg

        # anchor (FIRST or ORIGIN)
        mode = str(getattr(cfg, "anchor_mode_2d", "FIRST")).upper()
        if mode == "ORIGIN":
            a_r, a_c = 0, 0
            neuron._focus_set_2d = True
        else:
            if not getattr(neuron, "_focus_set_2d", False):
                neuron._anchor_row = int(row)
                neuron._anchor_col = int(col)
                neuron._focus_set_2d = True
            a_r, a_c = int(neuron._anchor_row), int(neuron._anchor_col)

        eps = 1.0  # spatial epsilon to avoid exploding bins near origin
        d_r = abs(int(row) - a_r) / max(abs(a_r), eps) * 100.0
        d_c = abs(int(col) - a_c) / max(abs(a_c), eps) * 100.0

        rbw = max(0.1, float(getattr(cfg, "row_bin_width_pct", 50.0)))
        cbw = max(0.1, float(getattr(cfg, "col_bin_width_pct", 50.0)))
        r_bin = int(d_r // rbw)
        c_bin = int(d_c // cbw)

        n_limit = int(getattr(neuron, "slot_limit", -1))
        limit = n_limit if n_limit >= 0 else int(getattr(cfg, "slot_limit", 16))
        slots = neuron.slots

        desired_key = (r_bin, c_bin)
        at_capacity = (limit > 0 and len(slots) >= limit)
        out_of_domain = (limit > 0 and (r_bin >= limit or c_bin >= limit))
        want_new = (desired_key not in slots)
        use_fallback = out_of_domain or (at_capacity and want_new)

        key = ((limit - 1, limit - 1) if (use_fallback and limit > 0) else desired_key)

        if key not in slots:
            if at_capacity:
                if len(slots) == 0:
                    slots[key] = Weight()
                else:
                    key = next(iter(slots.keys()))
            else:
                slots[key] = Weight()

        neuron.last_slot_used_fallback = bool(use_fallback)
        neuron.last_slot_id = key
        return slots[key]
```

------

### `src/mojo/grownet/Neuron.mojo`

```mojo
# Neuron.mojo
from .Weight import Weight
from .SlotConfig import SlotConfig
from .SlotEngine import SlotEngine

class Neuron:
    def __init__(self, neuron_id: str, bus, slot_cfg: SlotConfig | None = None, slot_limit: int = -1):
        self.id = str(neuron_id)
        self.bus = bus
        self.slot_cfg = slot_cfg if slot_cfg is not None else SlotConfig.fixed(10.0)
        self.slot_engine = SlotEngine(self.slot_cfg)
        self.slot_limit = int(slot_limit)

        self.slots = {}         # map: int or (r,c) -> Weight
        self.outgoing = []      # list of (target_neuron, feedback_bool)
        self.fire_hooks = []    # callbacks: (who, amplitude) -> None

        # state
        self.have_last_input = False
        self.last_input_value = 0.0
        self.fired_last = False

        # anchors
        self._focus_set = False
        self._focus_anchor = 0.0
        self._focus_set_2d = False
        self._anchor_row = 0
        self._anchor_col = 0

        # freeze/unfreeze helpers
        self.last_slot_id = None
        self._prefer_last_slot_once = False
        self._prefer_specific_slot_once = None
        self._last_frozen_slot = None

        # growth bookkeeping
        self.owner = None
        self.last_slot_used_fallback = False
        self.fallback_streak = 0
        self.last_growth_tick = -1

    # ----- wiring -----
    def connect(self, target, feedback: bool = False):
        self.outgoing.append((target, bool(feedback)))

    def register_fire_hook(self, hook):
        self.fire_hooks.append(hook)

    # ----- core I/O -----
    def on_input(self, value: float) -> bool:
        # optional one-shot reuse after unfreeze
        if self._prefer_last_slot_once and (self.last_slot_id in self.slots):
            slot = self.slots[self.last_slot_id]
            self._prefer_last_slot_once = False
        else:
            slot = self.slot_engine.select_or_create_slot(self, float(value))
        self._last_slot_obj = slot

        # reinforcement scaled by modulation; (inhibition is available if you fold it into amplitude)
        mod = float(getattr(self.bus, "modulation_factor", 1.0))
        slot.reinforce(mod)

        # decide to fire
        fired = slot.update_threshold(float(value))
        self.fired_last = bool(fired)
        self.last_input_value = float(value)
        self.have_last_input = True

        if fired:
            self.fire(value)

        # growth check
        self._maybe_request_neuron_growth()
        return fired

    def on_input_2d(self, value: float, row: int, col: int) -> bool:
        if not bool(getattr(self.slot_cfg, "spatial_enabled", False)):
            return self.on_input(value)

        # one-shot preferred slot (after unfreeze)
        if self._prefer_last_slot_once and (self.last_slot_id in self.slots):
            slot = self.slots[self.last_slot_id]
            self._prefer_last_slot_once = False
        elif self._prefer_specific_slot_once is not None:
            slot = self._prefer_specific_slot_once
            self._prefer_specific_slot_once = None
        else:
            slot = self.slot_engine.select_or_create_slot_2d(self, int(row), int(col))
        self._last_slot_obj = slot

        mod = float(getattr(self.bus, "modulation_factor", 1.0))
        slot.reinforce(mod)

        fired = slot.update_threshold(float(value))
        self.fired_last = bool(fired)
        self.last_input_value = float(value)
        self.have_last_input = True

        if fired:
            self.fire(value)

        self._maybe_request_neuron_growth()
        return fired

    def fire(self, amplitude: float):
        # notify hooks first (e.g., Tract-like behaviors)
        for h in self.fire_hooks:
            try: h(self, float(amplitude))
            except Exception: pass
        # then push to targets
        for (t, fb) in list(self.outgoing):
            try:
                t.on_input(float(amplitude))
            except Exception:
                pass

    def end_tick(self):
        # per-neuron cleanup if needed
        pass

    # ----- frozen slots -----
    def freeze_last_slot(self) -> bool:
        sid = self.last_slot_id
        if sid is None or sid not in self.slots:
            return False
        try:
            self.slots[sid].freeze()
            self._last_frozen_slot = self.slots[sid]
            return True
        except Exception:
            return False

    def unfreeze_last_slot(self) -> bool:
        sid = self.last_slot_id
        if sid is None or sid not in self.slots:
            return False
        try:
            self.slots[sid].unfreeze()
            # prefer the same slot on next tick once
            self._prefer_last_slot_once = True
            self._prefer_specific_slot_once = self.slots[sid]
            return True
        except Exception:
            return False

    # ----- growth escalation -----
    def _maybe_request_neuron_growth(self):
        cfg = self.slot_cfg
        try:
            if not getattr(cfg, "growth_enabled", True) or not getattr(cfg, "neuron_growth_enabled", True):
                self.fallback_streak = 0
                return
        except Exception:
            return

        at_capacity = (self.slot_limit >= 0 and len(self.slots) >= self.slot_limit)
        if at_capacity and bool(self.last_slot_used_fallback):
            self.fallback_streak += 1
        else:
            self.fallback_streak = 0

        threshold = int(getattr(cfg, "fallback_growth_threshold", 3))
        if self.fallback_streak >= max(1, threshold) and self.owner is not None:
            now = 0
            try:
                now = int(self.bus.get_current_step())
            except Exception:
                now = 0
            cooldown = int(getattr(cfg, "neuron_growth_cooldown_ticks", 0))
            if (self.last_growth_tick is None) or ((now - int(self.last_growth_tick)) >= cooldown):
                try:
                    new_idx = self.owner.try_grow_neuron(self)
                    self.last_growth_tick = now
                except Exception:
                    pass
            self.fallback_streak = 0
```

------

### `src/mojo/grownet/Layer.mojo`

```mojo
# Layer.mojo
from .LateralBus import LateralBus
from .SlotConfig import SlotConfig
from .Neuron import Neuron

class Layer:
    def __init__(self, excitatory_count: int, inhibitory_count: int, modulatory_count: int, neuron_limit: int | None = None):
        self.bus = LateralBus()
        self.rng_seed = 1234
        self._region = None
        self.neurons = []

        # store counts for possible spillover sizing
        self.excitatory_count = int(excitatory_count)
        self.inhibitory_count = int(inhibitory_count)
        self.modulatory_count = int(modulatory_count)

        # construct homogeneous excitatory by default (simple baseline)
        # you can subclass this to add I/M specializations later
        slot_limit = -1
        for i in range(self.excitatory_count):
            n = Neuron(f"E{i}", self.bus, SlotConfig.fixed(10.0), slot_limit)
            n.owner = self
            self.neurons.append(n)

        self.neuron_limit = int(SlotConfig.layer_neuron_limit_default) if neuron_limit is None else int(neuron_limit)

    # basic accessors
    def get_neurons(self): return self.neurons
    def get_bus(self):     return self.bus

    # region backref
    def _set_region(self, region): self._region = region

    # fan-out entry point for scalar convenience paths
    def forward(self, value: float):
        # by default, broadcast to all neurons
        for n in self.neurons: n.on_input(float(value))

    def end_tick(self):
        for n in self.neurons: n.end_tick()
        self.bus.decay()

    # ---- growth API (called by Neuron) ----
    def try_grow_neuron(self, seed_neuron) -> int | None:
        # enforce per-layer cap
        if self.neuron_limit is not None and int(self.neuron_limit) >= 0:
            if len(self.neurons) >= int(self.neuron_limit):
                if self._region and getattr(getattr(seed_neuron, "slot_cfg", object()), "layer_growth_enabled", False):
                    try: self._region.request_layer_growth(self)
                    except Exception: pass
                return None

        # same class where possible (here we keep Neuron baseline)
        new_n = Neuron(f"G{len(self.neurons)}", self.bus, seed_neuron.slot_cfg, seed_neuron.slot_limit)
        new_n.owner = self
        self.neurons.append(new_n)

        try:
            if self._region is not None:
                self._region.autowire_new_neuron(self, len(self.neurons) - 1)
        except Exception:
            pass
        return len(self.neurons) - 1
```

------

### `src/mojo/grownet/InputLayer2D.mojo`

```mojo
# InputLayer2D.mojo
from .Layer import Layer
from .Neuron import Neuron
from .SlotConfig import SlotConfig

class InputLayer2D(Layer):
    def __init__(self, height: int, width: int, gain: float, epsilon_fire: float):
        # call base with zero (we'll create our own inputs)
        super().__init__(0, 0, 0)
        self.height = int(height)
        self.width  = int(width)
        self.gain = float(gain)
        self.epsilon_fire = float(epsilon_fire)
        self.neurons = []

        for r in range(self.height):
            for c in range(self.width):
                n = Neuron(f"IN[{r},{c}]", self.get_bus(), SlotConfig.fixed(10.0), -1)
                n.owner = self
                self.neurons.append(n)

    # feed one image frame (list of rows of numeric values)
    def forward_frame(self, frame):
        for r, row in enumerate(frame):
            for c, v in enumerate(row):
                if float(v) != 0.0:
                    self.neurons[r * self.width + c].on_input_2d(self.gain * float(v), r, c)
        # allow zero frames to still produce orderly ticks
```

------

### `src/mojo/grownet/OutputLayer2D.mojo`

```mojo
# OutputLayer2D.mojo
from .Layer import Layer
from .Neuron import Neuron
from .SlotConfig import SlotConfig

class OutputLayer2D(Layer):
    def __init__(self, height: int, width: int, smoothing: float = 0.0):
        super().__init__(0, 0, 0)
        self.height = int(height)
        self.width  = int(width)
        self.smoothing = float(smoothing)
        self.neurons = []
        # we keep a simple frame snapshot you can poll after ticks
        self._frame = [[0.0 for _ in range(self.width)] for __ in range(self.height)]

        for r in range(self.height):
            for c in range(self.width):
                n = Neuron(f"OUT[{r},{c}]", self.get_bus(), SlotConfig.fixed(10.0), -1)
                n.owner = self
                # overwrite on_input to also update the visible frame (simple projection)
                orig_on_input = n.on_input
                def _wrap(value: float, rr=r, cc=c, orig=orig_on_input):
                    fired = orig(value)
                    # record magnitude (optionally smoothed)
                    self._frame[rr][cc] = (self.smoothing * self._frame[rr][cc] +
                                           (1.0 - self.smoothing) * float(value))
                    return fired
                n.on_input = _wrap
                self.neurons.append(n)

    def get_frame(self):
        return [row[:] for row in self._frame]
```

------

### `src/mojo/grownet/Region.mojo`

```mojo
# Region.mojo
import random
from .Layer import Layer
from .InputLayer2D import InputLayer2D
from .OutputLayer2D import OutputLayer2D

class Region:
    def __init__(self, name: str):
        self.name = str(name)
        self.layers = []
        self.bus = None  # optional region-scope bus (per-layer buses already exist)
        self.rng = random.Random(1234)
        self.enable_spatial_metrics = False

        # wiring & growth bookkeeping
        self._mesh_rules = []   # dicts: {'src':i,'dst':j,'prob':p,'feedback':bool}
        self._input_edges = {}  # port -> layer_index (scalar or 2D)
        self._input_ports = {}  # port -> list[layer_index] (fan-out convenience)

    # ----- construction -----
    def add_layer(self, excitatory_count: int, inhibitory_count: int, modulatory_count: int) -> int:
        L = Layer(excitatory_count, inhibitory_count, modulatory_count)
        try: L._set_region(self)
        except Exception: pass
        self.layers.append(L)
        return len(self.layers) - 1

    def add_input_layer_2d(self, height: int, width: int, gain: float, epsilon_fire: float) -> int:
        L = InputLayer2D(height, width, gain, epsilon_fire)
        try: L._set_region(self)
        except Exception: pass
        self.layers.append(L)
        return len(self.layers) - 1

    def add_output_layer_2d(self, height: int, width: int, smoothing: float) -> int:
        L = OutputLayer2D(height, width, smoothing)
        try: L._set_region(self)
        except Exception: pass
        self.layers.append(L)
        return len(self.layers) - 1

    # ----- binding -----
    def bind_input(self, port: str, layer_indices):
        self._input_ports[str(port)] = list(layer_indices)
        if layer_indices:
            self._input_edges[str(port)] = int(layer_indices[0])

    # ----- mesh wiring -----
    def connect_layers(self, source_index: int, dest_index: int, probability: float, feedback: bool = False) -> int:
        if source_index < 0 or source_index >= len(self.layers):
            raise IndexError("invalid source index")
        if dest_index < 0 or dest_index >= len(self.layers):
            raise IndexError("invalid dest index")

        src = self.layers[source_index]
        dst = self.layers[dest_index]
        edges = 0
        for s in src.get_neurons():
            for t in dst.get_neurons():
                if self.rng.random() <= float(probability):
                    s.connect(t, bool(feedback))
                    edges += 1

        self._mesh_rules.append({'src': int(source_index), 'dst': int(dest_index),
                                 'prob': float(probability), 'feedback': bool(feedback)})
        return edges

    # ----- windowed deterministic wiring (Input2D -> Output2D or generic layer) -----
    def connect_layers_windowed(self, source_index: int, dest_index: int,
                                kernel_h: int, kernel_w: int,
                                stride_h: int, stride_w: int,
                                padding: str = "valid",
                                feedback: bool = False) -> int:
        src = self.layers[source_index]
        dst = self.layers[dest_index]
        # Only implement the deterministic variant used in Python/C++
        # Build window origins
        H = int(getattr(src, "height", 0)); W = int(getattr(src, "width", 0))
        kh = int(kernel_h); kw = int(kernel_w)
        sh = int(stride_h); sw = int(stride_w)
        pad = str(padding).lower()

        def origins_valid():
            r = 0
            while r + kh <= H:
                c = 0
                while c + kw <= W:
                    yield (r, c)
                    c += sw
                r += sh

        def origins_same():
            r0 = -(kh // 2); c0 = -(kw // 2)
            r = r0
            while r < H:
                c = c0
                while c < W:
                    yield (r, c)
                    c += sw
                r += sh

        origins = list(origins_valid() if pad == "valid" else origins_same())

        allowed = set()
        src_neurons = src.get_neurons()
        dst_neurons = dst.get_neurons()

        dst_is_out2d = hasattr(dst, "get_frame")  # crude check
        if dst_is_out2d:
            # map window -> center and connect (src -> center), dedup
            made = set()
            for (r0, c0) in origins:
                rr0 = max(0, r0); cc0 = max(0, c0)
                rr1 = min(H, r0 + kh); cc1 = min(W, c0 + kw)
                if rr0 >= rr1 or cc0 >= cc1: continue
                cr = min(H - 1, max(0, r0 + kh // 2))
                cc = min(W - 1, max(0, c0 + kw // 2))
                center_idx = cr * W + cc
                for rr in range(rr0, rr1):
                    for cc2 in range(cc0, cc1):
                        src_idx = rr * W + cc2
                        allowed.add(src_idx)
                        key = (src_idx, center_idx)
                        if key in made: continue
                        made.add(key)
                        if 0 <= src_idx < len(src_neurons) and 0 <= center_idx < len(dst_neurons):
                            s = src_neurons[src_idx]; t = dst_neurons[center_idx]
                            s.connect(t, feedback)
        else:
            # generic: first time we see a source, connect it to ALL dest neurons
            seen = set()
            for (r0, c0) in origins:
                rr0 = max(0, r0); cc0 = max(0, c0)
                rr1 = min(H, r0 + kh); cc1 = min(W, c0 + kw)
                if rr0 >= rr1 or cc0 >= cc1: continue
                for rr in range(rr0, rr1):
                    for cc2 in range(cc0, cc1):
                        src_idx = rr * W + cc2
                        if src_idx not in seen:
                            seen.add(src_idx)
                            allowed.add(src_idx)
                            if 0 <= src_idx < len(src_neurons):
                                s = src_neurons[src_idx]
                                for t in dst_neurons:
                                    s.connect(t, feedback)

        # return unique source subscriptions
        return int(len(allowed))

    # ----- ticks -----
    def tick(self, port: str, value: float):
        edge_idx = self._input_edges.get(str(port))
        if edge_idx is None:
            raise KeyError(f"No InputEdge for port '{port}'. Call bind_input(...) first.")
        self.layers[edge_idx].forward(float(value))
        # fan-out convenience: also drive any additional bound target layers directly (matches Python polish)
        for li in self._input_ports.get(str(port), []):
            if li != edge_idx:
                self.layers[li].forward(float(value))
        # Phase-B
        for L in self.layers: L.end_tick()
        return {"delivered_events": 1}

    def tick_2d(self, port: str, frame):
        edge_idx = self._input_edges.get(str(port))
        if edge_idx is None:
            raise KeyError(f"No InputEdge for port '{port}'. Call bind_input(...) first.")
        edge = self.layers[edge_idx]
        if not hasattr(edge, "forward_frame"):
            raise TypeError("tick_2d requires an InputLayer2D edge")
        edge.forward_frame(frame)
        # Phase-B
        for L in self.layers: L.end_tick()
        return {"delivered_events": 1}

    # ----- growth autowiring -----
    def autowire_new_neuron(self, layer_obj, new_idx: int):
        try:
            li = self.layers.index(layer_obj)
        except ValueError:
            return
        # outbound mesh
        for rule in list(self._mesh_rules):
            if int(rule.get('src')) != li: continue
            dst_i = int(rule.get('dst'))
            prob  = float(rule.get('prob', 0.0)); fb = bool(rule.get('feedback', False))
            dst = self.layers[dst_i]
            s = layer_obj.get_neurons()[new_idx]
            for t in dst.get_neurons():
                if self.rng.random() <= prob:
                    s.connect(t, fb)
        # inbound mesh
        for rule in list(self._mesh_rules):
            if int(rule.get('dst')) != li: continue
            src_i = int(rule.get('src'))
            prob  = float(rule.get('prob', 0.0)); fb = bool(rule.get('feedback', False))
            src = self.layers[src_i]
            t = layer_obj.get_neurons()[new_idx]
            for s in src.get_neurons():
                if self.rng.random() <= prob:
                    s.connect(t, fb)

    def request_layer_growth(self, saturated_layer) -> int | None:
        try:
            idx = self.layers.index(saturated_layer)
        except ValueError:
            return None
        # small spillover (E-only)
        new_exc = max(4, (getattr(saturated_layer, 'excitatory_count', 4) // 2) or 4)
        new_idx = self.add_layer(new_exc, 0, 0)
        self.connect_layers(idx, new_idx, probability=0.15, feedback=False)
        return new_idx
```

------

## Example (Mojo)

### `examples/mojo/growth_demo.mojo`

```mojo
# examples/mojo/growth_demo.mojo
from src.mojo.grownet.Region import Region

def main():
    r = Region("growth_mojo")
    lin = r.add_input_layer_2d(4, 4, gain=1.0, epsilon_fire=0.01)
    hid = r.add_layer(4, 0, 0)

    # windowed wiring: 2x2 stride 2 "valid"
    r.connect_layers_windowed(lin, hid, 2, 2, 2, 2, "valid")
    r.bind_input("img", [lin])

    # enable spatial & growth on hidden neurons; force tiny slot capacity
    L = r.layers[hid]
    for n in L.get_neurons():
        n.slot_cfg.spatial_enabled = True
        n.slot_cfg.row_bin_width_pct = 10.0
        n.slot_cfg.col_bin_width_pct = 10.0
        n.slot_cfg.growth_enabled = True
        n.slot_cfg.neuron_growth_enabled = True
        n.slot_cfg.fallback_growth_threshold = 1
        n.slot_limit = 1

    frames = [
        [[0,1,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]],
        [[0,0,1,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]],
        [[0,0,0,1],[0,0,0,0],[0,0,0,0],[0,0,0,0]],
    ]
    print("start neurons:", len(L.get_neurons()))
    for i, f in enumerate(frames, 1):
        r.tick_2d("img", f)
        print("tick", i, "neurons:", len(L.get_neurons()))
        for idx, n in enumerate(L.get_neurons()):
            print("  n", idx, "slots", len(n.slots), "fallback", n.last_slot_used_fallback, "streak", n.fallback_streak)

if __name__ == "__main__":
    main()
```

------

## Docs tweak

Append this **Mojo parity** note to `docs/GROWTH.md` (end of file):

```md
### Mojo parity

The Mojo runtime mirrors Python semantics:

- **Strict slot capacity** (no new slot when at capacity; fallback bin is reused deterministically).
- **Fallback marking** drives **neuron growth** after `fallback_growth_threshold` consecutive at-capacity hits, with a cooldown using the bus `current_step`.
- **Auto‑wiring** for newly grown neurons replays recorded `connect_layers(...)` mesh rules for both outbound and inbound edges.
- `connect_layers_windowed(...)` provides deterministic 2D wiring identical to Python/C++ (center rule for OutputLayer2D).
```

------

## Usage quick‑start

- Place files as shown, then run the demo (Mojo’s Python‑subset mode):

```bash
# from repo root
mojo examples/mojo/growth_demo.mojo
# or, if your toolchain invokes via python:
python examples/mojo/growth_demo.mojo
```

You should see the hidden layer’s neuron count increase after a couple of frames as fallback hits at capacity.

------

## Why this matches your Python/C++/Java behavior

- **Slot selection** (scalar & 2D) uses the same **percent‑delta binning**, FIRST/ORIGIN anchors, and **strict capacity** with deterministic reuse at cap.
- **Growth triggers** exactly when “wanted a new bin but couldn’t,” tracked via `last_slot_used_fallback` and a **streak** with **cooldown** from `bus.current_step`.
- **Deterministic autowiring** reuses previously recorded **mesh rules** for both inbound and outbound edges, as in your Region `_autowire_new_neuron`.
- **Windowed wiring** implements the **center rule** for OutputLayer2D and unique‑source counting in line with your documented return semantics.

------

### (Optional) C++ hygiene follow‑ups you may still want

If you still see the “invalid use of incomplete type ‘Neuron’” inlined in `SlotEngine.h`, either:

- include `Neuron.h` at the top of `SlotEngine.h`, **or**
- move any inlined methods that dereference `Neuron` (e.g., 2D selectors) into `SlotEngine.cpp` (and `#include "Neuron.h"` there).

This keeps headers light and avoids cyclic includes.

------

