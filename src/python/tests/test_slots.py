from src.python.neuron_excitatory import ExcitatoryNeuron
from src.python.lateral_bus import LateralBus

def test_slot_assignment_sequence():
    neuron = ExcitatoryNeuron("n1", LateralBus())
    neuron.fixed_step_percent = 10.0
    neuron.on_input(10.0)   # first -> slot 0
    assert 0 in neuron.slots
    neuron.on_input(11.0)   # +10% -> near 10% bin (id 2 with our scheme)
    neuron.on_input(11.2)   # small delta -> same or adjacent slot depending on step
    assert len(neuron.slots) >= 2
