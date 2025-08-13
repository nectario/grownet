# layer.py
# A mixed-type neuron layer with a local LateralBus and simple wiring helpers.

from typing import List
import random

from bus import LateralBus
from neuron import Neuron
from neuron_excitatory import ExcitatoryNeuron
from neuron_inhibitory import InhibitoryNeuron
from neuron_modulatory import ModulatoryNeuron


class Layer:
    """
    A collection of neurons that share a LateralBus (inhibition/modulation),
    plus convenience helpers to create random intra-layer fan-out.

    __init__ accepts both the long argument names (excitatory_count, etc.)
    and the short aliases (size_exc, size_inhib, size_mod) used by some demos.
    """

    def __init__(
        self,
        excitatory_count: int | None = None,
        inhibitory_count: int | None = None,
        modulatory_count: int | None = None,
        **kwargs,
    ) -> None:
        # Support short aliases used by train_omniglot.py
        if excitatory_count is None:
            excitatory_count = int(kwargs.get("size_exc", 0))
        if inhibitory_count is None:
            inhibitory_count = int(kwargs.get("size_inhib", 0))
        if modulatory_count is None:
            modulatory_count = int(kwargs.get("size_mod", 0))

        self.bus: LateralBus = LateralBus()
        self.neurons: List[Neuron] = []
        self.random_generator: random.Random = random.Random(1234)

        # Instantiate the requested neuron population.
        # NOTE: use neuron_id=... (not name=...) to match the Neuron API.
        for i in range(excitatory_count):
            n = ExcitatoryNeuron(neuron_id=f"E{i}", bus=self.bus)
            self.neurons.append(n)

        for i in range(inhibitory_count):
            n = InhibitoryNeuron(neuron_id=f"I{i}", bus=self.bus)
            self.neurons.append(n)

        for i in range(modulatory_count):
            n = ModulatoryNeuron(neuron_id=f"M{i}", bus=self.bus)
            self.neurons.append(n)

    # --- wiring helpers (unchanged public API expected by demos) ----------------

    def wire_random_feedforward(self, probability: float) -> None:
        """Create random forward edges inside this layer (demo-only)."""
        for source in self.neurons:
            for target in self.neurons:
                if source is target:
                    continue
                if self.random_generator.random() < probability:
                    source.connect(target, is_feedback=False)

    def wire_random_feedback(self, probability: float) -> None:
        """Create random feedback edges inside this layer (demo-only)."""
        for source in self.neurons:
            for target in self.neurons:
                if source is target:
                    continue
                if self.random_generator.random() < probability:
                    source.connect(target, is_feedback=True)

    # --- drive all neurons with the same scalar (used by Region.tick) ----------

    def forward(self, value: float) -> None:
        """Feed a scalar to all neurons in the layer for one tick."""
        for neuron in self.neurons:
            fired = neuron.on_input(value)
            if fired:
                neuron.on_output(value)

    # Convenience accessors used by Region metrics/maintenance
    def get_bus(self) -> LateralBus:
        return self.bus
