from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Any, List, Optional, TypeVar, Generic


@dataclass
class ParallelOptions:
    max_workers: Optional[int] = None
    tile_size: int = 4096
    reduction_mode: str = "ordered"   # "ordered" | "pairwise_tree"
    device: str = "cpu"               # "cpu" | "gpu" | "auto"
    vectorization_enabled: bool = True


_GLOBAL_OPTIONS = ParallelOptions()


def configure(options: ParallelOptions) -> None:
    global _GLOBAL_OPTIONS
    _GLOBAL_OPTIONS = options


T = TypeVar("T")
R = TypeVar("R")


def parallel_for(domain: Iterable[T], kernel: Callable[[T], None], options: Optional[ParallelOptions] = None) -> None:
    # Sequential fallback; deterministic by construction.
    _ = options or _GLOBAL_OPTIONS
    for item in domain:
        kernel(item)


def parallel_map(domain: Iterable[T], kernel: Callable[[T], R], reduce_in_order: Callable[[List[R]], R], options: Optional[ParallelOptions] = None) -> R:
    # Sequential fallback; collect in a stable order and reduce deterministically.
    _ = options or _GLOBAL_OPTIONS
    local_results: List[R] = []
    for item in domain:
        local_results.append(kernel(item))
    return reduce_in_order(local_results)


def _rotl64(x: int, r: int) -> int:
    return ((x << r) & 0xFFFFFFFFFFFFFFFF) | (x >> (64 - r))


def _mix64(x: int) -> int:
    # SplitMix64 mix function
    x = (x + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
    z = x
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9 & 0xFFFFFFFFFFFFFFFF
    z = (z ^ (z >> 27)) * 0x94D049BB133111EB & 0xFFFFFFFFFFFFFFFF
    z = z ^ (z >> 31)
    return z & 0xFFFFFFFFFFFFFFFF


def counter_rng(seed: int, step: int, draw_kind: int, layer_index: int, unit_index: int, draw_index: int) -> float:
    # Counter-based deterministic RNG using SplitMix64-style mixing of a composed counter.
    # Compose a 64-bit key from inputs in a stable way.
    key = (seed & 0xFFFFFFFFFFFFFFFF)
    for v in (step, draw_kind, layer_index, unit_index, draw_index):
        key = _mix64((key ^ (v & 0xFFFFFFFFFFFFFFFF)) & 0xFFFFFFFFFFFFFFFF)
    # Convert to double in [0,1)
    mantissa = (key >> 11) & ((1 << 53) - 1)
    return mantissa / float(1 << 53)

