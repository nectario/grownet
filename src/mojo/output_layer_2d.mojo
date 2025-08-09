from output_neuron import OutputNeuron

struct OutputLayer2D:
    var height: Int64
    var width: Int64
    var neurons: Array[OutputNeuron] = Array()
    var frame: Array[Array[Float64]]

    fn init(self, height: Int64, width: Int64, smoothing: Float64 = 0.2):
        self.height = height
        self.width = width
        for y in range(self.height):
            for x in range(self.width):
                var n = OutputNeuron(name=f"OUT[{y},{x}]", smoothing=smoothing)
                self.neurons.push(n)
        self.frame = Array[Array[Float64]](self.height)
        for y in range(self.height):
            var row = Array[Float64](self.width)
            for x in range(self.width):
                row[x] = 0.0
            self.frame[y] = row

    fn index(self, y: Int64, x: Int64) -> Int64:
        return y * self.width + x

    fn propagate_from(self, source_index: Int64, value: Float64, modulation: Float64 = 1.0, inhibition: Float64 = 1.0):
        if source_index >= 0 and source_index < Int64(self.neurons.len):
            _ = self.neurons[source_index].on_routed_event(value, modulation, inhibition)

    fn end_tick(self):
        for idx in range(Int64(self.neurons.len)):
            self.neurons[idx].end_tick()
            var y = idx / self.width
            var x = idx % self.width
            self.frame[Int(y)][Int(x)] = self.neurons[idx].output_value

    fn get_frame(self) -> Array[Array[Float64]]:
        return self.frame
