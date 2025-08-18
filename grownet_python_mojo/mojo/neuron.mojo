from region_bus import RegionBus
from synapse import Synapse
import Vector

# NOTE: This is intentionally conservative Mojo that mirrors the Python API.
class Neuron:
    var id: String
    var bus: RegionBus
    var slot_limit: Int64
    var outgoing: Vector[Synapse]
    var last_input: Float64
    var has_hook: Bool

    # Hook signature: (who, value) -> None ; we store as a Python callable for simplicity today.
    var py_hook: PythonObject

    fn __init__(inout self, id: String, bus: RegionBus, slot_limit: Int64 = 64):
        self.id = id
        self.bus = bus
        self.slot_limit = slot_limit
        self.outgoing = Vector[Synapse]()
        self.last_input = 0.0
        self.has_hook = False
        self.py_hook = Python.none()

    fn connect(inout self, other: Neuron, feedback: Bool = False):
        let s = Synapse(self, other, 1.0, feedback)
        self.outgoing.push_back(s)

    fn on_input(inout self, value: Float64) -> Bool:
        let inhib = self.bus.get_inhibition_factor()
        let eff = value * (1.0 - (if inhib > 1.0 { 1.0 } else if inhib < 0.0 { 0.0 } else { inhib }))
        self.last_input = eff
        return self.fire(eff)

    fn fire(inout self, value: Float64) -> Bool:
        if self.has_hook:
            Python.call(self.py_hook, self, value)
        for s in self.outgoing:
            s.transmit(value)
        return True

    fn end_tick(inout self):
        self.last_input = 0.0

    fn register_fire_hook(inout self, hook: PythonObject):
        self.py_hook = hook
        self.has_hook = True

    fn get_id(self) -> String:
        return self.id

    fn get_outgoing(self) -> Vector[Synapse]:
        return self.outgoing
