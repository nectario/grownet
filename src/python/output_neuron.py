# output_neuron.py
# Ensure parity with Java/C++: provide getOutputValue() and endTick()

class OutputNeuron:
    def __init__(self, name: str, smoothing: float = 0.0):
        # Minimal surface to keep compatibility; adapt if your real base class differs.
        self._name = name
        self._smoothing = float(smoothing)
        self._lastEmitted = 0.0
        # Expected in your project: slots map, bus reference, etc.
        self._slots = {}
        self._outgoing = []

    # ---- project hooks (these exist in your full implementation) ----
    def onInput(self, value: float) -> bool:
        # User's full implementation will decide when to emit; here just capture.
        self._lastEmitted = value
        return True

    def onOutput(self, amplitude: float) -> None:
        self._lastEmitted = amplitude

    def endTick(self) -> None:
        # decay toward zero like Java/C++
        self._lastEmitted *= (1.0 - self._smoothing)

    # ---- metrics-facing helpers expected by Region aggregation ----
    def getSlots(self):
        return self._slots

    def getOutgoing(self):
        return self._outgoing

    # ---- new method for parity ----
    def getOutputValue(self) -> float:
        return self._lastEmitted
