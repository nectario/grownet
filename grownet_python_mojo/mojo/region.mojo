from region_bus import RegionBus
from region_metrics import RegionMetrics
from layer import Layer
import Vector
import Random

struct PruneSummary:
    var pruned_synapses: Int64
    var pruned_edges: Int64
    fn __init__(inout self):
        self.pruned_synapses = 0
        self.pruned_edges = 0

class Region:
    var name: String
    var layers: Vector[Layer]
    var input_ports: PythonDictionary
    var output_ports: PythonDictionary
    var bus: RegionBus

    fn __init__(inout self, name: String):
        self.name = name
        self.layers = Vector[Layer]()
        self.input_ports = Python.dict()
        self.output_ports = Python.dict()
        self.bus = RegionBus()

    fn add_layer(inout self, excitatory_count: Int64, inhibitory_count: Int64, modulatory_count: Int64) -> Int64:
        let layer = Layer(excitatory_count, inhibitory_count, modulatory_count, self.bus)
        self.layers.push_back(layer)
        return Int64(self.layers.size() - 1)

    fn bind_input(inout self, port: String, layer_indices: PythonObject):
        Python.set_item(self.input_ports, port, layer_indices)

    fn bind_output(inout self, port: String, layer_indices: PythonObject):
        Python.set_item(self.output_ports, port, layer_indices)

    fn connect_layers(inout self, source_index: Int64, dest_index: Int64, probability: Float64, feedback: Bool = False) -> Int64:
        let p = if probability < 0.0 { 0.0 } else if probability > 1.0 { 1.0 } else { probability }
        let src = self.layers[source_index]
        let dst = self.layers[dest_index]
        let rng = Random.default()
        var edges: Int64 = 0
        for a in src.get_neurons():
            for b in dst.get_neurons():
                if a.get_id() != b.get_id():
                    if Random.random_f64(rng) < p:
                        a.connect(b, feedback)
                        edges += 1
                    end
                end
            end
        end
        return edges

    fn pulse_inhibition(inout self, factor: Float64):
        self.bus.set_inhibition_factor(factor)

    fn pulse_modulation(inout self, factor: Float64):
        self.bus.set_modulation_factor(factor)

    fn tick(inout self, port: String, value: Float64) -> RegionMetrics:
        var m = RegionMetrics()
        if Python.has_key(self.input_ports, port):
            let entry = Python.get_item(self.input_ports, port)
            for idx in Python.iter(entry):
                self.layers[Int64(Python.to_int(idx))].forward(value)
                m.inc_delivered_events()
            end
        end
        for layer in self.layers:
            layer.end_tick()
        for layer in self.layers:
            for neuron in layer.get_neurons():
                m.add_slots(0)          # slots not tracked in this minimal mirror
                m.add_synapses(Int64(neuron.get_outgoing().size()))
            end
        end
        return m
