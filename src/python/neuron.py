from typing import Dict, List, Optional, Callable
import math

from weight import Weight
from synapse import Synapse
from bus import LateralBus


class Neuron:
    """
    Base neuron with slot logic and unified on_input/on_output hooks.
    Subclasses may override fire() for excitatory / inhibitory / modulatory behavior.
    """

    # slot_limit < 0 means "unlimited"
    slot_limit: int = -1

    def __init__(self, neuron_id: str, shared_bus: Optional[LateralBus] = None) -> None:
        self.neuron_id: str = neuron_id
        self.bus: LateralBus = shared_bus if shared_bus is not None else LateralBus()
        self.slots: Dict[int, Weight] = {}
        self.outgoing: List[Synapse] = []

        self.has_last_input: bool = False
        self.last_input_value: float = 0.0

        self.fire_hooks: List[Callable[[float, "Neuron"], None]] = []

    # ---------------------------------------------------------------------
    # I/O

    def on_input(self, value: float) -> bool:
        """
        Route to a slot, learn locally, maybe fire.
        Returns True if this neuron fired.
        """
        slot = self.select_slot(value)

        # local learning (modulation/inhibition supplied by the bus)
        slot.reinforce(
            modulation_factor=self.bus.modulation_factor,
            inhibition_factor=self.bus.inhibition_factor,
        )

        fired = slot.update_threshold(value)
        if fired:
            self.fire(value)

        # update book-keeping
        self.has_last_input = True
        self.last_input_value = value
        return fired

    def on_output(self, amplitude: float) -> None:
        """Default no‑op; OutputNeuron overrides this."""
        return

    # ---------------------------------------------------------------------
    # Connectivity

    def connect(self, target: "Neuron", feedback: bool = False) -> Synapse:
        syn = Synapse(target=target, is_feedback=feedback)
        self.outgoing.append(syn)
        return syn

    def prune_synapses(self, current_step: int, stale_window: int, min_strength: float) -> int:
        """
        Drop synapses where (current_step - last_step) > stale_window AND
        syn.weight.strength_value < min_strength.
        Returns number of synapses removed.
        """
        keep: List[Synapse] = []
        removed = 0
        for syn in self.outgoing:
            stale_too_long = (current_step - syn.last_step) > stale_window
            weak = syn.weight.strength_value < min_strength
            if stale_too_long and weak:
                removed += 1
            else:
                keep.append(syn)
        self.outgoing = keep
        return removed

    # ---------------------------------------------------------------------
    # Spiking

    def fire(self, input_value: float) -> None:
        """
        Default excitatory behavior: propagate along outgoing synapses.
        Edge gating: only transmit if the edge's local threshold fires.
        """
        for syn in self.outgoing:
            # local learning also occurs on edges
            syn.weight.reinforce(
                modulation_factor=self.bus.modulation_factor,
                inhibition_factor=self.bus.inhibition_factor,
            )
            syn.last_step = self.bus.current_step

            # gate transmission by the edge's (weight) threshold
            if syn.weight.update_threshold(input_value):
                syn.target.on_input(input_value)

        # fire hooks (e.g., debugging/telemetry)
        for hook in self.fire_hooks:
            hook(input_value, self)

    # ---------------------------------------------------------------------
    # Helpers

    def select_slot(self, value: float) -> Weight:
        """
        Pick/create a slot keyed by percent‑delta of current vs last input.
        Bin width is 10% (can be made policy-driven later).
        Bin id = 0 for identical; otherwise ceil(delta% / 10).
        """
        bin_id = 0
        if self.has_last_input and self.last_input_value != 0.0:
            delta = abs(value - self.last_input_value) / abs(self.last_input_value)
            delta_percent = delta * 100.0
            bin_id = 0 if delta_percent == 0.0 else math.ceil(delta_percent / 10.0)

        slot = self.slots.get(bin_id)
        if slot is None:
            # capacity policy: reuse first slot if at limit (simple baseline)
            if Neuron.slot_limit > 0 and len(self.slots) >= Neuron.slot_limit:
                slot = next(iter(self.slots.values()))
            else:
                slot = Weight()
                self.slots[bin_id] = slot
        return slot

    # ---------------------------------------------------------------------
    # Utilities

    def register_fire_hook(self, hook: Callable[[float, "Neuron"], None]) -> None:
        self.fire_hooks.append(hook)

    def neuron_value(self, mode: str = "readiness") -> float:
        """
        Simple scalar summaries, useful for logging.
        - readiness: max margin (strength - theta) across slots
        - firing_rate: average EMA across slots
        - memory: sum of absolute strengths
        """
        if not self.slots:
            return 0.0

        if mode == "readiness":
            best = -1e300
            for w in self.slots.values():
                margin = w.strength_value - w.threshold_value
                if margin > best:
                    best = margin
            return best

        if mode == "firing_rate":
            total = sum(w.ema_rate for w in self.slots.values())
            return total / float(len(self.slots))

        if mode == "memory":
            return sum(abs(w.strength_value) for w in self.slots.values())

        # default
        return self.neuron_value("readiness")
