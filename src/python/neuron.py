import math
from typing import Dict, List, Optional
from weight import Weight
from synapse import Synapse
from bus import LateralBus

class Neuron:
    """
    Base neuron with slot logic. Subclasses override fire() behaviour.
    Compartments are keyed by percent-delta bins:
      bin 0: 0%
      bin 1: (0,10%], bin 2: (10,20%], ...
    """
    SLOT_LIMIT: Optional[int] = None  # None = unlimited

    def __init__(self, neuron_id: str, bus: LateralBus):
        self.neuron_id = neuron_id
        self.bus = bus
        self.slots: Dict[int, Weight] = {}
        self.outgoing: List[Synapse] = []
        self.last_input_value: Optional[float] = None

    # ----------------- public API -----------------
    def on_input(self, input_value: float):
        slot = self.select_slot(input_value)
        # Local learning in the active slot
        slot.reinforce(
            modulation_factor=self.bus.modulation_factor,
            inhibition_factor=self.bus.inhibition_factor,
        )
        if slot.update_threshold(input_value):
            self.fire(input_value)

        # remember last input for next binning step
        self.last_input_value = input_value

    def connect(self, target: "Neuron", is_feedback: bool = False) -> Synapse:
        syn = Synapse(target, is_feedback)
        self.outgoing.append(syn)
        return syn

    def prune_synapses(self, current_step: int, stale_window: int = 10_000, min_strength: float = 0.05):
        """Drop synapses that have not been used for a long time and stayed weak."""
        self.outgoing = [
            s for s in self.outgoing
            if (current_step - s.last_step) <= stale_window or s.weight.strength_value >= min_strength
        ]

    # ----------------- default firing -----------------
    def fire(self, input_value: float):
        """Excitatory default: propagate along all outgoing synapses."""
        for syn in self.outgoing:
            # Reinforce the synapse’s weight when source fires
            syn.weight.reinforce(
                modulation_factor=self.bus.modulation_factor,
                inhibition_factor=self.bus.inhibition_factor,
            )
            syn.last_step = self.bus.current_step
            if syn.weight.update_threshold(input_value):
                syn.target.on_input(input_value)

    # ----------------- helpers -----------------
    def select_slot(self, input_value: float) -> Weight:
        """Route to a slot based on percent delta from last input."""
        if self.last_input_value is None or self.last_input_value == 0.0:
            bin_id = 0
        else:
            delta = abs(input_value - self.last_input_value) / abs(self.last_input_value)
            delta_percent = delta * 100.0
            bin_id = 0 if delta_percent == 0.0 else int(math.ceil(delta_percent / 10.0))

        comp = self.slots.get(bin_id)
        if comp is None:
            if Neuron.SLOT_LIMIT is not None and len(self.slots) >= Neuron.SLOT_LIMIT:
                # trivial reuse: return the earliest created slot
                comp = next(iter(self.slots.values()))
            else:
                comp = Weight()
                self.slots[bin_id] = comp
        return comp


# ----------------- subclasses -----------------
class ExcitatoryNeuron(Neuron):
    """Inherits default excitatory behaviour."""
    pass


class InhibitoryNeuron(Neuron):
    """Emits an inhibitory pulse (scales down learning/strength this tick)."""
    def fire(self, input_value: float):
        # gamma < 1 attenuates; reset occurs in bus.decay()
        self.bus.inhibition_factor = 0.7


class ModulatoryNeuron(Neuron):
    """Emits a modulatory pulse (scales learning rate this tick)."""
    def fire(self, input_value: float):
        self.bus.modulation_factor = 1.5
