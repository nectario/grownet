from layer import Layer


def test_scalar_neuron_growth_on_fallback_strict_capacity():
    """At capacity + consecutive fallbacks >= threshold triggers neuron growth (scalar path)."""
    # Single layer with a small excitatory population; we will observe growth in-place.
    layer = Layer(excitatory_count=2, inhibitory_count=0, modulatory_count=0)
    base_count = len(layer.get_neurons())

    # Configure first neuron aggressively to trigger growth quickly.
    seed = layer.get_neurons()[0]
    seed.slot_limit = 1  # strict capacity: only one slot allowed
    seed.slot_cfg.bin_width_pct = 1.0  # fine bins so new inputs desire new bins
    seed.slot_cfg.growth_enabled = True
    seed.slot_cfg.neuron_growth_enabled = True
    seed.slot_cfg.fallback_growth_threshold = 2  # two consecutive fallbacks
    seed.slot_cfg.neuron_growth_cooldown_ticks = 0  # allow immediate growth

    # First input: sets FIRST anchor and allocates the initial slot
    seed.on_input(1.0)
    # Subsequent inputs: desire new bins, but at capacity → fallback marked by engine
    seed.on_input(1.02)
    seed.on_input(1.04)

    # Growth may be executed on the third call; assert layer grew
    assert len(layer.get_neurons()) > base_count

