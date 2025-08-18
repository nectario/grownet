from typing import Optional, Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from neuron import Neuron

class Synapse:
    def __init__(self, pre: "Neuron", post: "Neuron", weight: float = 1.0, feedback: bool = False) -> None:
        self._pre = pre
        self._post = post
        self._weight = float(weight)
        self._feedback = bool(feedback)
        self._last_strength = 0.0
        self._last_tick = 0

    def transmit(self, value: float) -> None:
        self._last_strength = value * self._weight
        self._post.on_input(self._last_strength)

    # --- accessors ---
    def get_weight(self) -> float:
        return self._weight

    def is_feedback(self) -> bool:
        return self._feedback
