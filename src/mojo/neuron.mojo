# neuron.mojo — base neuron with slots + unified on_input/on_output hooks

from math_utils     import abs_val
from weight         import Weight
from bus            import LateralBus
from slot_config    import SlotConfig
from slot_engine    import SlotEngine

struct Neuron:
    var neuron_id:       String
    var bus:             LateralBus
    var slots:           Dict[Int64, Weight]
    var last_input_value:F64
    var have_last_input: Bool
    var slot_engine:     SlotEngine
    var slot_limit:      Int64   # -1 = unbounded

    fn init(neuron_id: String, bus: LateralBus,
            cfg: SlotConfig = SlotConfig(), slot_limit: Int64 = -1) -> None:
        self.neuron_id        = neuron_id
        self.bus              = bus
        self.slots            = {}
        self.last_input_value = 0.0
        self.have_last_input  = False
        self.slot_engine      = SlotEngine(cfg)
        self.slot_limit       = slot_limit

    # ---- core IO -----------------------------------------------------------

    fn on_input(self, value: F64) -> Bool:
        # Select or create a slot for this input
        var slot_id: Int64 = 0
        if self.have_last_input:
            slot_id = self.slot_engine.slot_id(self.last_input_value, value, Int64(self.slots.len))
        else:
            # T0 imprint path → put first observation in slot 0
            slot_id = 0

        var slot: Weight
        let existing = self.slots.get(slot_id)
        if existing is Weight:
            slot = existing
        else:
            if (self.slot_limit >= 0) and (Int64(self.slots.len) >= self.slot_limit):
                # trivial reuse policy: first slot
                slot = self.slots.values()[0]
            else:
                slot = Weight()
                self.slots[slot_id] = slot

        # local learning + threshold test
        slot.reinforce(self.bus.modulation_factor)
        let fired = slot.update_threshold(value)

        if fired:
            self.fire(value)

        self.have_last_input  = True
        self.last_input_value = value
        return fired

    fn on_output(self, amplitude: F64) -> None:
        # default no-op; OutputNeuron overrides
        pass

    # ---- spiking behaviour (subclasses override as needed) ----------------

    fn fire(self, input_value: F64) -> None:
        # default excitatory semantics are defined in subclasses;
        # base provides a placeholder to keep API coherent.
        pass

    # ---- small logging helpers --------------------------------------------

    fn neuron_value(self, mode: String) -> F64:
        if self.slots.len == 0:
            return 0.0

        if mode == "readiness":
            var best: F64 = -1e300
            for _, w in self.slots.items():
                let margin = w.strength_value - w.threshold_value
                if margin > best:
                    best = margin
            return best

        if mode == "firing_rate":
            var sum: F64 = 0.0
            for _, w in self.slots.items():
                sum = sum + w.ema_rate
            return sum / F64(self.slots.len)

        if mode == "memory":
            var acc: F64 = 0.0
            for _, w in self.slots.items():
                acc = acc + (w.strength_value if w.strength_value >= 0.0 else -w.strength_value)
            return acc

        return self.neuron_value("readiness")
