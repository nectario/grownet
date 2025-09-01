import pytest
from region import Region


def _get_first_neuron(region: Region, layer_index: int):
    """Helper to read the first neuron of a layer."""
    return region.get_layers()[layer_index].get_neurons()[0]


def _last_slot_of(neuron):
    """
    Robustly fetch the most recently used slot object.
    Falls back to any slot if the convenience pointer is absent.
    """
    slot = getattr(neuron, "_last_slot", None)
    if slot is not None:
        return slot
    # Fallback (shouldn't be needed if PR for frozen slots is applied):
    slots_map = getattr(neuron, "slots", {})
    assert isinstance(slots_map, dict) and slots_map, "Neuron has no slots yet"
    return next(iter(slots_map.values()))


def test_frozen_slot_scalar_stops_adaptation_and_unfreeze_resumes():
    """
    Drive a scalar edge into a 1-neuron hidden layer.
    - After the first tick we freeze the last-selected slot.
    - While frozen, reinforcement and theta must NOT change.
    - After unfreezing, reinforcement resumes (strength increases).
    """
    r = Region("frozen_scalar")
    h = r.add_layer(excitatory_count=1, inhibitory_count=0, modulatory_count=0)
    r.bind_input("x", [h])

    # First tick establishes FIRST anchor + picks/creates a slot.
    r.tick("x", 0.6)
    n = _get_first_neuron(r, h)
    s = _last_slot_of(n)

    # Record baseline before freezing.
    strength0 = float(s.strength)
    theta0 = float(s.theta)

    # Freeze and tick again (values would normally adapt).
    assert n.freeze_last_slot() is True
    r.tick("x", 0.9)

    # While frozen: no reinforcement, no theta drift.
    assert float(s.strength) == pytest.approx(strength0)
    assert float(s.theta) == pytest.approx(theta0)

    # Unfreeze and tick again — strength should now grow by the step (~0.02).
    assert n.unfreeze_last_slot() is True
    r.tick("x", 0.8)
    assert float(s.strength) > strength0  # adaptation resumed


def test_frozen_slot_spatial_2d_stops_adaptation_and_unfreeze_resumes():
    """
    Same idea as the scalar test, but through the spatial (row,col) path.
    We enable spatial slotting on a single hidden neuron and deliver the
    same pixel twice while frozen — strength/theta must not change.
    """
    r = Region("frozen_2d")
    lin = r.add_input_layer_2d(3, 3, gain=1.0, epsilon_fire=0.01)
    hid = r.add_layer(excitatory_count=1, inhibitory_count=0, modulatory_count=0)

    # Enable spatial slotting on the destination neuron.
    n = _get_first_neuron(r, hid)
    n.slot_cfg.spatial_enabled = True
    n.slot_cfg.row_bin_width_pct = 100.0
    n.slot_cfg.col_bin_width_pct = 100.0

    # Deterministic 2D wiring and bind input.
    r.connect_layers_windowed(lin, hid, kernel_h=3, kernel_w=3, stride_h=3, stride_w=3, padding="valid")
    r.bind_input("img", [lin])

    # Drive a single bright pixel at the same location to hit the same spatial bin.
    frame = [[0.0 for _ in range(3)] for _ in range(3)]
    frame[1][1] = 1.0

    r.tick_2d("img", frame)  # establish spatial slot
    s = _last_slot_of(n)
    strength0 = float(s.strength)
    theta0 = float(s.theta)

    # Freeze -> tick (same pixel) -> no changes.
    assert n.freeze_last_slot() is True
    r.tick_2d("img", frame)
    assert float(s.strength) == pytest.approx(strength0)
    assert float(s.theta) == pytest.approx(theta0)

    # Unfreeze -> tick (same pixel) -> reinforcement resumes.
    assert n.unfreeze_last_slot() is True
    r.tick_2d("img", frame)
    assert float(s.strength) > strength0
