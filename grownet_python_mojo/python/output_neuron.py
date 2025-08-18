from neuron import Neuron

class OutputNeuron(Neuron):
    def __init__(self, neuron_id: str, bus, smoothing: float = 0.2) -> None:
        super().__init__(neuron_id, bus)
        self._smoothing = float(smoothing)
        self._last_emitted: float = 0.0

    def on_input(self, value: float) -> bool:
        # Smooth a running value for inspection
        self._last_emitted = (1.0 - self._smoothing) * self._last_emitted + self._smoothing * value
        return self.fire(self._last_emitted)

    def end_tick(self) -> None:
        # Light decay
        self._last_emitted *= (1.0 - self._smoothing)
