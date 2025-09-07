import pytest


def test_proximity_policy_disabled_returns_zero():
    from region import Region
    from policy.proximity_connectivity import ProximityConfig, ProximityEngine
    region = Region("prox-disabled")
    layer_index = region.add_layer(4, 0, 0)
    config = ProximityConfig(proximity_connect_enabled=False)
    added = ProximityEngine.apply(region, config)
    assert added == 0


def test_proximity_policy_budget_respected_step_mode():
    from region import Region
    from policy.proximity_connectivity import ProximityConfig, ProximityEngine
    region = Region("prox-budget")
    layer_index = region.add_layer(9, 0, 0)
    # Enable deterministic STEP mode with a radius that links adjacent grid neighbors
    config = ProximityConfig(
        proximity_connect_enabled=True,
        proximity_function="STEP",
        proximity_radius=1.25,
        proximity_max_edges_per_tick=5,
        proximity_cooldown_ticks=0,
        candidate_layers=(layer_index,),
    )
    # No RNG required in STEP mode
    added_first = ProximityEngine.apply(region, config)
    assert added_first == 5
    # Second pass should also add up to budget again (new edges), or saturate earlier
    added_second = ProximityEngine.apply(region, config)
    assert 0 <= added_second <= 5

