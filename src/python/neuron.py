from weight import Weight
from slot_config import fixed
from slot_engine import SlotEngine

class Neuron:
    def __init__(self, neuron_id, bus=None, slot_cfg=None, slot_limit=-1):
        self._id = str(neuron_id)
        self._bus = bus
        self._slot_cfg = slot_cfg if slot_cfg is not None else fixed(10.0)
        self._slot_engine = SlotEngine(self._slot_cfg)
        self._slot_limit = int(slot_limit)
        self._slots = {}   # int -> Weight
        self._outgoing = []  # list of target neurons
        self._have_last_input = False
        self._last_input_value = 0.0
        self._fired_last = False
        self._fire_hooks = []  # callbacks: fn(neuron, value)

    # ---------- infrastructure ----------
    def set_bus(self, bus):
        self._bus = bus

    def get_bus(self):
        return self._bus

    def id(self):
        return self._id

    def slots(self):
        return self._slots

    def get_outgoing(self):
        return self._outgoing

    def connect(self, target, feedback=False):
        # For now we store target only; feedback is a flag for future use.
        self._outgoing.append(target)
        return target

    def register_fire_hook(self, callback):
        self._fire_hooks.append(callback)

    def has_last_input(self):
        return self._have_last_input

    def get_last_input_value(self):
        return self._last_input_value

    def set_last_input_value(self, v):
        self._last_input_value = float(v)
        self._have_last_input = True

    def fired_last(self):
        return self._fired_last

    def set_fired_last(self, flag):
        self._fired_last = bool(flag)

    # ---------- core behaviour ----------
    def on_input(self, value):
        # Choose (or create) slot, reinforce with current modulation, update θ, decide to fire
        if self._slot_limit >= 0 and len(self._slots) >= self._slot_limit:
            # if saturated, reuse slot 0
            if 0 not in self._slots:
                self._slots[0] = Weight()
            slot = self._slots[0]
        else:
            slot = self._slot_engine.select_or_create_slot(self, value)

        # reinforcement scaled by modulation
        mod = 1.0
        if self._bus is not None:
            mod = self._bus.get_modulation_factor()
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
        for t in list(self._outgoing):
            t.on_input(input_value)
        for hook in self._fire_hooks:
            hook(self, input_value)

    def on_output(self, amplitude):
        # default no-op (specialized by output neurons)
        pass

    def end_tick(self):
        # default: nothing; subclasses may implement decay, etc.
        pass
