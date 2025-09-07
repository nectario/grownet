from __future__ import annotations

from dataclasses import dataclass
from math import floor, sqrt, exp
from typing import Dict, Tuple, Iterable, List, Optional, Any


@dataclass
class ProximityConfig:
    proximity_connect_enabled: bool = False
    proximity_radius: float = 1.0
    proximity_function: str = "STEP"  # STEP | LINEAR | LOGISTIC
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
    layer_spacing: float = 4.0
    grid_spacing: float = 1.2

    @staticmethod
    def position(region_name: str, layer_index: int, neuron_index: int,
                 layer_height: int = 0, layer_width: int = 0) -> Tuple[float, float, float]:
        if layer_height > 0 and layer_width > 0:
            row_index, col_index = divmod(int(neuron_index), int(layer_width))
            offset_x = (col_index - (layer_width - 1) / 2.0) * DeterministicLayout.grid_spacing
            offset_y = ((layer_height - 1) / 2.0 - row_index) * DeterministicLayout.grid_spacing
            offset_z = float(layer_index) * DeterministicLayout.layer_spacing
            return (offset_x, offset_y, offset_z)

        # Non-2D: arrange on a ceil-sqrt grid centered around (0,0)
        grid_side = int((int(neuron_index) + 1) ** 0.5)
        if grid_side * grid_side < int(neuron_index) + 1:
            grid_side += 1
        row_index = int(neuron_index) // grid_side
        col_index = int(neuron_index) % grid_side
        offset_x = (col_index - (grid_side - 1) / 2.0) * DeterministicLayout.grid_spacing
        offset_y = ((grid_side - 1) / 2.0 - row_index) * DeterministicLayout.grid_spacing
        offset_z = float(layer_index) * DeterministicLayout.layer_spacing
        return (offset_x, offset_y, offset_z)


class SpatialHash:
    def __init__(self, cell_size: float):
        if float(cell_size) <= 0.0:
            raise ValueError("cell_size must be > 0")
        self.cell_size = float(cell_size)
        self.cells: Dict[Tuple[int, int, int], List[Tuple[int, int]]] = {}

    def key_for_position(self, position: Tuple[float, float, float]) -> Tuple[int, int, int]:
        cell_x = int(floor(position[0] / self.cell_size))
        cell_y = int(floor(position[1] / self.cell_size))
        cell_z = int(floor(position[2] / self.cell_size))
        return (cell_x, cell_y, cell_z)

    def insert(self, item_key: Tuple[int, int], position: Tuple[float, float, float]) -> None:
        key = self.key_for_position(position)
        self.cells.setdefault(key, []).append(item_key)

    def near(self, position: Tuple[float, float, float]) -> Iterable[Tuple[int, int]]:
        base_key = self.key_for_position(position)
        for offset_z in (-1, 0, 1):
            for offset_y in (-1, 0, 1):
                for offset_x in (-1, 0, 1):
                    neighbor_key = (base_key[0] + offset_x, base_key[1] + offset_y, base_key[2] + offset_z)
                    bucket = self.cells.get(neighbor_key)
                    if bucket:
                        for item in bucket:
                            yield item


