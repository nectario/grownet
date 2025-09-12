from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, List, Tuple


@dataclass
class IndexDomain(Iterable[int]):
    count: int

    def __iter__(self) -> Iterator[int]:
        # Stable, deterministic order [0..count)
        return iter(range(int(self.count)))


def build_layer_neuron_tiles(neuron_counts: List[int], tile_size: int) -> List[Tuple[int, int, int]]:
    """Return a stable list of tiles (layer_index, start, end) covering all neurons.

    Each tile denotes a half-open interval [start, end) within that layer's neuron list.
    The enumeration is lexicographic in (layer_index, start).
    """
    tiles: List[Tuple[int, int, int]] = []
    for layer_index, total_neurons in enumerate(neuron_counts):
        start_index = 0
        while start_index < int(total_neurons):
            end_index = min(int(total_neurons), start_index + int(tile_size))
            tiles.append((layer_index, start_index, end_index))
            start_index = end_index
    return tiles

