from layer import Layer, Spike

struct OutputNeuronState:
    var last_emitted: Float64 = 0.0

struct OutputLayer2D:
    var height: Int
    var width: Int
    var core: Layer
    var pixels: list[list[Float64]]
    var smoothing: Float64
    var states: list[OutputNeuronState]

    fn init(inout self, height: Int, width: Int, smoothing: Float64) -> None:
        self.height = height
        self.width = width
        self.smoothing = smoothing
        self.core = Layer(height * width, 0, 0)
        self.pixels = []
        var r = 0
        while r < height:
            var row = []
            var c = 0
            while c < width:
                row.append(0.0)
                c += 1
            self.pixels.append(row)
            r += 1
        self.states = []
        var i = 0
        while i < height * width:
            self.states.append(OutputNeuronState())
            i += 1

    fn index(self, y: Int, x: Int) -> Int:
        return y * self.width + x

    fn propagate_from(inout self, source_index: Int, value: Float64) -> None:
        # Sinks are passive; we merely record output activity.
        let y = source_index / self.width
        let x = source_index % self.width
        var s = self.states[source_index]
        s.last_emitted = value
        self.states[source_index] = s
        self.pixels[y][x] = value

    fn end_tick(inout self) -> None:
        # Simple exponential decay on pixel values to simulate persistence.
        var i = 0
        while i < self.height * self.width:
            let y = i / self.width
            let x = i % self.width
            self.pixels[y][x] = self.pixels[y][x] * (1.0 - self.smoothing)
            i += 1

    fn get_frame(self) -> list[list[Float64]]:
        return self.pixels
