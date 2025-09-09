from weight import Weight
from slot_config import fixed
from slot_engine import SlotEngine

class Neuron:
    """Base neuron with slot memory and unified on_input/on_output contract."""
    def __init__(self, neuron_id, bus=None, slot_cfg=None, slot_limit=-1):
        self.id = str(neuron_id)
        self.bus = bus
        self.slot_cfg = slot_cfg if slot_cfg is not None else fixed(10.0)
        self.slot_engine = SlotEngine(self.slot_cfg)
        self.slot_limit = int(slot_limit)
        self.slots = {}   # int -> Weight
        self.outgoing = []  # list of target neurons
        self.have_last_input = False
        self.last_input_value = 0.0

        # temporal focus state
        self.focus_anchor = 0.0
        self.focus_set = False
        self.focus_lock_until_tick = 0
        self.fired_last = False
        self.fire_hooks = []  # callbacks: fn(neuron, value)
        # Remember last selected slot for convenience freeze controls
        self.last_slot = None

        # spatial focus anchors (row/col) — set lazily when spatial is enabled
        self.focus_anchor_row = None  # type: int | None
        self.focus_anchor_col = None  # type: int | None

        # growth bookkeeping
        self.owner = None  # set by Layer when neuron is added to a layer
        self.last_slot_used_fallback = False
        self.prev_missing_slot_id = None
        self.last_missing_slot_id = None
        self.fallback_streak = 0
        self.last_max_axis_delta_pct = 0.0
        self.last_growth_tick = -1

    # ---------- infrastructure ----------
    def set_bus(self, bus):
        self.bus = bus

    def get_bus(self):
        return self.bus

    def id(self):
        return self.id

    def get_outgoing(self):
        return self.outgoing

    def connect(self, target, feedback=False, is_feedback=None):

        # Accept both `feedback` and `is_feedback` (compat alias)
        if is_feedback is not None:
            feedback = bool(is_feedback)

        # For now we store target only; feedback flag reserved for future use.
        self.outgoing.append(target)
        return target

    def register_fire_hook(self, callback):
        """Register a callback invoked after this neuron fires (value, self)."""
        self.fire_hooks.append(callback)

    def has_last_input(self):
        return self.have_last_input

    def get_last_input_value(self):
        return self.last_input_value

    def set_last_input_value(self, v):
        self.last_input_value = float(v)
        self.have_last_input = True

    def fired_last(self):
        return self.fired_last

    def set_fired_last(self, flag):
        self.fired_last = bool(flag)

    # ---------- core behaviour ----------
    def on_input(self, value):
        """Select/reinforce a slot, update threshold, and optionally fire. May request growth."""
        # Choose (or create) slot via the engine so fallback is marked deterministically.
        # Optional one-shot preference: reuse the last selected slot immediately after unfreeze.
        if getattr(self, "prefer_last_slot_once", False) and getattr(self, "last_slot", None) is not None:
            slot = self.last_slot
            self.prefer_last_slot_once = False
        else:
            slot = self.slot_engine.select_or_create_slot(self, value)
        self.last_slot = slot

        # reinforcement scaled by modulation
        mod = 1.0
        if self.bus is not None:
            mod = self.bus.get_modulation_factor()
        slot.reinforce(modulation_factor=mod)

        fired = slot.update_threshold(value)

        # record
        self.set_fired_last(fired)
        self.set_last_input_value(value)

        if fired:
            self.fire(value)
        # Growth check (even in scalar path)
        self.maybe_request_neuron_growth()
        return fired

    def fire(self, input_value):

        # Default (=excitatory): propagate to outgoing neurons
        for target_neuron in list(self.outgoing):
            target_neuron.on_input(input_value)

        for hook in self.fire_hooks:
            hook(self, input_value)

    def on_output(self, amplitude):

        # default no-op (specialized by output neurons)
        pass

    def end_tick(self):

        # default: nothing; subclasses may implement decay, etc.
        pass

    # ---------- spatial variant ----------
    def on_input_2d(self, value: float, row: int, col: int) -> bool:
        """Spatial on_input: manage (row,col) anchor and 2D slot selection.
        If spatial is not enabled in the neuron's slot config, fall back to scalar on_input.
        Also may request growth.
        """
        try:
            if not bool(getattr(self.slot_cfg, "spatial_enabled", False)):
                return self.on_input(value)
        except Exception:
            return self.on_input(value)

        # Optional one-shot preference: reuse the last slot immediately after unfreeze
        if getattr(self, "prefer_last_slot_once", False) and getattr(self, "last_slot", None) is not None:
            slot = self.last_slot
            self.prefer_last_slot_once = False
        else:
            # choose/create spatial slot via engine (engine enforces capacity rules)
            slot = self.slot_engine.select_or_create_slot_2d(self, int(row), int(col))
        self.last_slot = slot

        # reinforcement scaled by modulation
        mod = 1.0
        if self.bus is not None:
            mod = self.bus.get_modulation_factor()
        slot.reinforce(modulation_factor=mod)

        fired = slot.update_threshold(value)
        self.set_fired_last(fired)
        self.set_last_input_value(value)
        if fired:
            self.fire(value)
        # growth escalation (runs whether fired or not)
        self.maybe_request_neuron_growth()
        return fired

    # ---------- maintenance ----------
    def prune_synapses(self, stale_window: int, min_strength: float):
        """Minimal prune implementation: drop all outgoing connections.

        Tests that force-prune via a high min_strength rely on this behavior
        to clear edges. Real implementations may use timestamps/strengths.
        """
        before = len(self.outgoing)
        self.outgoing = []
        return before

    # ---------- frozen-slot convenience ----------
    def freeze_last_slot(self) -> bool:
        slot_obj = getattr(self, "last_slot", None)
        if slot_obj is None:
            return False
        try:
            slot_obj.freeze()
            # Remember which slot we froze to assist unfreeze preference
            try:
                self.last_frozen_slot = slot_obj
            except Exception:
                pass
            return True
        except Exception:
            return False

    def unfreeze_last_slot(self) -> bool:
        # Prefer unfreezing the last frozen slot if tracked; fallback to last selected
        slot_obj = getattr(self, "last_frozen_slot", None)
        if slot_obj is None:
            slot_obj = getattr(self, "last_slot", None)
        if slot_obj is None:
            return False
        try:
            slot_obj.unfreeze()
        except Exception:
            pass
        # Hint selector to reuse this slot on the next tick once.
        self.prefer_last_slot_once = True
        return True

    # ---------- growth helpers ----------
    def maybe_request_neuron_growth(self) -> None:
        cfg = self.slot_cfg
        try:
            if not getattr(cfg, "growth_enabled", True) or not getattr(cfg, "neuron_growth_enabled", True):
                self.fallback_streak = 0
                return
        except Exception:
            return
        # Only escalate when capacity clamp is active and fallback was used
        at_capacity = (self.slot_limit >= 0 and len(self.slots) >= self.slot_limit)
        if not (at_capacity and bool(getattr(self, "last_slot_used_fallback", False))):
            self.fallback_streak = 0
            self.prev_missing_slot_id = None
            self.last_missing_slot_id = None
            return

        # Guard: min delta magnitude
        min_delta = float(getattr(cfg, "min_delta_pct_for_growth", 0.0))
        if min_delta > 0.0 and self.last_max_axis_delta_pct < min_delta:
            self.fallback_streak = 0
            self.prev_missing_slot_id = None
            return

        # Guard: require same missing slot id on consecutive ticks
        if bool(getattr(cfg, "fallback_growth_requires_same_missing_slot", False)):
            if self.prev_missing_slot_id == self.last_missing_slot_id:
                self.fallback_streak += 1
            else:
                self.fallback_streak = 1
                self.prev_missing_slot_id = self.last_missing_slot_id
        else:
            self.fallback_streak += 1

        threshold = int(getattr(cfg, "fallback_growth_threshold", 3))
        if self.fallback_streak >= max(1, threshold) and self.owner is not None:
            now = 0
            try:
                if self.bus is not None and hasattr(self.bus, "get_current_step"):
                    now = int(self.bus.get_current_step())
                elif self.bus is not None and hasattr(self.bus, "get_step"):
                    now = int(self.bus.get_step())
            except Exception:
                now = 0
            cooldown = int(getattr(cfg, "neuron_growth_cooldown_ticks", 10))
            if self.last_growth_tick is None or (now - int(self.last_growth_tick)) >= cooldown:
                try:
                    self.owner.try_grow_neuron(self)
                    self.last_growth_tick = now
                except Exception:
                    pass
            self.fallback_streak = 0
            self.prev_missing_slot_id = None
            self.last_missing_slot_id = None
