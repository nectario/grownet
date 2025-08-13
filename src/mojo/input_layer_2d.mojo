from layer import Layer, FireEvent
from neuron import Neuron, NeuronType

struct InputLayer2D:
    var base: Layer
    var height: Int64
    var width: Int64
    var gain: Float64

    fn __init__(h: Int64, w: Int64, gain: Float64 = 1.0) -> Self:
        var layer = Layer()
        # one Input neuron per pixel
        for _ in range(h * w):
            layer.add_neuron(Neuron(NeuronType.INPUT, layer.bus))
        return Self(base = layer, height = h, width = w, gain = gain)

    fn forward_image(mut self , image: Array[Array[Float64]]):
        self.base.local_fires.clear()
        var idx: Int64 = 0
        for y in range(self.height):
            for x in range(self.width):
                let v = image[Int(y)][Int(x)] * self.gain
                var neu = self.base.neurons[idx]
                let fired = neu.on_input(v)
                if fired:
                    neu.on_output(v)
                    self.base.local_fires.append(FireEvent(idx, v))
                self.base.neurons[idx] = neu
                idx += 1
