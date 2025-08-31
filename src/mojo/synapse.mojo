from weight import Weight

struct Synapse:
    var target_index: Int
    var feedback: Bool = False
    var weight_state: Weight

    fn init(mut self, target_index: Int, feedback: Bool) -> None:
        self.target_index = target_index
        self.feedback = feedback
        self.weight_state = Weight()
