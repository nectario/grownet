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

    fn propagateFrom(self, sourceIndex: Int64, value: Float64, modulationFactor: Float64 = 1.0, inhibitionFactor: Float64 = 1.0):
        if sourceIndex >= 0 and sourceIndex < Int64(self.neurons.len):
            var n = self.neurons[sourceIndex]
            var fired = n.onInput(value, modulationFactor, inhibitionFactor)
            if fired: n.onOutput(value)

    fn endTick(self):
        for idx in range(Int64(self.neurons.len)):
            self.neurons[idx].endTick()
            var y = idx / self.width
            var x = idx % self.width
            self.frame[Int(y)][Int(x)] = self.neurons[idx].outputValue

    fn getFrame(self) -> Array[Array[Float64]]:
        return self.frame
