struct GrowthPolicy:
    var enable_layer_growth: Bool
    var max_total_layers: Int
    var avg_slots_threshold: Float64
    var percent_neurons_at_cap_threshold: Float64
    var layer_cooldown_ticks: Int
    var new_layer_excitatory_count: Int
    var wire_probability: Float64

    fn init(
        enable_layer_growth: Bool = True,
        max_total_layers: Int = -1,
        avg_slots_threshold: Float64 = 8.0,
        percent_neurons_at_cap_threshold: Float64 = 50.0,
        layer_cooldown_ticks: Int = 25,
        new_layer_excitatory_count: Int = 4,
        wire_probability: Float64 = 1.0
    ) -> None:
        self.enable_layer_growth = enable_layer_growth
        self.max_total_layers = max_total_layers
        self.avg_slots_threshold = avg_slots_threshold
        self.percent_neurons_at_cap_threshold = percent_neurons_at_cap_threshold
        self.layer_cooldown_ticks = layer_cooldown_ticks
        self.new_layer_excitatory_count = new_layer_excitatory_count
        self.wire_probability = wire_probability

