from input_neuron import InputNeuron

struct InputLayer2D:
    var height: Int64
    var width: Int64
    var neurons: Array[InputNeuron] = Array()

    fn init(self, height: Int64, width: Int64, gain: Float64 = 1.0, epsilonFire: Float64 = 0.01):
        self.height = height
        self.width = width
        for y in range(height):
            for x in range(width):
                var n = InputNeuron(name=f"IN[{y},{x}]", gain=gain, epsilonFire=epsilonFire)
                self.neurons.push(n)

    fn index(self, y: Int64, x: Int64) -> Int64:
        return y * self.width + x

    fn forwardImage(self, image: Array[Array[Float64]], modulationFactor: Float64 = 1.0, inhibitionFactor: Float64 = 1.0):
        for y in range(self.height):
            for x in range(self.width):
                var idx = self.index(y, x)
                var v = image[Int(y)][Int(x)]
                var fired = self.neurons[idx].onInput(v, modulationFactor, inhibitionFactor)
                if fired:
                    self.neurons[idx].onOutput(v)
