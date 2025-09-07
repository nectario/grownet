# File: src/mojo/policy/proximity_connectivity.mojo
# NOTE: ADAPT Region API names to your Mojo tree. Use typed params and snake_case public API.
struct ProximityConfig:
    var proximity_connect_enabled: Bool = False
    var proximity_radius: Float64 = 1.0
    var proximity_function: String = "STEP"   # "STEP" | "LINEAR" | "LOGISTIC"
    var linear_exponent_gamma: Float64 = 1.0
    var logistic_steepness_k: Float64 = 4.0
    var proximity_max_edges_per_tick: Int = 128
    var proximity_cooldown_ticks: Int = 5
    var development_window_start: Int = 0
    var development_window_end: Int = 9_223_372_036_854_775_807  # Long.MAX_VALUE
    var stabilization_hits: Int = 3
    var decay_if_unused: Bool = True
    var decay_half_life_ticks: Int = 200
    var candidate_layers: List[Int] = []
    var record_mesh_rules_on_cross_layer: Bool = True

struct DeterministicLayout:
    static var layer_spacing: Float64 = 4.0
    static var grid_spacing: Float64 = 1.2

    @staticmethod
    fn position(region_name: String, layer_index: Int, neuron_index: Int, layer_height: Int, layer_width: Int) -> (Float64, Float64, Float64):
        if layer_height > 0 and layer_width > 0:
            let row_index = neuron_index / layer_width
            let col_index = neuron_index % layer_width
            let x_coord = (Float64(col_index) - (Float64(layer_width) - 1.0) / 2.0) * DeterministicLayout.grid_spacing
            let y_coord = ((Float64(layer_height) - 1.0) / 2.0 - Float64(row_index)) * DeterministicLayout.grid_spacing
            let z_coord = Float64(layer_index) * DeterministicLayout.layer_spacing
            return (x_coord, y_coord, z_coord)
        # fallback grid
        var grid_side = Int((Float64(neuron_index + 1)) ** 0.5)
        if grid_side * grid_side < neuron_index + 1:
            grid_side = grid_side + 1
        let row_index = neuron_index / grid_side
        let col_index = neuron_index % grid_side
        let x_coord = (Float64(col_index) - (Float64(grid_side) - 1.0) / 2.0) * DeterministicLayout.grid_spacing
        let y_coord = ((Float64(grid_side) - 1.0) / 2.0 - Float64(row_index)) * DeterministicLayout.grid_spacing
        let z_coord = Float64(layer_index) * DeterministicLayout.layer_spacing
        return (x_coord, y_coord, z_coord)

struct SpatialHash:
    var cell_size: Float64
    var cells: Dict[(Int, Int, Int), List[(Int, Int)]]

    fn __init__(in cell_size: Float64):
        self.cell_size = cell_size
        self.cells = Dict[(Int, Int, Int), List[(Int, Int)]]()

    fn key_for_position(self, position: (Float64, Float64, Float64)) -> (Int, Int, Int):
        return (Int(position[0] / self.cell_size), Int(position[1] / self.cell_size), Int(position[2] / self.cell_size))

    fn insert(self, item_key: (Int, Int), position: (Float64, Float64, Float64)):
        let key = self.key_for_position(position)
        if not self.cells.contains(key):
            self.cells[key] = List[(Int, Int)]()
        self.cells[key].append(item_key)

    fn near(self, position: (Float64, Float64, Float64)) -> List[(Int, Int)]:
        let base = self.key_for_position(position)
        var result = List[(Int, Int)]()
        var offset_z = -1
        while offset_z <= 1:
            var offset_y = -1
            while offset_y <= 1:
                var offset_x = -1
                while offset_x <= 1:
                    let neighbor_key = (base.0 + offset_x, base.1 + offset_y, base.2 + offset_z)
                    if self.cells.contains(neighbor_key):
                        let bucket = self.cells[neighbor_key]
                        var idx = 0
                        while idx < bucket.len:
                            result.append(bucket[idx])
                            idx = idx + 1
                    offset_x = offset_x + 1
                offset_y = offset_y + 1
            offset_z = offset_z + 1
        return result

