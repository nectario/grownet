from weight import Weight

class Synapse:
    """Directed edge: source neuron --(weight)--> target neuron, with routing metadata."""
    __slots__ = ("weight", "target", "is_feedback", "last_step")

    def __init__(self, target, is_feedback: bool = False):
        self.weight = Weight()
        self.target = target
        self.is_feedback = is_feedback
        self.last_step = 0  # updated from LateralBus.current_step when used
