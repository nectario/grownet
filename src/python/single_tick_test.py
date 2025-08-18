# from region import Region  # adapt imports to your layout
# from neuron import Neuron  # if you expose types
# Exact module names may differ in your project; adjust accordingly.

def log_fire(who, value: float):
    # Set a breakpoint here, or keep as a "tracepoint" style print
    print(f"FIRE {who.name}  value={value:.4f}  layer={who._layer.name}")

def main():
    region = Region("dbg")
    L0 = region._add_layer(1, 0, 0)
    L1 = region._add_layer(1, 0, 0)

    region._bind_input("in", [L0])
    region._bind_output("out", [L1])
    region._connect_layers(L0, L1, 1.0, False)

    # Register hooks (adjust to your API; many projects expose layer._neurons)
    for n in region.layers[L0]._neurons:
        n._register_fire_hook(log_fire)
    for n in region.layers[L1]._neurons:
        n._register_fire_hook(log_fire)

    # Breakpoints to set:
    # - Region._tick
    # - Layer._propagate_from
    # - Neuron._on_input
    # - SlotEngine._select_or_create_slot
    # - Neuron._fire
    # - Tract._on_source_fired, Synapse._transmit
    # - end of Region._tick (metrics)

    metrics = region._tick("in", 1.0)
    print("Metrics:", metrics)

if __name__ == "__main__":
    main()
