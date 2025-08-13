from neuron import Neuron, LateralBus

struct FireEvent:
    var source_index: Int64
    var amplitude: Float64

    fn __init__(source_index: Int64, amplitude: Float64) -> Self:
        return Self(source_index, amplitude)

struct Layer:
    var neurons: Array[Neuron]
    var bus: LateralBus
    var adjacency: Dict[Int64, Array[Int64]]    # intra-layer routing
    var local_fires: Array[FireEvent]           # collected during Phase A

    fn __init__() -> Self:
        return Self(
            neurons = Array[Neuron](),
            bus = LateralBus(),
            adjacency = Dict[Int64, Array[Int64]](),
            local_fires = Array[FireEvent]()
        )

    fn add_neuron(mut self , neuron: Neuron) -> Int64:
        self.neurons.append(neuron)
        return Int64(self.neurons.size) - 1

    fn connect_intra(mut self , src: Int64, dst: Int64):
        var lst = self.adjacency.get(src)
        if lst is None:
            lst = Array[Int64]()
        lst.append(dst)
        self.adjacency[src] = lst

    fn forward(mut self , value: Float64):
        self.local_fires.clear()
        let n = Int64(self.neurons.size)
        for i in range(n):
            var neu = self.neurons[i]
            let fired = neu.on_input(value)
            if fired:
                neu.on_output(value)
                self.local_fires.append(FireEvent(i, value))
            self.neurons[i] = neu

    fn propagate_from(mut self , source_index: Int64, value: Float64):
        let neigh_opt = self.adjacency.get(source_index)
        if neigh_opt is None:
            return
        let neigh = neigh_opt!
        for j in neigh:
            var dst = self.neurons[j]
            let fired = dst.on_input(value)
            if fired:
                dst.on_output(value)
            self.neurons[j] = dst

    fn receive_from_tract(mut self , target_index: Int64, value: Float64):
        var dst = self.neurons[target_index]
        let fired = dst.on_input(value)
        if fired:
            dst.on_output(value)
        self.neurons[target_index] = dst

    fn decay_bus(mut self ):
        self.bus.decay()
