from region import Region
from policy.proximity_connectivity import ProximityConfig, ProximityEngine

fn check(cond: Bool, msg: String):
    if not cond: raise Error("Test failed: " + msg)

fn test_proximity_step_budget_cooldown():
    var region = Region("prox-step")
    var l = region.add_layer(9, 0, 0)
    var cfg = ProximityConfig()
    cfg.proximity_connect_enabled = True
    cfg.proximity_function = "STEP"
    cfg.proximity_radius = 1.25
    cfg.proximity_max_edges_per_tick = 5
    cfg.proximity_cooldown_ticks = 100
    var added = ProximityEngine().apply(region, cfg)
    check(added >= 0 and added <= 5, "added within budget")
    var second = ProximityEngine().apply(region, cfg)
    check(second == 0, "cooldown prevents repeat")

fn main():
    test_proximity_step_budget_cooldown()
    print("[MOJO] proximity_step passed.")

