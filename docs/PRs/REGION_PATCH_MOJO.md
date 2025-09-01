# Region.mojo patch for IO & image tick

Add factory helpers matching your Layer types:
```mojo
from input_layer_2d import InputLayer2D
from output_layer_2d import OutputLayer2D

fn add_input_layer_2d(self, height: Int64, width: Int64, gain: Float64 = 1.0, epsilon_fire: Float64 = 0.01) -> Int64:
    let layer = InputLayer2D(height, width, gain, epsilon_fire)
    self.layers.append(layer)
    return Int64(self.layers.len) - 1

fn add_output_layer_2d(self, height: Int64, width: Int64, smoothing: Float64 = 0.2) -> Int64:
    let layer = OutputLayer2D(height, width, smoothing)
    self.layers.append(layer)
    return Int64(self.layers.len) - 1
```

Add a convenience tick for images (adapt names if your API differs):
```mojo
fn tick_image(self, port: String, image: Array[Array[Float64]]) -> Dict[String, Float64]:
    # Phase A: drive bound entry layers for this port
    if self.input_ports.contains(port):
        for idx in self.input_ports[port]:
            let layer = self.layers[Int(idx)]
            # If it's an input image layer, call forward_image; otherwise feed scalar mean
            if layer isa InputLayer2D:
                (layer as InputLayer2D).forward_image(image)
            else:
                var sum: Float64 = 0.0
                var count: Int64 = 0
                for row in image:
                    for v in row:
                        sum = sum + v
                        count = count + 1
                let scalar = (count > 0) ? (sum / Float64(count)) : 0.0
                layer.forward(scalar)

    # Phase B: flush tracts
    var delivered: Int64 = 0
    for t in self.tracts:
        delivered = delivered + t.flush()

    # Finalize outputs
    for l in self.layers:
        if l isa OutputLayer2D:
            (l as OutputLayer2D).end_tick()

    # Decay buses
    for l in self.layers:
        l.bus.decay()
    self.bus.decay()

    # Metrics
    var total_slots: Int64 = 0
    var total_synapses: Int64 = 0
    for l in self.layers:
        for n in l.neurons:
            total_slots = total_slots + Int64(n.slots.len)
        for entry in l.adjacency.items():
            total_synapses = total_synapses + Int64(entry.value.len)

    var m = Dict[String, Float64]()
    m["delivered_events"] = Float64(delivered)
    m["total_slots"] = Float64(total_slots)
    m["total_synapses"] = Float64(total_synapses)
    return m
```

Ensure your `Weight` names match the ones used by the Input/Output layers (`first_seen`, `threshold_value`, `strength_value`, `update_threshold`, `reinforce`).
Also ensure your `Layer` calls `neuron.onOutput(value)` when a neuron fires (unified contract).
