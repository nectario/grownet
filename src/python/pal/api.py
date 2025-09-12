from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, TypeVar, Sequence
import os
from concurrent.futures import ThreadPoolExecutor


T = TypeVar("T")
R = TypeVar("R")


@dataclass
class ParallelOptions:
    max_workers: Optional[int] = None
    tile_size: int = 4096
    reduction_mode: str = "ordered"   # "ordered" | "pairwise_tree" (ordered used)
    device: str = "cpu"               # "cpu" | "gpu" | "auto" (no-op in Python for now)
    vectorization_enabled: bool = True


GLOBAL_OPTIONS = ParallelOptions()


def configure(options: ParallelOptions) -> None:
    global GLOBAL_OPTIONS
    GLOBAL_OPTIONS = options


def _coerce_items(domain: Iterable[T]) -> List[T]:
    return list(domain) if not isinstance(domain, list) else domain  # preserve order


def _resolve_max_workers(options: Optional[ParallelOptions]) -> int:
    if options and options.max_workers:
        return max(1, int(options.max_workers))
    env = os.getenv("GROWNET_PAL_MAX_WORKERS")
    if env:
        try:
            return max(1, int(env))
        except ValueError:
            pass
    return max(1, (os.cpu_count() or 1))


def _resolve_tile_size(options: Optional[ParallelOptions]) -> int:
    tile = (options.tile_size if options else GLOBAL_OPTIONS.tile_size)
    return max(1, int(tile))


def _run_chunk_for(chunk: Sequence[T], kernel: Callable[[T], None]) -> None:
    for item in chunk:
        kernel(item)


def _run_chunk_map(chunk: Sequence[T], kernel: Callable[[T], R]) -> List[R]:
    results: List[R] = []
    for item in chunk:
        results.append(kernel(item))
    return results


def parallel_for(domain: Iterable[T], kernel: Callable[[T], None], options: Optional[ParallelOptions] = None) -> None:
    items = _coerce_items(domain)
    n = len(items)
    if n == 0:
        return
    opts = options or GLOBAL_OPTIONS
    tile = _resolve_tile_size(opts)
    max_workers = _resolve_max_workers(opts)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = []
        for start in range(0, n, tile):
            end = min(n, start + tile)
            futures.append(pool.submit(_run_chunk_for, items[start:end], kernel))
        for f in futures:
            f.result()


def parallel_map(domain: Iterable[T], kernel: Callable[[T], R], reduce_in_order: Callable[[List[R]], R], options: Optional[ParallelOptions] = None) -> R:
    items = _coerce_items(domain)
    n = len(items)
    if n == 0:
        return reduce_in_order([])
    opts = options or GLOBAL_OPTIONS
    tile = _resolve_tile_size(opts)
    max_workers = _resolve_max_workers(opts)

    partials: List[List[R]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = []
        for start in range(0, n, tile):
            end = min(n, start + tile)
            futures.append(pool.submit(_run_chunk_map, items[start:end], kernel))
        for f in futures:
            partials.append(f.result())

    flat: List[R] = []
    for part in partials:
        flat.extend(part)
    return reduce_in_order(flat)


def mix64(x: int) -> int:
    # SplitMix64 mix function
    x = (x + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
    z = x
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9 & 0xFFFFFFFFFFFFFFFF
    z = (z ^ (z >> 27)) * 0x94D049BB133111EB & 0xFFFFFFFFFFFFFFFF
    z = z ^ (z >> 31)
    return z & 0xFFFFFFFFFFFFFFFF


def counter_rng(seed: int, step: int, draw_kind: int, layer_index: int, unit_index: int, draw_index: int) -> float:
    # Counter-based deterministic RNG using SplitMix64-style mixing
    key = (seed & 0xFFFFFFFFFFFFFFFF)
    for v in (step, draw_kind, layer_index, unit_index, draw_index):
        key = mix64((key ^ (v & 0xFFFFFFFFFFFFFFFF)) & 0xFFFFFFFFFFFFFFFF)
    mantissa = (key >> 11) & ((1 << 53) - 1)
    return mantissa / float(1 << 53)
