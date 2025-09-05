# output_neuron.py
# Ensure parity with Java/C++: provide get_output_value() and end_tick()
from neuron import Neuron
class OutputNeuron(Neuron):


    def __init__(self, neuron_id: str, smoothing: float = 0.0):
        super().__init__(neuron_id, bus=None, slot_cfg=None, slot_limit=1)  # single-slot sink
        # Minimal surface to keep compatibility; adapt if your real base class differs.
        self.name = neuron_id
        self.smoothing = float(smoothing)
        self.last_emitted = 0.0

        # Expected in your project: slots map, bus reference, etc.
        self.slots = {}
        self.outgoing = []


    # ---- project hooks (these exist in your full implementation) ----
    def on_input(self, value: float) -> bool:

        # User's full implementation will decide when to emit; here just capture.
        self.last_emitted = value
        return True

    def on_output(self, amplitude: float) -> None:
        self.last_emitted = amplitude

    def end_tick(self) -> None:

        # decay toward zero like Java/C++
        self.last_emitted *= (1.0 - self.smoothing)

    # ---- metrics-facing helpers expected by Region aggregation ----
    def get_slots(self):
        return self.slots

    def get_outgoing(self):
        return self.outgoing

    # ---- new method for parity ----
    def get_output_value(self) -> float:
        return self.last_emitted