class ProximityEngine:
    # Per-region state for cooldown tracking: { region_name: { 'last_attempt_step': {(L,N): step} } }
    region_state: Dict[str, Dict[str, Dict[Tuple[int, int], int]]] = {}

    @staticmethod
    def apply(region: Any, config: ProximityConfig) -> int:
        if not config.proximity_connect_enabled:
            return 0

        # development window
        current_step = 0
        try:
            if region.bus is not None and hasattr(region.bus, "get_current_step"):
                current_step = int(region.bus.get_current_step())
        except Exception:
            current_step = 0
        if current_step < int(config.development_window_start) or current_step > int(config.development_window_end):
            return 0

        # validate radius
        if float(config.proximity_radius) <= 0.0:
            return 0

        # candidate layers (default = all trainable layers)
        try:
            candidate_layers: List[int] = list(config.candidate_layers) if config.candidate_layers else list(range(len(region.layers)))
        except Exception:
            candidate_layers = []
        if not candidate_layers:
            return 0

        # Build spatial hash
        spatial_grid = SpatialHash(config.proximity_radius)
        region_name = getattr(region, "name", f"region_{id(region)}")
        for candidate_layer_index in candidate_layers:
            layer_obj = region.layers[candidate_layer_index]
            layer_height = int(getattr(layer_obj, "height", 0))
            layer_width = int(getattr(layer_obj, "width", 0))
            neuron_list = layer_obj.get_neurons()
            for neuron_index, _neuron_obj in enumerate(neuron_list):
                position = DeterministicLayout.position(region_name, candidate_layer_index, neuron_index, layer_height, layer_width)
                spatial_grid.insert((candidate_layer_index, neuron_index), position)

        # Probability functions
        def probability_from_distance(distance_value: float) -> float:
            if config.proximity_function == "STEP":
                return 1.0 if distance_value <= float(config.proximity_radius) else 0.0
            normalized = max(0.0, 1.0 - distance_value / max(float(config.proximity_radius), 1e-12))
            if config.proximity_function == "LINEAR":
                return normalized ** max(float(config.linear_exponent_gamma), 1e-12)
            # LOGISTIC default
            return 1.0 / (1.0 + exp(float(config.logistic_steepness_k) * (distance_value - float(config.proximity_radius))))

        # deterministic RNG requirement for probabilistic modes (LINEAR, LOGISTIC)
        rng_object = getattr(region, "rng", None)
        if config.proximity_function in ("LINEAR", "LOGISTIC") and rng_object is None:
            raise RuntimeError("ProximityEngine probabilistic mode requires a seeded Region RNG")

        # region-scoped cooldown state
        state = ProximityEngine.region_state.setdefault(region_name, {"last_attempt_step": {}})
        last_attempt_step = state["last_attempt_step"]

        # Helper fallbacks (ADAPT points)
        def get_neuron(layer_index_value: int, neuron_index_value: int) -> Any:
            layer_obj_local = region.layers[layer_index_value]
            return layer_obj_local.get_neurons()[neuron_index_value]

        def has_edge(layer_src_index: int, neuron_src_index: int, layer_dst_index: int, neuron_dst_index: int) -> bool:
            source_neuron_obj = get_neuron(layer_src_index, neuron_src_index)
            try:
                outgoing_list = source_neuron_obj.get_outgoing()
            except Exception:
                outgoing_list = getattr(source_neuron_obj, "outgoing", [])
            target_neuron_obj = get_neuron(layer_dst_index, neuron_dst_index)
            for target_existing in list(outgoing_list):
                if target_existing is target_neuron_obj:
                    return True
            return False

        def connect_neurons(layer_src_index: int, neuron_src_index: int, layer_dst_index: int, neuron_dst_index: int) -> None:
            source_neuron_obj = get_neuron(layer_src_index, neuron_src_index)
            target_neuron_obj = get_neuron(layer_dst_index, neuron_dst_index)
            try:
                source_neuron_obj.connect(target_neuron_obj, feedback=False)  # type: ignore[arg-type]
            except TypeError:
                source_neuron_obj.connect(target_neuron_obj)  # type: ignore[attr-defined]

        def record_mesh_rule_if_needed(layer_src_index: int, layer_dst_index: int) -> None:
            if not bool(config.record_mesh_rules_on_cross_layer):
                return
            if layer_src_index == layer_dst_index:
                return
            try:
                region.mesh_rules.append({'src': int(layer_src_index), 'dst': int(layer_dst_index), 'prob': 1.0, 'feedback': False})
            except Exception:
                # Best-effort only; if Region does not expose mesh_rules, we silently skip.
                pass

        # Main iteration: deterministic order (layer, neuron)
        edges_added_count = 0
        cooldown_ticks = int(config.proximity_cooldown_ticks)
        for candidate_layer_index in candidate_layers:
            layer_obj = region.layers[candidate_layer_index]
            layer_height = int(getattr(layer_obj, "height", 0))
            layer_width = int(getattr(layer_obj, "width", 0))
            neuron_list = layer_obj.get_neurons()
            for neuron_index in range(len(neuron_list)):
                last_step = int(last_attempt_step.get((candidate_layer_index, neuron_index), -10**9))
                if (current_step - last_step) < cooldown_ticks:
                    continue
                # Mark an attempt time even if no edges are added for this source
                last_attempt_step[(candidate_layer_index, neuron_index)] = current_step
                origin_position = DeterministicLayout.position(region_name, candidate_layer_index, neuron_index, layer_height, layer_width)
                for neighbor_layer_index, neighbor_neuron_index in spatial_grid.near(origin_position):
                    if neighbor_layer_index == candidate_layer_index and neighbor_neuron_index == neuron_index:
                        continue
                    if has_edge(candidate_layer_index, neuron_index, neighbor_layer_index, neighbor_neuron_index):
                        continue
                    neighbor_layer_obj = region.layers[neighbor_layer_index]
                    neighbor_position = DeterministicLayout.position(
                        region_name,
                        neighbor_layer_index,
                        neighbor_neuron_index,
                        int(getattr(neighbor_layer_obj, "height", 0)),
                        int(getattr(neighbor_layer_obj, "width", 0)),
                    )
                    offset_x = origin_position[0] - neighbor_position[0]
                    offset_y = origin_position[1] - neighbor_position[1]
                    offset_z = origin_position[2] - neighbor_position[2]
                    euclidean_distance = sqrt(offset_x * offset_x + offset_y * offset_y + offset_z * offset_z)
                    if euclidean_distance > float(config.proximity_radius):
                        continue
                    probability_value = probability_from_distance(euclidean_distance)
                    if probability_value < 1.0:
                        # Deterministic RNG required in probabilistic modes
                        if rng_object.random() >= probability_value:  # type: ignore[attr-defined]
                            continue
                    connect_neurons(candidate_layer_index, neuron_index, neighbor_layer_index, neighbor_neuron_index)
                    record_mesh_rule_if_needed(candidate_layer_index, neighbor_layer_index)
                    last_attempt_step[(neighbor_layer_index, neighbor_neuron_index)] = current_step
                    edges_added_count += 1
                    if edges_added_count >= int(config.proximity_max_edges_per_tick):
                        return edges_added_count

        return edges_added_count
