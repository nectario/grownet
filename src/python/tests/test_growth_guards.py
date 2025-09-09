import pytest
from neuron import Neuron
import pytest
from neuron import Neuron
from slot_config import SlotConfig


def make_neuron_at_capacity(cfg: SlotConfig | None = None) -> Neuron:
    n = Neuron("n1")
    if cfg is not None:
        n.slot_cfg = cfg
    n.slot_limit = 1
    n.slots = {0: object()}
    return n


def test_defaults_preserve_behaviour():
    cfg = SlotConfig()
    n = make_neuron_at_capacity(cfg)
    for _ in range(3):
        n.last_slot_used_fallback = True
        n.last_max_axis_delta_pct = 10.0
        n.last_missing_slot_id = 1
        n.maybe_request_neuron_growth()
    assert n.fallback_streak == 3


def test_same_missing_slot_guard_blocks_alternation():
    cfg = SlotConfig()
    cfg.fallback_growth_requires_same_missing_slot = True
    n = make_neuron_at_capacity()
    n.slot_cfg = cfg
    ids = [1, 2, 1, 2, 1, 2]
    for sid in ids:
        n.last_slot_used_fallback = True
        n.last_missing_slot_id = sid
        n.last_max_axis_delta_pct = 90.0
        n.maybe_request_neuron_growth()
    assert n.fallback_streak <= 1


def test_min_delta_gate_blocks_small_deltas():
    cfg = SlotConfig()
    cfg.min_delta_pct_for_growth = 70.0
    n = make_neuron_at_capacity()
    n.slot_cfg = cfg
    for _ in range(3):
        n.last_slot_used_fallback = True
        n.last_max_axis_delta_pct = 60.0
        n.last_missing_slot_id = 3
        n.maybe_request_neuron_growth()
    assert n.fallback_streak == 0
    for _ in range(3):
        n.last_slot_used_fallback = True
        n.last_max_axis_delta_pct = 80.0
        n.last_missing_slot_id = 3
        n.maybe_request_neuron_growth()
    assert n.fallback_streak == 3
