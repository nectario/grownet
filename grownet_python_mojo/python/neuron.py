from typing import List, Callable, Optional, TYPE_CHECKING
from region_bus import RegionBus
from synapse import Synapse

class Neuron:
    """
    Base neuron with a thin event‑style API.
    Subclasses override on_input(...) for specific behavior.
    """
    def __init__(self, neuron_id: str, bus: RegionBus, slot_limit: int = 64) -> None:
        self._id = str(neuron_id)
        self._bus = bus
        self._slot_limit = int(slot_limit)
        self._outgoing: List[Synapse] = []
        self._slots: List[float] = []  # placeholder for "slot engine" accounting
        self._fire_hook: Optional[Callable[["Neuron", float], None]] = None
        self._last_input: float = 0.0

    # -------- connections --------
    def connect(self, other: "Neuron", feedback: bool = False) -> None:
        self._outgoing.append(Synapse(self, other, weight=1.0, feedback=feedback))

    # -------- runtime --------
    def on_input(self, value: float) -> bool:
        """
        Default behavior: store input (optionally gated by inhibition) and fire.
        Returns True if fired (for hooks/tests).
        """
        inhib = self._bus.get_inhibition_factor()
        effective = value * (1.0 - max(0.0, min(1.0, inhib)))
        self._last_input = effective
        return self.fire(effective)

    def fire(self, value: float) -> bool:
        if self._fire_hook:
            self._fire_hook(self, value)
        for s in self._outgoing:
            s.transmit(value)
        return True

    def end_tick(self) -> None:
        self._last_input = 0.0

    # -------- hooks / accessors --------
    def register_fire_hook(self, hook: Callable[["Neuron", float], None]) -> None:
        self._fire_hook = hook

    def get_id(self) -> str:
        return self._id

    def get_outgoing(self) -> List[Synapse]:
        return self._outgoing

    def get_slots(self) -> List[float]:
        return self._slots

    def get_bus(self) -> RegionBus:
        return self._bus


class ExcitatoryNeuron(Neuron):
    pass


class InhibitoryNeuron(Neuron):
    def on_input(self, value: float) -> bool:
        # Flip sign to approximate inhibitory behavior
        return super().on_input(-abs(value))


class ModulatoryNeuron(Neuron):
    def on_input(self, value: float) -> bool:
        # Use modulation to scale the outgoing signal
        m = self._bus.get_modulation_factor()
        return super().on_input(value * (1.0 + m))
