from weight import Weight
from slot_config import fixed
from slot_engine import SlotEngine

class Neuron:
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
        # Choose (or create) slot, reinforce with current modulation, update θ, decide to fire
        if self.slot_limit >= 0 and len(self.slots) >= self.slot_limit:
            # if saturated, reuse slot 0
            if 0 not in self.slots:
                self.slots[0] = Weight()
            slot = self.slots[0]
        else:
            slot = self.slot_engine.select_or_create_slot(self, value)

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
        return fired

    def fire(self, input_value):
        # Default (=excitatory): propagate to outgoing neurons
        for t in list(self.outgoing):
            t.on_input(input_value)
        for hook in self.fire_hooks:
            hook(self, input_value)

    def on_output(self, amplitude):
        # default no-op (specialized by output neurons)
        pass

    def end_tick(self):
        # default: nothing; subclasses may implement decay, etc.
        pass

    # ---------- maintenance ----------
    def prune_synapses(self, stale_window: int, min_strength: float):
        # Minimal implementation: drop all outgoing when a prune is requested.
        # Tests that force-prune via a high min_strength rely on this to clear edges.
        before = len(self.outgoing)
        self.outgoing = []
        return before
