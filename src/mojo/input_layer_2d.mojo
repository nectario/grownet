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

    fn index(self, y: Int, x: Int) -> Int:
        return y * self.width + x

    fn forward_image(mut self, frame: list[list[Float64]]) -> list[Spike]:
        # Fan out each pixel into the corresponding excit neuron.
        var spikes = []
        var y = 0
        while y < self.height:
            var x = 0
            while x < self.width:
                let v = frame[y][x]
                let sub = self.core.forward(v)
                # Offset not tracked (flat mapping); keep amplitudes only.
                for s in sub:
                    spikes.append(s)
                x += 1
            y += 1
        self.core.end_tick()
        return spikes
