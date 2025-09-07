from math import sqrt

struct ProximityConfig:
    var proximity_connect_enabled: Bool = False
    var proximity_radius: Float64 = 1.0
    var proximity_function: String = "STEP"  # STEP | LINEAR | LOGISTIC
    var linear_exponent_gamma: Float64 = 1.0
    var logistic_steepness_k: Float64 = 4.0
    var proximity_max_edges_per_tick: Int = 128
    var proximity_cooldown_ticks: Int = 5
    var development_window_start: Int64 = 0
    var development_window_end: Int64 = 9223372036854775807
    var stabilization_hits: Int = 3
    var decay_if_unused: Bool = True
    var decay_half_life_ticks: Int = 200
    var candidate_layers: list[Int]
    var record_mesh_rules_on_cross_layer: Bool = True

    fn init(mut self):
        self.candidate_layers = []

struct DeterministicLayout:
    var layer_spacing: Float64 = 4.0
    var grid_spacing: Float64 = 1.2

    fn position(self, region_name: String, layer_index: Int, neuron_index: Int, layer_height: Int = 0, layer_width: Int = 0) -> (Float64, Float64, Float64):
        if layer_height > 0 and layer_width > 0:
            var row_index = neuron_index / layer_width
            var col_index = neuron_index % layer_width
            var offset_x = (Float64(col_index) - (Float64(layer_width) - 1.0) / 2.0) * self.grid_spacing
            var offset_y = ((Float64(layer_height) - 1.0) / 2.0 - Float64(row_index)) * self.grid_spacing
            var offset_z = Float64(layer_index) * self.layer_spacing
            return (offset_x, offset_y, offset_z)
        var plus_one = neuron_index + 1
        var grid_side = Int(sqrt(Float64(plus_one)))
        if (grid_side * grid_side) < plus_one:
            grid_side = grid_side + 1
        var row_index2 = neuron_index / grid_side
        var col_index2 = neuron_index % grid_side
        var offset_x2 = (Float64(col_index2) - (Float64(grid_side) - 1.0) / 2.0) * self.grid_spacing
        var offset_y2 = ((Float64(grid_side) - 1.0) / 2.0 - Float64(row_index2)) * self.grid_spacing
        var offset_z2 = Float64(layer_index) * self.layer_spacing
        return (offset_x2, offset_y2, offset_z2)

struct SpatialHash:
    var cell_size: Float64
    var cells: dict[tuple[Int, Int, Int], list[tuple[Int, Int]]]

    fn init(mut self, cell_size: Float64):
        if cell_size <= 0.0:
            raise Error("cell_size must be > 0")
        self.cell_size = cell_size
        self.cells = dict[tuple[Int, Int, Int], list[tuple[Int, Int]]]()

    fn key_for_position(self, position: (Float64, Float64, Float64)) -> (Int, Int, Int):
        var key_x = Int(position[0] / self.cell_size)
        var key_y = Int(position[1] / self.cell_size)
        var key_z = Int(position[2] / self.cell_size)
        return (key_x, key_y, key_z)

    fn insert(mut self, key: (Int, Int), position: (Float64, Float64, Float64)) -> None:
        var bucket_key = self.key_for_position(position)
        if not self.cells.contains(bucket_key):
            self.cells[bucket_key] = []
        self.cells[bucket_key].append(key)

    fn near(self, position: (Float64, Float64, Float64)) -> list[tuple[Int, Int]]:
        var results = []
        var base_key = self.key_for_position(position)
        var offset_z = -1
        while offset_z <= 1:
            var offset_y = -1
            while offset_y <= 1:
                var offset_x = -1
                while offset_x <= 1:
                    var candidate_key = (base_key[0] + offset_x, base_key[1] + offset_y, base_key[2] + offset_z)
                    if self.cells.contains(candidate_key):
                        var bucket = self.cells[candidate_key]
                        for pair in bucket: results.append(pair)
                    offset_x = offset_x + 1
                offset_y = offset_y + 1
            offset_z = offset_z + 1
        return results

