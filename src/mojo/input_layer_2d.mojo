from input_neuron import InputNeuron

struct InputLayer2D:
    var height: Int64
    var width: Int64
    var neurons: Array[InputNeuron] = Array()

    fn init(self, height: Int64, width: Int64, gain: Float64 = 1.0, epsilon_fire: Float64 = 0.01):
        self.height = height
        self.width = width
        for y in range(height):
            for x in range(width):
                var n = InputNeuron(name=f"IN[{y},{x}]", gain=gain, epsilon_fire=epsilon_fire)
                self.neurons.push(n)

    fn index(self, y: Int64, x: Int64) -> Int64:
        return y * self.width + x

    fn forward_image(self, image: Array[Array[Float64]], modulation: Float64 = 1.0, inhibition: Float64 = 1.0):
        for y in range(self.height):
            for x in range(self.width):
                var idx = self.index(y, x)
                _ = self.neurons[idx].on_sensor_value(image[Int(y)][Int(x)], modulation, inhibition)
