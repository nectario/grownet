from dataclasses import dataclass, field
from typing import Optional
from neuron import Neuron
from .weight import Weight

@dataclass
class Synapse:
    source_id: str
    target: Optional['Neuron']  # forward reference
    weight: Weight = field(default_factory=Weight)
    is_feedback: bool = False
    last_step: int = 0

    def deliver(self, value: float) -> None:
        if self.target is not None:
            self.target.on_input(value)

