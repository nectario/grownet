from layer import Layer

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

    fn forward_image(mut self, frame: list[list[Float64]]) -> list[Spike]:
        # Fan out each pixel into the corresponding excit neuron (row-major).
        var spikes = []
        var row = 0
        while row < self.height:
            var col = 0
            while col < self.width:
                let pixel_value = frame[row][col]
                let sub = self.core.forward(pixel_value)
                # Offset not tracked (flat mapping); keep amplitudes only.
                for s in sub:
                    spikes.append(s)
                col += 1
            row += 1
        self.core.end_tick()
        return spikes
