import Python

# Minimal synapse to mirror Python shape.
class Neuron:  # forward decl for type names (actual class in neuron.mojo)
    pass

struct Synapse:
    var pre: Neuron
    var post: Neuron
    var weight: Float64
    var feedback: Bool

    fn __init__(inout self, pre: Neuron, post: Neuron, weight: Float64 = 1.0, feedback: Bool = False):
        self.pre = pre
        self.post = post
        self.weight = weight
        self.feedback = feedback

    fn transmit(inout self, value: Float64):
        self.post.on_input(value * self.weight)
