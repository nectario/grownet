from region import Region


def mk_region_for_growth():
    r = Region("growth")
    lin = r.add_input_layer_2d(4, 4, gain=1.0, epsilon_fire=0.01)
    lhid = r.add_layer(excitatory_count=4, inhibitory_count=0, modulatory_count=0)
    r.connect_layers_windowed(lin, lhid, kernel_h=2, kernel_w=2, stride_h=2, stride_w=2, padding="valid")
    r.bind_input("img", [lin])
    # Enable spatial slotting + aggressive growth on hidden neurons
    layer = r.get_layers()[lhid]
    for neuron in layer.get_neurons():
        neuron.slot_cfg.spatial_enabled = True
        neuron.slot_cfg.row_bin_width_pct = 10.0
        neuron.slot_cfg.col_bin_width_pct = 10.0
        neuron.slot_cfg.growth_enabled = True
        neuron.slot_cfg.neuron_growth_enabled = True
        neuron.slot_cfg.fallback_growth_threshold = 1  # grow fast for test
        neuron.slot_limit = 1  # force fallback immediately
    return r, lin, lhid


def test_neuron_growth_on_fallback():
    r, lin, lhid = mk_region_for_growth()
    layer = r.get_layers()[lhid]
    base_count = len(layer.get_neurons())
    # drive a dot that keeps landing in novel bins so fallback triggers
    frames = [
        [[0, 1, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        [[0, 0, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        [[0, 0, 0, 1], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
    ]
    for f in frames:
        r.tick_2d("img", f)
    assert len(layer.get_neurons()) > base_count


def test_autowire_inbound_mesh_and_tracts_do_not_crash():
    # light smoke: add downstream layer via mesh so rules exist; ensure growth path wires without exceptions
    r, lin, lhid = mk_region_for_growth()
    lout = r.add_layer(excitatory_count=3, inhibitory_count=0, modulatory_count=0)
    r.connect_layers(lhid, lout, probability=0.5, feedback=False)
    # trigger growth
    r.tick_2d("img", [[0, 1, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
    r.tick_2d("img", [[0, 0, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
    # If we reach here without error, auto-wiring paths executed safely.
    assert True
