# File: src/python/policy/proximity_connectivity.py
# Purpose: Optional proximity autowiring policy (deterministic) for GrowNet.
# Notes: No leading underscores in public names. Descriptive identifiers only.
from dataclasses import dataclass
from math import floor, exp
from typing import Dict, Tuple, Iterable, Optional, List, Any

@dataclass
class ProximityConfig:
    proximity_connect_enabled: bool = False
    proximity_radius: float = 1.0
    proximity_function: str = "STEP"      # "STEP" | "LINEAR" | "LOGISTIC"
    linear_exponent_gamma: float = 1.0
    logistic_steepness_k: float = 4.0
    proximity_max_edges_per_tick: int = 128
    proximity_cooldown_ticks: int = 5
    development_window_start: int = 0
    development_window_end: int = 2**63 - 1
    stabilization_hits: int = 3
    decay_if_unused: bool = True
    decay_half_life_ticks: int = 200
    candidate_layers: Tuple[int, ...] = tuple()
    record_mesh_rules_on_cross_layer: bool = True

class DeterministicLayout:
    layer_spacing = 4.0
    grid_spacing = 1.2

    @staticmethod
    def position(region_name: str, layer_index: int, neuron_index: int,
                 layer_height: int = 0, layer_width: int = 0) -> Tuple[float, float, float]:
        if layer_height > 0 and layer_width > 0:
            row_index, col_index = divmod(neuron_index, layer_width)
            x_coord = (col_index - (layer_width - 1) / 2.0) * DeterministicLayout.grid_spacing
            y_coord = ((layer_height - 1) / 2.0 - row_index) * DeterministicLayout.grid_spacing
            z_coord = float(layer_index) * DeterministicLayout.layer_spacing
            return (x_coord, y_coord, z_coord)
        # Fallback grid for non‑2D layers (ceil‑sqrt layout)
        grid_side = int((neuron_index + 1) ** 0.5)
        if grid_side * grid_side < neuron_index + 1:
            grid_side += 1
        row_index = neuron_index // grid_side
        col_index = neuron_index % grid_side
        x_coord = (col_index - (grid_side - 1) / 2.0) * DeterministicLayout.grid_spacing
        y_coord = ((grid_side - 1) / 2.0 - row_index) * DeterministicLayout.grid_spacing
        z_coord = float(layer_index) * DeterministicLayout.layer_spacing
        return (x_coord, y_coord, z_coord)

class SpatialHash:
    def __init__(self, cell_size: float):
        self.cell_size = cell_size
        self.cells: Dict[Tuple[int, int, int], list] = {}

    def key_for_position(self, position: Tuple[float, float, float]) -> Tuple[int, int, int]:
        return (floor(position[0] / self.cell_size),
                floor(position[1] / self.cell_size),
                floor(position[2] / self.cell_size))

    def insert(self, item_key, position: Tuple[float, float, float]) -> None:
        hash_key = self.key_for_position(position)
        self.cells.setdefault(hash_key, []).append(item_key)

    def near(self, position: Tuple[float, float, float], radius: float) -> Iterable:
        base = self.key_for_position(position)
        for offset_z in (-1, 0, 1):
            for offset_y in (-1, 0, 1):
                for offset_x in (-1, 0, 1):
                    neighbor_key = (base[0] + offset_x, base[1] + offset_y, base[2] + offset_z)
                    if neighbor_key in self.cells:
                        for item_key in self.cells[neighbor_key]:
                            yield item_key

