from layer import Layer
from neuron import Neuron, NeuronType

struct OutputLayer2D:
    var base: Layer
    var height: Int64
    var width: Int64

    fn __init__(h: Int64, w: Int64, smoothing: Float64 = 0.20) -> Self:
        var layer = Layer()
        for _ in range(h * w):
            layer.add_neuron(Neuron(NeuronType.OUTPUT, layer.bus, smoothing))
        return Self(base = layer, height = h, width = w)

    fn end_tick(mut self ):
        let n = Int64(self.base.neurons.size)
        for i in range(n):
            var neu = self.base.neurons[i]
            neu.end_tick()
            self.base.neurons[i] = neu

    fn get_frame(self) -> Array[Array[Float64]]:
        var img = Array[Array[Float64]](self.height)
        var idx: Int64 = 0
        for y in range(self.height):
            var row = Array[Float64](self.width)
            for x in range(self.width):
                row[Int(x)] = self.base.neurons[idx].output_value
                idx += 1
            img[Int(y)] = row
        return img
