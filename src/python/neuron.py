
from typing import Dict, List, Callable
from .lateral_bus import LateralBus
from .slot_config import SlotConfig
from .slot_engine import SlotEngine
from .weight import Weight
from .synapse import Synapse

class Neuron:
    def __init__(self, neuron_id: str, bus: LateralBus, cfg: SlotConfig, slot_limit: int = -1) -> None:
        self._id = neuron_id
        self._bus = bus
        self._slot_engine = SlotEngine(cfg)
        self._slot_limit = int(slot_limit)
        self._slots: Dict[int, Weight] = {}
        self._outgoing: List[Synapse] = []
        self._have_last_input: bool = False
        self._last_input_value: float = 0.0
        self._fired_last: bool = False
        self._fire_hooks: List[Callable[["Neuron", float], None]] = []

    # --- connections ---
    def connect(self, target: "Neuron", feedback: bool = False) -> Synapse:
        syn = Synapse(self, target, feedback)
        self._outgoing.append(syn)
        return syn

    # --- IO ---
    def on_input(self, value: float) -> bool:
        slot = self._slot_engine.select_or_create_slot(self, value)
        slot.reinforce(self._bus.get_modulation_factor())
        fired = slot.update_threshold(value)
        self.set_fired_last(fired)
        self.set_last_input_value(value)
        return fired

    def on_output(self, amplitude: float) -> None:
        # fan out to connected neurons
        for hook in self._fire_hooks:
            try:
                hook(self, amplitude)
            except Exception:
                pass
        for syn in self._outgoing:
            syn.transmit(amplitude)

    # --- hooks ---
    def register_fire_hook(self, fn) -> None:
        self._fire_hooks.append(fn)

    # --- tick ---
    def end_tick(self) -> None:
        pass

    # --- accessors ---
    def get_slots(self) -> Dict[int, Weight]:
        return self._slots

    def get_outgoing(self) -> List[Synapse]:
        return self._outgoing

    def get_bus(self) -> LateralBus:
        return self._bus

    def get_id(self) -> str:
        return self._id

    def has_last_input(self) -> bool:
        return self._have_last_input

    def get_last_input_value(self) -> float:
        return self._last_input_value

    def set_last_input_value(self, v: float) -> None:
        self._have_last_input = True
        self._last_input_value = float(v)

    def set_fired_last(self, b: bool) -> None:
        self._fired_last = bool(b)

    def get_fired_last(self) -> bool:
        return self._fired_last
