import random
from neuron_excitatory import ExcitatoryNeuron
from neuron_inhibitory import InhibitoryNeuron
from neuron_modulatory import ModulatoryNeuron
from neuron import Neuron
from lateral_bus import LateralBus
from slot_config import SlotConfig

class Layer:
    """Mixed E/I/M population with a shared lateral bus + growth hooks."""
    def __init__(self, excitatory_count, inhibitory_count, modulatory_count, neuron_limit: int | None = None):
        self.bus = LateralBus()
        self.rng = random.Random(1234)
        self.neurons = []
        # store counts for potential spillover sizing
        self.excitatory_count = int(excitatory_count)
        self.inhibitory_count = int(inhibitory_count)
        self.modulatory_count = int(modulatory_count)
        # default slot policy baked into Neuron base
        for idx in range(self.excitatory_count):
            neuron = ExcitatoryNeuron(f"E{idx}")
            neuron.set_bus(self.bus)
            neuron.owner = self
            self.neurons.append(neuron)
        for idx in range(self.inhibitory_count):
            neuron = InhibitoryNeuron(f"I{idx}")
            neuron.set_bus(self.bus)
            neuron.owner = self
            self.neurons.append(neuron)
        for idx in range(self.modulatory_count):
            neuron = ModulatoryNeuron(f"M{idx}")
            neuron.set_bus(self.bus)
            neuron.owner = self
            self.neurons.append(neuron)
        # Region backref for growth plumbing
        self._region = None
        # Per-layer neuron cap (overrides SlotConfig default if provided)
        default_cap = getattr(SlotConfig, "layer_neuron_limit_default", -1)
        self.neuron_limit = default_cap if neuron_limit is None else int(neuron_limit)

    def get_neurons(self):
        return self.neurons

    def get_bus(self):
        return self.bus

    # wiring
    def wire_random_feedforward(self, probability):
        for src_neuron in self.neurons:
            for dst_neuron in self.neurons:
                if src_neuron is dst_neuron:
                    continue
                if self.rng.random() < probability:
                    src_neuron.connect(dst_neuron, feedback=False)

    def wire_random_feedback(self, probability):
        for src_neuron in self.neurons:
            for dst_neuron in self.neurons:
                if src_neuron is dst_neuron:
                    continue
                if self.rng.random() < probability:
                    src_neuron.connect(dst_neuron, feedback=True)

    # main drive
    def forward(self, value):
        """Drive all neurons with a scalar for this tick."""
        for neuron in self.neurons:
            fired = neuron.on_input(value)
            if fired:
                neuron.on_output(value)

    def propagate_from(self, source_index, value):
        # default: treat like uniform drive from external source
        self.forward(value)

    def propagate_from_2d(self, source_index: int, value: float, height: int, width: int) -> None:
        """Destination-side hook for 2D-aware propagation.

        Computes (row,col) from source_index and calls each neuron's spatial
        on_input_2d if available/enabled, else falls back to scalar on_input.
        """
        try:
            row = int(source_index) // int(width)
            col = int(source_index) % int(width)
        except Exception:
            # if shape is invalid, fallback to scalar
            row, col = 0, 0
        for neuron in self.neurons:
            fired = False
            if hasattr(neuron, "on_input_2d"):
                try:
                    fired = neuron.on_input_2d(value, row, col)
                except Exception:
                    fired = neuron.on_input(value)
            else:
                fired = neuron.on_input(value)
            if fired:
                neuron.on_output(value)

    def end_tick(self):
        # Decay the bus; give neurons a chance to do housekeeping
        for neuron in self.neurons:
            neuron.end_tick()
        self.bus.decay()

    # ---- growth API (called by Neuron) ----
    def try_grow_neuron(self, seed_neuron) -> int | None:
        """Add a new neuron cloned from 'seed_neuron' behavior and auto-wire it via Region.

        Returns the new neuron index or None if growth was blocked.
        """
        # Enforce per-layer cap if set
        if self.neuron_limit is not None and int(self.neuron_limit) >= 0:
            if len(self.neurons) >= int(self.neuron_limit):
                # Escalate to layer growth if enabled on requesting neuron
                if self._region and getattr(getattr(seed_neuron, "slot_cfg", object()), "layer_growth_enabled", False):
                    try:
                        self._region.request_layer_growth(self)
                    except Exception:
                        pass
                return None

        # Instantiate same class as seed if possible; default to ExcitatoryNeuron
        cls = type(seed_neuron)
        try:
            if issubclass(cls, Neuron):
                name = f"G{len(self.neurons)}"
                new_n = cls(name)
            else:
                new_n = ExcitatoryNeuron(f"E{len(self.neurons)}")
        except Exception:
            new_n = ExcitatoryNeuron(f"E{len(self.neurons)}")

        # Copy over bus/config/limits
        try:
            new_n.set_bus(self.bus)
        except Exception:
            new_n.bus = self.bus
        try:
            new_n.slot_cfg = seed_neuron.slot_cfg
            new_n.slot_engine = seed_neuron.slot_engine
            new_n.slot_limit = seed_neuron.slot_limit
        except Exception:
            pass
        new_n.owner = self
        self.neurons.append(new_n)

        # Autowire using Region rules/tracts
        try:
            if self._region is not None:
                self._region._autowire_new_neuron(self, len(self.neurons) - 1)
        except Exception:
            pass
        return len(self.neurons) - 1

    # Region injects itself so the layer can call back on growth
    def _set_region(self, region):
        self._region = region