struct ProximityEngine:
    @staticmethod
    fn apply(region: any, config: ProximityConfig) -> Int:
        if not config.proximity_connect_enabled:
            return 0
        let current_step = region.bus.get_current_step()  # ADAPT accessor
        if current_step < config.development_window_start or current_step > config.development_window_end:
            return 0

        var candidate_layers = config.candidate_layers
        if candidate_layers.len == 0:
            let count = region.layer_count()               # ADAPT
            var idx = 0
            while idx < count:
                candidate_layers.append(idx)
                idx = idx + 1

        var grid = SpatialHash(config.proximity_radius)

        var layer_idx = 0
        while layer_idx < candidate_layers.len:
            let layer_index = candidate_layers[layer_idx]
            let layer = region.layer(layer_index)         # ADAPT
            let height = layer.height
            let width = layer.width
            let neuron_count = layer.get_neurons().len    # ADAPT
            var neuron_index = 0
            while neuron_index < neuron_count:
                let pos = DeterministicLayout.position(region.name, layer_index, neuron_index, height, width)
                grid.insert((layer_index, neuron_index), pos)
                neuron_index = neuron_index + 1
            layer_idx = layer_idx + 1

        let probabilistic = config.proximity_function != "STEP"
        if probabilistic and not region.has_rng():        # ADAPT
            raise Error("ProximityEngine: probabilistic mode requires a seeded region RNG")

        var edges_added = 0

        layer_idx = 0
        while layer_idx < candidate_layers.len:
            let layer_index = candidate_layers[layer_idx]
            let layer = region.layer(layer_index)
            let height = layer.height
            let width = layer.width
            let neuron_count = layer.get_neurons().len
            var neuron_index = 0
            while neuron_index < neuron_count:
                let origin = DeterministicLayout.position(region.name, layer_index, neuron_index, height, width)
                let neighbors = grid.near(origin)
                var n_idx = 0
                while n_idx < neighbors.len:
                    let neighbor = neighbors[n_idx]
                    let neighbor_layer_index = neighbor[0]
                    let neighbor_neuron_index = neighbor[1]
                    if neighbor_layer_index == layer_index and neighbor_neuron_index == neuron_index:
                        n_idx = n_idx + 1; continue
                    if region.has_edge(layer_index, neuron_index, neighbor_layer_index, neighbor_neuron_index): # ADAPT
                        n_idx = n_idx + 1; continue
                    let nh_layer = region.layer(neighbor_layer_index)
                    let nh = nh_layer.height
                    let nw = nh_layer.width
                    let neighbor_pos = DeterministicLayout.position(region.name, neighbor_layer_index, neighbor_neuron_index, nh, nw)
                    let dx = origin[0] - neighbor_pos[0]
                    let dy = origin[1] - neighbor_pos[1]
                    let dz = origin[2] - neighbor_pos[2]
                    let distance = (dx*dx + dy*dy + dz*dz) ** 0.5
                    if distance > config.proximity_radius:
                        n_idx = n_idx + 1; continue

                    var probability_value: Float64 = 1.0
                    if config.proximity_function == "STEP":
                        probability_value = 1.0
                    elif config.proximity_function == "LINEAR":
                        let unit = max(0.0, 1.0 - distance / max(config.proximity_radius, 1e-12))
                        probability_value = unit ** max(config.linear_exponent_gamma, 1e-12)
                    else:
                        probability_value = 1.0 / (1.0 + exp(config.logistic_steepness_k * (distance - config.proximity_radius)))

                    var accept = True
                    if config.proximity_function != "STEP":
                        accept = region.rng_next_double() < probability_value  # ADAPT
                    if accept:
                        region.connect_neurons(layer_index, neuron_index, neighbor_layer_index, neighbor_neuron_index, False) # ADAPT
                        if config.record_mesh_rules_on_cross_layer and layer_index != neighbor_layer_index:
                            region.record_mesh_rule_for(layer_index, neighbor_layer_index, 1.0, False) # ADAPT
                        edges_added = edges_added + 1
                        if edges_added >= config.proximity_max_edges_per_tick:
                            return edges_added
                    n_idx = n_idx + 1
                neuron_index = neuron_index + 1
            layer_idx = layer_idx + 1

        return edges_added
