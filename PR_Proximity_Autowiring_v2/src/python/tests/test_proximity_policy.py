# File: src/python/tests/test_proximity_policy.py
# NOTE: ADAPT Region construction and method names to your tree.

import pytest

from policy.proximity_connectivity import (
    ProximityConfig,
    ProximityEngine,
    DeterministicLayout,
)

def test_proximity_disabled_no_edges(region_factory):
    region = region_factory()  # ADAPT: fixture that returns a region with one small 2D layer
    config = ProximityConfig(proximity_connect_enabled=False)
    edges_added = ProximityEngine.apply(region, config)
    assert edges_added == 0

def test_probabilistic_without_rng_raises(region_factory):
    region = region_factory(seed=None)   # ADAPT: ensure region.rng is None
    config = ProximityConfig(
        proximity_connect_enabled=True,
        proximity_radius=1.5,
        proximity_function="LOGISTIC"
    )
    with pytest.raises(RuntimeError):
        ProximityEngine.apply(region, config)

def test_budget_respected(region_factory):
    region = region_factory(seed=1234)   # ADAPT: ensure deterministic RNG
    # Construct a small dense layer to guarantee candidates within radius.
    config = ProximityConfig(
        proximity_connect_enabled=True,
        proximity_radius=2.0,
        proximity_function="STEP",
        proximity_max_edges_per_tick=3,
        proximity_cooldown_ticks=0
    )
    edges_added = ProximityEngine.apply(region, config)
    assert edges_added <= config.proximity_max_edges_per_tick

def test_directionality(region_factory, two_neuron_layer_setup):
    region, neuron_a, neuron_b, layer_index = two_neuron_layer_setup(seed=1234)  # ADAPT helper
    config = ProximityConfig(
        proximity_connect_enabled=True,
        proximity_radius=10.0,
        proximity_function="STEP",
        proximity_max_edges_per_tick=1,
        proximity_cooldown_ticks=0
    )
    # First pass: expect one directed edge based on iteration order
    edges_added = ProximityEngine.apply(region, config)
    assert edges_added == 1
    # Second pass: allow the reverse edge (depending on iteration and budget)
    edges_added_second = ProximityEngine.apply(region, config)
    assert edges_added_second in (0, 1)
