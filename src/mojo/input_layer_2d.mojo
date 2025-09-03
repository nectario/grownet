from layer import Layer
from neuron import Neuron

struct InputLayer2D:
    var height: Int
    var width: Int
    var core: Layer

    fn init(mut self, height: Int, width: Int, gain: Float64, epsilon_fire: Float64) -> None:
        self.height = height
        self.width = width
        # Map each pixel to one excitatory neuron; no inhib/mod in this input shim.
        self.core = Layer(height * width, 0, 0)

    fn index(self, row: Int, col: Int) -> Int:
        return row * self.width + col

    fn forward_image(mut self, frame: list[list[Float64]]) -> None:
        # Fan out each pixel into the corresponding excit neuron (row-major).
        var row = 0
        while row < self.height:
            var col = 0
            while col < self.width:
                var pixel_value = frame[row][col]
                self.core.forward(pixel_value)
                col += 1
            row += 1
        # Do not call end_tick here; Region handles it per layer

    fn get_neurons(self) -> list[Neuron]:
        return self.core.get_neurons()

    fn get_bus(self) -> LateralBus:
        return self.core.bus

    fn propagate_from(mut self, source_index: Int, value: Float64) -> None:
        # Inputs are sinks; nothing to do.
        pass
