# Ensure tests can import from src/python without packaging
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).parents[1] / "src" / "python"))

from neuron import ExcitatoryNeuron
from bus import LateralBus

def test_slot_creation_bins_by_percent_delta():
    bus = LateralBus()
    n = ExcitatoryNeuron("N0", bus)

    # First input (10) -> bin 0
    n.on_input(10.0)
    assert len(n.slots) == 1

    # 11 is +10% from 10 -> new bin (1..10%): bin 1
    n.on_input(11.0)
    assert len(n.slots) == 2

    # 11.2 is +1.8% from 11 -> same bin 1
    n.on_input(11.2)
    assert len(n.slots) == 2

def test_connect_and_prune_synapse():
    bus = LateralBus()
    a = ExcitatoryNeuron("A", bus)
    b = ExcitatoryNeuron("B", bus)

    syn = a.connect(b)
    assert len(a.outgoing) == 1

    # Use synapse a few times
    for step in range(5):
        bus.current_step = step
        a.on_input(1.0)

    # Advance time far beyond stale_window -> prune
    bus.current_step += 20_000
    a.prune_synapses(bus.current_step, stale_window=10_000, min_strength=0.9)  # force prune by threshold
    assert len(a.outgoing) == 0

def test_feedback_edge_smoke():
    bus = LateralBus()
    parent = ExcitatoryNeuron("P", bus)
    child = ExcitatoryNeuron("C", bus)
    parent.connect(child)
    child.connect(parent, is_feedback=True)

    for step in range(20):
        bus.current_step = step
        parent.on_input(1.0)

    assert len(parent.slots) >= 1
    assert len(child.slots) >= 1
