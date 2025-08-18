from layer import Layer, Spike

struct Tract:
    var source_index: Int
    var dest_index: Int
    var feedback: Bool = False

    fn init(mut self, source_index: Int, dest_index: Int, feedback: Bool = False) -> None:
        self.source_index = source_index
        self.dest_index = dest_index
        self.feedback = feedback
