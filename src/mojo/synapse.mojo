from weight import Weight

struct Synapse:
    var target_index: Int
    var feedback: Bool = False
    var weight_state: Weight
    # minimal bookkeeping for parity shims
    var last_seen_tick: Int64 = 0

    fn init(mut self, target_index: Int, feedback: Bool) -> None:
        self.target_index = target_index
        self.feedback = feedback
        self.weight_state = Weight()

    # Parity accessors
    fn get_last_seen_tick(self) -> Int64:
        return self.last_seen_tick

    fn set_last_seen_tick(mut self, t: Int64) -> None:
        self.last_seen_tick = t

    fn get_strength_value(self) -> Float64:
        return self.weight_state.strength

    fn set_strength_value(mut self, s: Float64) -> None:
        self.weight_state.strength = s
