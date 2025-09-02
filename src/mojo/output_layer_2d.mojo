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

    fn init(mut self, height: Int, width: Int, smoothing: Float64) -> None:
        self.height = height
        self.width = width
        self.smoothing = smoothing
        self.core = Layer(height * width, 0, 0)
        self.pixels = []
        var row_index = 0
        while row_index < height:
            var row = []
            var col_index = 0
            while col_index < width:
                row.append(0.0)
                col_index += 1
            self.pixels.append(row)
            row_index += 1
        self.states = []
        var index = 0
        while index < height * width:
            self.states.append(OutputNeuronState())
            index += 1

    fn index(self, row: Int, col: Int) -> Int:
        return row * self.width + col

    fn propagate_from(mut self, source_index: Int, value: Float64) -> None:
        # Sinks are passive; we merely record output activity.
        var row_index = source_index / self.width
        var col_index = source_index % self.width
        var neuron_state = self.states[source_index]
        neuron_state.last_emitted = value
        self.states[source_index] = neuron_state
        self.pixels[row_index][col_index] = value

    fn end_tick(mut self) -> None:
        # Simple exponential decay on pixel values to simulate persistence.
        var index = 0
        while index < self.height * self.width:
            var row_index = index / self.width
            var col_index = index % self.width
            self.pixels[row_index][col_index] = self.pixels[row_index][col_index] * (1.0 - self.smoothing)
            index += 1

    fn get_frame(self) -> list[list[Float64]]:
        return self.pixels