class ProximityEngine:
    # Transient, non‑core state by region key (cooldowns, etc.).
    region_state: Dict[str, Dict] = {}

    @staticmethod
    def region_key(region: Any) -> str:
        return getattr(region, "name", f"region_{id(region)}")

    @staticmethod
    def neuron_global_id(layer_index: int, neuron_index: int) -> Tuple[int, int]:
        return (layer_index, neuron_index)

    @staticmethod
    def euclidean_distance(a_position: Tuple[float, float, float],
                           b_position: Tuple[float, float, float]) -> float:
        delta_x = a_position[0] - b_position[0]
        delta_y = a_position[1] - b_position[1]
        delta_z = a_position[2] - b_position[2]
        return (delta_x * delta_x + delta_y * delta_y + delta_z * delta_z) ** 0.5

    @staticmethod
    def probability_from_distance(distance_value: float, config: ProximityConfig) -> float:
        if config.proximity_function == "STEP":
            return 1.0 if distance_value <= config.proximity_radius else 0.0
        unit_value = max(0.0, 1.0 - distance_value / max(config.proximity_radius, 1e-12))
        if config.proximity_function == "LINEAR":
            return unit_value ** max(config.linear_exponent_gamma, 1e-12)
        # LOGISTIC
        return 1.0 / (1.0 + exp(config.logistic_steepness_k * (distance_value - config.proximity_radius)))

    @staticmethod
    def apply(region: Any, config: ProximityConfig) -> int:
        if not config.proximity_connect_enabled:
            return 0

        current_step = region.bus.get_current_step() if hasattr(region.bus, "get_current_step") else getattr(region.bus, "current_step", 0)
        if current_step < config.development_window_start or current_step > config.development_window_end:
            return 0

        region_key_value = ProximityEngine.region_key(region)
        state = ProximityEngine.region_state.setdefault(region_key_value, {"last_attempt_step": {}})

        grid = SpatialHash(config.proximity_radius)
        candidate_layers = list(config.candidate_layers) if config.candidate_layers else list(range(len(region.layers)))

        for layer_index in candidate_layers:
            layer = region.layers[layer_index]
            height = getattr(layer, "height", 0)
            width = getattr(layer, "width", 0)
            neuron_list = layer.get_neurons()
            for neuron_index in range(len(neuron_list)):
                position = DeterministicLayout.position(region_key_value, layer_index, neuron_index, height, width)
                grid.insert((layer_index, neuron_index), position)

        region_random = getattr(region, "rng", None)

        def draw_bernoulli(probability_value: float) -> bool:
            if probability_value <= 0.0:
                return False
            if probability_value >= 1.0:
                return True
            # Determinism requirement: a seeded Region RNG must be present for probabilistic modes.
            if region_random is None:
                raise RuntimeError("ProximityEngine: probabilistic proximity_function requires a seeded region RNG.")
            return region_random.random() < probability_value

        edges_added = 0

        for layer_index in candidate_layers:
            layer = region.layers[layer_index]
            height = getattr(layer, "height", 0)
            width = getattr(layer, "width", 0)
            neuron_list = layer.get_neurons()
            for neuron_index in range(len(neuron_list)):
                global_id = ProximityEngine.neuron_global_id(layer_index, neuron_index)
                last_step = state["last_attempt_step"].get(global_id, -10**9)
                if (current_step - last_step) < config.proximity_cooldown_ticks:
                    continue
                origin_position = DeterministicLayout.position(region_key_value, layer_index, neuron_index, height, width)
                for neighbor_layer_index, neighbor_neuron_index in grid.near(origin_position, config.proximity_radius):
                    if neighbor_layer_index == layer_index and neighbor_neuron_index == neuron_index:
                        continue
                    if ProximityEngine.already_connected(region, layer_index, neuron_index, neighbor_layer_index, neighbor_neuron_index):
                        continue
                    neighbor_layer = region.layers[neighbor_layer_index]
                    neighbor_height = getattr(neighbor_layer, "height", 0)
                    neighbor_width = getattr(neighbor_layer, "width", 0)
                    neighbor_position = DeterministicLayout.position(region_key_value, neighbor_layer_index, neighbor_neuron_index, neighbor_height, neighbor_width)
                    distance_value = ProximityEngine.euclidean_distance(origin_position, neighbor_position)
                    if distance_value > config.proximity_radius:
                        continue
                    probability_value = ProximityEngine.probability_from_distance(distance_value, config)
                    if draw_bernoulli(probability_value):
                        ProximityEngine.connect_neurons(region, layer_index, neuron_index, neighbor_layer_index, neighbor_neuron_index, config.record_mesh_rules_on_cross_layer)
                        state["last_attempt_step"][global_id] = current_step
                        state["last_attempt_step"][ProximityEngine.neuron_global_id(neighbor_layer_index, neighbor_neuron_index)] = current_step
                        edges_added += 1
                        if edges_added >= config.proximity_max_edges_per_tick:
                            return edges_added
        return edges_added

    @staticmethod
    def already_connected(region: Any, src_layer_index: int, src_neuron_index: int,
                          dst_layer_index: int, dst_neuron_index: int) -> bool:
        # Preferred canonical query (ADAPT if available in your repo):
        if hasattr(region, "has_edge"):
            return region.has_edge(src_layer_index, src_neuron_index, dst_layer_index, dst_neuron_index)
        # Fallback: scan outgoing synapses (ensure the Synapse API provides target layer/index access).
        source_neuron = region.layers[src_layer_index].get_neurons()[src_neuron_index]
        for synapse in source_neuron.get_outgoing():
            has_same_target_index = (synapse.get_target_index() == dst_neuron_index) if hasattr(synapse, "get_target_index") else False
            has_same_layer_index = False
            if hasattr(synapse, "get_target_layer_index"):
                has_same_layer_index = (synapse.get_target_layer_index() == dst_layer_index)
            elif hasattr(synapse, "target_layer"):
                has_same_layer_index = (getattr(synapse, "target_layer") == dst_layer_index)
            else:
                # If the layer is not encoded on Synapse, assume single-destination-layer per list (best-effort fallback).
                has_same_layer_index = True
            if has_same_target_index and has_same_layer_index:
                return True
        return False

    @staticmethod
    def connect_neurons(region: Any, src_layer_index: int, src_neuron_index: int,
                        dst_layer_index: int, dst_neuron_index: int, record_mesh_rule: bool) -> None:
        # Preferred canonical creation (ADAPT to your repo):
        if hasattr(region, "connect_neurons"):
            region.connect_neurons(src_layer_index, src_neuron_index, dst_layer_index, dst_neuron_index, feedback=False)
        else:
            source_neuron = region.layers[src_layer_index].get_neurons()[src_neuron_index]
            if hasattr(region, "create_synapse"):
                new_synapse = region.create_synapse(dst_layer_index, dst_neuron_index, feedback=False)
            else:
                # ADAPT import: replace with your Synapse class path.
                try:
                    from src.python.synapse import Synapse
                    new_synapse = Synapse(dst_neuron_index, False)
                    setattr(new_synapse, "target_layer", dst_layer_index)
                except Exception as import_error:
                    raise RuntimeError("Please adapt connect_neurons() to your Synapse API") from import_error
            source_neuron.get_outgoing().append(new_synapse)

        if record_mesh_rule and src_layer_index != dst_layer_index and hasattr(region, "record_mesh_rule_for"):
            region.record_mesh_rule_for(src_layer_index, dst_layer_index, probability=1.0, feedback=False)
