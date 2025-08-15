from weight import Weight

struct Synapse:
    var target_index: Int
    var feedback: Bool = False
    var w: Weight

    fn init(inout self, target_index: Int, feedback: Bool) -> None:
        self.target_index = target_index
        self.feedback = feedback
        self.w = Weight()
