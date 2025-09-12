from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, List
import math


@dataclass
class TopographicConfig:
    kernel_h: int = 7
    kernel_w: int = 7
    stride_h: int = 1
    stride_w: int = 1
    padding: str = "same"
    feedback: bool = False
    weight_mode: str = "gaussian"   # "gaussian" | "dog"
    sigma_center: float = 2.0
    sigma_surround: float = 4.0
    surround_ratio: float = 0.5
    normalize_incoming: bool = True


# Internal registry to expose computed weights without mutating core objects.
# Keyed by (id(region), src_layer_index, dst_layer_index) → {(src_idx, dst_idx): weight}
_TOPO_REGISTRY: Dict[Tuple[int, int, int], Dict[Tuple[int, int], float]] = {}


def _validate_config(cfg: TopographicConfig) -> None:
    if cfg.kernel_h < 1 or cfg.kernel_w < 1:
        raise ValueError("kernel_h and kernel_w must be >= 1")
    if cfg.stride_h < 1 or cfg.stride_w < 1:
        raise ValueError("stride_h and stride_w must be >= 1")
    if str(cfg.padding).lower() not in ("same", "valid"):
        raise ValueError("padding must be 'same' or 'valid'")
    if cfg.sigma_center <= 0.0:
        raise ValueError("sigma_center must be > 0")
    if cfg.weight_mode.lower() == "dog":
        if cfg.sigma_surround <= cfg.sigma_center:
            raise ValueError("sigma_surround must be > sigma_center for DoG mode")
        if cfg.surround_ratio < 0.0:
            raise ValueError("surround_ratio must be >= 0")


def connect_layers_topographic(region, source_layer_index: int, destination_layer_index: int, config: TopographicConfig) -> int:
    """Wrap windowed wiring, compute deterministic distance-based weights, optionally normalize incoming.

    Returns the unique source count from the underlying connect_layers_windowed call.
    Computed weights are stored in a local registry for inspection by demos/tests.
    """
    _validate_config(config)

    # Step 1: build topology using existing helper (center-mapped where applicable)
    unique_sources = region.connect_layers_windowed(
        source_layer_index, destination_layer_index,
        config.kernel_h, config.kernel_w,
        config.stride_h, config.stride_w,
        config.padding, config.feedback,
    )

    src_layer = region.layers[source_layer_index]
    dst_layer = region.layers[destination_layer_index]
    source_height, source_width = int(getattr(src_layer, "height", 0)), int(getattr(src_layer, "width", 0))
    dest_height, dest_width = int(getattr(dst_layer, "height", 0)), int(getattr(dst_layer, "width", 0))
    if source_height <= 0 or source_width <= 0 or dest_height <= 0 or dest_width <= 0:
        raise ValueError("Topographic wiring requires 2D source and destination layers with height/width")

    # Reconstruct center mapping deterministically (mirror Region.connect_layers_windowed rules)
    padding_mode = str(config.padding or "valid").lower()
    origins: List[Tuple[int, int]] = []
    if padding_mode == "same":
        pad_rows = max(0, (config.kernel_h - 1) // 2)
        pad_cols = max(0, (config.kernel_w - 1) // 2)
        row_cursor = -pad_rows
        while row_cursor + config.kernel_h <= source_height + pad_rows + pad_rows:
            col_cursor = -pad_cols
            while col_cursor + config.kernel_w <= source_width + pad_cols + pad_cols:
                origins.append((row_cursor, col_cursor))
                col_cursor += config.stride_w
            row_cursor += config.stride_h
    else:
        row_cursor = 0
        while row_cursor + config.kernel_h <= source_height:
            col_cursor = 0
            while col_cursor + config.kernel_w <= source_width:
                origins.append((row_cursor, col_cursor))
                col_cursor += config.stride_w
            row_cursor += config.stride_h

    # Compute weights (source → center) with dedupe
    weights: Dict[Tuple[int, int], float] = {}
    for (origin_row, origin_col) in origins:
        row_start = max(0, origin_row)
        col_start = max(0, origin_col)
        row_end = min(source_height, origin_row + config.kernel_h)
        col_end = min(source_width, origin_col + config.kernel_w)
        if row_start >= row_end or col_start >= col_end:
            continue
        center_row_index = min(source_height - 1, max(0, origin_row + config.kernel_h // 2))
        center_col_index = min(source_width - 1, max(0, origin_col + config.kernel_w // 2))
        center_index = center_row_index * dest_width + center_col_index
        for src_row_index in range(row_start, row_end):
            for src_col_index in range(col_start, col_end):
                src_index = src_row_index * source_width + src_col_index
                # squared distance
                delta_row = float(src_row_index - center_row_index)
                delta_col = float(src_col_index - center_col_index)
                squared_distance = delta_row * delta_row + delta_col * delta_col
                if config.weight_mode.lower() == "gaussian":
                    weight_value = math.exp(-squared_distance / (2.0 * config.sigma_center * config.sigma_center))
                else:
                    weight_center = math.exp(-squared_distance / (2.0 * config.sigma_center * config.sigma_center))
                    weight_surround = math.exp(-squared_distance / (2.0 * config.sigma_surround * config.sigma_surround))
                    weight_value = max(0.0, weight_center - config.surround_ratio * weight_surround)
                key = (src_index, center_index)
                # dedupe by keeping the first assignment; center mapping ensures one center per window
                if key not in weights:
                    weights[key] = weight_value

    # Optional per-target normalization (incoming to each destination center sums to 1.0)
    if config.normalize_incoming:
        incoming_sums = [0.0] * (dest_height * dest_width)
        for (_, center_index), w_val in weights.items():
            incoming_sums[center_index] += w_val
        for key, weight_val in list(weights.items()):
            center_index = key[1]
            sum_value = incoming_sums[center_index]
            if sum_value > 1e-12:
                weights[key] = weight_val / sum_value

    # Save to registry for inspection
    _TOPO_REGISTRY[(id(region), int(source_layer_index), int(destination_layer_index))] = weights
    return int(unique_sources)


def get_topographic_weights(region, source_layer_index: int, destination_layer_index: int) -> Dict[Tuple[int, int], float]:
    """Retrieve computed weights for a given (region, src, dst) pair (if present)."""
    return _TOPO_REGISTRY.get((id(region), int(source_layer_index), int(destination_layer_index)), {})


def get_incoming_weight_sums(region, destination_layer_index: int, weights: Dict[Tuple[int, int], float]) -> List[float]:
    """Compute per-target incoming sums from a (src,dst)->w mapping (helper for demos/tests)."""
    dst_layer = region.layers[destination_layer_index]
    dest_height, dest_width = int(getattr(dst_layer, "height", 0)), int(getattr(dst_layer, "width", 0))
    totals = [0.0] * max(1, dest_height * dest_width)
    for (_, center_index), w_val in weights.items():
        if 0 <= center_index < len(totals):
            totals[center_index] += float(w_val)
    return totals