struct ProximityEngine:
    # cooldown map per region name
    var last_attempt_step: dict[String, dict[tuple[Int, Int], Int64]]

    fn init(mut self):
        self.last_attempt_step = dict[String, dict[tuple[Int, Int], Int64]]()

    fn apply(mut self, region: any, config: ProximityConfig) -> Int:
        if not config.proximity_connect_enabled:
            return 0
        var region_name = region.get_name()
        var current_step: Int64 = 0
        current_step = region.get_bus().get_current_step()
        if (current_step < config.development_window_start) or (current_step > config.development_window_end):
            return 0
        if config.proximity_radius <= 0.0:
            return 0

        var candidate_indices = []
        if config.candidate_layers.len > 0:
            candidate_indices = config.candidate_layers
        else:
            var index_value = 0
            var layers_list = region.get_layers()
            while index_value < layers_list.len:
                candidate_indices.append(index_value)
                index_value = index_value + 1

        if candidate_indices.len == 0:
            return 0

        var layout = DeterministicLayout()
        var grid = SpatialHash(config.proximity_radius)
        var layers_ref = region.get_layers()
        for layer_index in candidate_indices:
            var layer_ref = layers_ref[layer_index]
            var height_value = 0
            var width_value = 0
            if hasattr(layer_ref, "height"): height_value = layer_ref.height
            if hasattr(layer_ref, "width"): width_value = layer_ref.width
            var neuron_list = layer_ref.get_neurons()
            var neuron_index = 0
            while neuron_index < neuron_list.len:
                var pos = layout.position(region_name, layer_index, neuron_index, height_value, width_value)
                grid.insert((layer_index, neuron_index), pos)
                neuron_index = neuron_index + 1

        # STEP only unless RNG is added to Region
        var added = 0
        if not self.last_attempt_step.contains(region_name):
            self.last_attempt_step[region_name] = dict[tuple[Int, Int], Int64]()
        var cooldown_map = self.last_attempt_step[region_name]

        for layer_index_apply in candidate_indices:
            var layer_apply = layers_ref[layer_index_apply]
            var height_apply = 0
            var width_apply = 0
            if hasattr(layer_apply, "height"): height_apply = layer_apply.height
            if hasattr(layer_apply, "width"): width_apply = layer_apply.width
            var neuron_list_apply = layer_apply.get_neurons()
            var neuron_index_apply = 0
            while neuron_index_apply < neuron_list_apply.len:
                var last = cooldown_map[(layer_index_apply, neuron_index_apply)] if cooldown_map.contains((layer_index_apply, neuron_index_apply)) else -1000000000
                if (current_step - last) < config.proximity_cooldown_ticks:
                    neuron_index_apply = neuron_index_apply + 1
                    continue
                var origin_pos = layout.position(region_name, layer_index_apply, neuron_index_apply, height_apply, width_apply)
                var neighbors = grid.near(origin_pos)
                for pair_key in neighbors:
                    var neighbor_layer = pair_key[0]
                    var neighbor_neuron = pair_key[1]
                    if neighbor_layer == layer_index_apply and neighbor_neuron == neuron_index_apply:
                        continue
                    # Same-layer adjacency only in Mojo (cross-layer requires broader wiring API)
                    if neighbor_layer != layer_index_apply:
                        continue
                    var target_layer = layers_ref[neighbor_layer]
                    var neighbor_pos = layout.position(region_name, neighbor_layer, neighbor_neuron,
                                                       (target_layer.height if hasattr(target_layer, "height") else 0),
                                                       (target_layer.width if hasattr(target_layer, "width") else 0))
                    var offset_x = origin_pos[0] - neighbor_pos[0]
                    var offset_y = origin_pos[1] - neighbor_pos[1]
                    var offset_z = origin_pos[2] - neighbor_pos[2]
                    var distance_value = sqrt(offset_x * offset_x + offset_y * offset_y + offset_z * offset_z)
                    if distance_value > config.proximity_radius:
                        continue
                    # STEP only (no RNG in current Region)
                    if config.proximity_function != "STEP":
                        raise Error("ProximityEngine: probabilistic modes require a seeded RNG; use STEP in Mojo policy")
                    # Connect directed edge within the same layer
                    layers_ref[layer_index_apply].get_neurons()[neuron_index_apply].connect(neighbor_neuron, False)
                    cooldown_map[(layer_index_apply, neuron_index_apply)] = current_step
                    cooldown_map[(neighbor_layer, neighbor_neuron)] = current_step
                    added = added + 1
                    if added >= config.proximity_max_edges_per_tick:
                        return added
                neuron_index_apply = neuron_index_apply + 1
        return added

