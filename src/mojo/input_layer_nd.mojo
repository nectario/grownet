
from layer import Layer

struct InputLayerND:
    var shape: List[Int]
    var size: Int
    var core: Layer

    fn init(mut self, shape: List[Int], gain: Float64, epsilon_fire: Float64) -> None:
        if shape.size == 0:
            raise Exception("shape must be rank >= 1")
        self.shape = List[Int]()
        var index: Int = 0
        var total: Int = 1
        while index < shape.size:
            var dim = shape[index]
            if dim <= 0:
                raise Exception("shape dims must be > 0")
            self.shape.append(dim)
            total = total * dim
            index += 1
        self.size = total
        self.core = Layer(self.size, 0, 0)

    fn has_shape(self, other: List[Int]) -> Bool:
        if other.size != self.shape.size:
            return False
        var index: Int = 0
        while index < self.shape.size:
            if self.shape[index] != other[index]:
                return False
            index += 1
        return True

    fn forward_nd(mut self, flat: List[Float64], shape: List[Int]) -> None:
        if not self.has_shape(shape):
            raise Exception("shape mismatch with bound InputLayerND")
        if flat.size != self.size:
            raise Exception("flat length != expected size")
        var index: Int = 0
        while index < self.size:
            self.core.get_neurons()[index].on_input(flat[index])
            index += 1

    fn propagate_from(mut self, source_index: Int, value: Float64) -> None:
        pass
