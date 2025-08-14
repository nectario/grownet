from __future__ import annotations
from typing import Dict, List
from weight import Weight
from slot_engine import SlotEngine
from slot_config import SlotConfig
from lateral_bus import LateralBus

class Neuron:
    """
    Base neuron with slot logic and unified on_input/on_output hooks.
    Subclasses override fire() for excitatory/inhibitory/modulatory behaviour.
    """

    def __init__(self, neuron_id: str, slot_config: SlotConfig | None = None, shared_bus: LateralBus | None = None) -> None:
        self.neuron_id = neuron_id
        self.bus: LateralBus = shared_bus if shared_bus is not None else LateralBus()
        self.slots: Dict[int, Weight] = {}
        self.outgoing: List = []  # Synapse objects if you use them
        self.have_last_input: bool = False
        self.last_input_value: float = 0.0
        self.slot_engine = SlotEngine(slot_config or SlotConfig())

    # --- main loop -------------------------------------------------------

    def on_input(self, value: float) -> bool:
        """Route to a slot, learn locally, maybe fire. Returns True if fired."""
        slot = self.slot_engine.select_or_create_slot(self, value)
        slot.reinforce(self.bus.modulation_factor, self.bus.inhibition_factor)
        fired = slot.update_threshold(value)
        if fired:
            self.fire(value)
        self.have_last_input = True
        self.last_input_value = value
        return fired

    def on_output(self, amplitude: float) -> None:
        """Default no-op; OutputNeuron overrides to expose values externally."""
        return

    # --- spike propagation -----------------------------------------------

    def fire(self, input_value: float) -> None:
        """Default excitatory behaviour: propagate along outgoing synapses."""
        for syn in self.outgoing:
            delivered = syn.deliver(input_value)
            if delivered:
                syn.target.on_input(input_value)
