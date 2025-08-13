from layer import Layer
from input_layer_2d import InputLayer2D
from output_layer_2d import OutputLayer2D

struct Tract:
    var src_index: Int64
    var dst_index: Int64
    var edges: Dict[Int64, Array[Int64]]   # srcNeuron -> [dstNeurons]
    var probability: Float64

    fn __init__(src_index: Int64, dst_index: Int64, probability: Float64) -> Self:
        return Self(src_index, dst_index, Dict[Int64, Array[Int64]](), probability)

    fn wire_dense_deterministic(mut self , src_count: Int64, dst_count: Int64):
        if self.probability <= 0.0: return
        let threshold = Int64(self.probability * 10000.0)
        for s in range(src_count):
            var fan = Array[Int64]()
            for d in range(dst_count):
                # deterministic pseudo-random without RNG
                let score = (Int64( s * 9973 + d * 7919 ) % 10000)
                if score < threshold:
                    fan.append(Int64(d))
            if fan.size > 0:
                self.edges[Int64(s)] = fan

    fn flush(mut self , mut region: Region) -> Int64:
        var delivered: Int64 = 0
        var src_layer = region.layers[self.src_index]
        var dst_layer = region.layers[self.dst_index]
        for ev in src_layer.local_fires:
            let sidx = ev.source_index
            let value = ev.amplitude
            let list_opt = self.edges.get(sidx)
            if list_opt is None:
                continue
            let lst = list_opt!
            for d in lst:
                dst_layer.receive_from_tract(d, value)
                delivered += 1
        region.layers[self.dst_index] = dst_layer
        return delivered

struct Region:
    var name: String
    var layers: Array[Layer]
    var input_2d: Dict[Int64, InputLayer2D]
    var output_2d: Dict[Int64, OutputLayer2D]
    var input_ports: Dict[String, Array[Int64]]
    var tracts: Array[Tract]

    fn __init__(name: String) -> Self:
        return Self(
            name = name,
            layers = Array[Layer](),
            input_2d = Dict[Int64, InputLayer2D](),
            output_2d = Dict[Int64, OutputLayer2D](),
            input_ports = Dict[String, Array[Int64]](),
            tracts = Array[Tract]()
        )

    fn add_layer(mut self , excitatory_count: Int64, inhibitory_count: Int64, modulatory_count: Int64) -> Int64:
        var layer = Layer()
        from neuron import Neuron, NeuronType
        for _ in range(excitatory_count): layer.add_neuron(Neuron(NeuronType.EXCITATORY, layer.bus))
        for _ in range(inhibitory_count): layer.add_neuron(Neuron(NeuronType.INHIBITORY, layer.bus))
        for _ in range(modulatory_count): layer.add_neuron(Neuron(NeuronType.MODULATORY, layer.bus))
        self.layers.append(layer)
        return Int64(self.layers.size) - 1

    fn add_input_layer_2d(mut self , h: Int64, w: Int64, gain: Float64 = 1.0, epsilon_fire_unused: Float64 = 0.01) -> Int64:
        var wrapper = InputLayer2D(h, w, gain)
        self.layers.append(wrapper.base)
        let idx = Int64(self.layers.size) - 1
        self.input_2d[idx] = wrapper
        return idx

    fn add_output_layer_2d(mut self , h: Int64, w: Int64, smoothing: Float64 = 0.20) -> Int64:
        var wrapper = OutputLayer2D(h, w, smoothing)
        self.layers.append(wrapper.base)
        let idx = Int64(self.layers.size) - 1
        self.output_2d[idx] = wrapper
        return idx

    fn bind_input(mut self , port: String, layer_indexes: Array[Int64]):
        self.input_ports[port] = layer_indexes

    fn connect_layers(mut self , src_index: Int64, dst_index: Int64, probability: Float64, feedback: Bool = False) -> Tract:
        var t = Tract(src_index, dst_index, probability)
        t.wire_dense_deterministic(Int64(self.layers[src_index].neurons.size),
                                   Int64(self.layers[dst_index].neurons.size))
        self.tracts.append(t)
        return t

    fn tick_image(mut self, port: String, image: Array[Array[Float64]]) -> Dict[String, Float64]:

        # -------- Phase A: drive bound input 2D layers --------
        if self.input_ports.has(port):
            var bound = self.input_ports[port]           # Array[Int64]
            for bi in range(Int64(bound.size())):
                var idx = bound[bi]
                if self.input_2d.has(idx):
                    var wrapper = self.input_2d[idx]     # InputLayer2D
                    wrapper.forward_image(image)         # no container re-assignment

        # -------- Phase B: flush inter-layer tracts once ------
        var delivered: Int64 = 0
        for ti in range(Int64(self.tracts.size())):
            delivered += self.tracts[ti].flush(self)     # Tract.flush(region) -> Int64

        # -------- Finalize outputs ----------------------------
        for li in range(Int64(self.layers.size())):
            if self.output_2d.has(li):
                var out_neuron = self.output_2d[li]             # OutputLayer2D
                out_neuron.end_tick()                           # compute EMA frame

        # -------- Decay buses ---------------------------------
        for li in range(Int64(self.layers.size())):
            # Call directly on the element; avoid write-back like self.layers[li] = layer
            self.layers[li].bus.decay()
        self.bus.decay()

        # -------- Metrics -------------------------------------
        var total_slots: Int64 = 0
        var total_synapses: Int64 = 0

        for li in range(Int64(self.layers.size())):
            var layer = self.layers[li]
            # count slots
            for ni in range(Int64(layer.neurons.size())):
                total_slots += Int64(layer.neurons[ni].slots.size())
            # count intra-layer adjacency edges
            for si in range(Int64(layer.neurons.size())):
                if layer.adjacency.has(si):
                    total_synapses += Int64(layer.adjacency[si].size())

        # Note: if your Tract exposes `edge_count()`, you can add inter-layer edges too:
        # for ti in range(Int64(self.tracts.size())):
        #     total_synapses += self.tracts[ti].edge_count()

        var m = Dict[String, Float64]()
        m["delivered_events"] = Float64(delivered)
        m["total_slots"]      = Float64(total_slots)
        m["total_synapses"]   = Float64(total_synapses)
        return m

