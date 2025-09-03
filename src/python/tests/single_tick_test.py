# from region import Region  # adapt imports to your layout
# from neuron import Neuron  # if you expose types
# Exact module names may differ in your project; adjust accordingly.

def log_fire(who, value: float):
    # Set a breakpoint here, or keep as a "tracepoint" style print
    name = getattr(who, 'name', getattr(who, 'id', 'neuron'))
    print(f"FIRE {name}  value={value:.4f}")

def main():
    region = Region("dbg")
    L0 = region.add_layer(1, 0, 0)
    L1 = region.add_layer(1, 0, 0)

    region.bind_input("in", [L0])
    region.bind_output("out", [L1])
    region.connect_layers(L0, L1, 1.0, False)

    # Register hooks (adjust to your API; many projects expose layer._neurons)
    for n in region.layers[L0].neurons:
        n.register_fire_hook(log_fire)
    for n in region.layers[L1].neurons:
        n.register_fire_hook(log_fire)

    # Breakpoints to set:
    # - Region.tick
    # - Layer.propagate_from
    # - Neuron.on_input
    # - SlotEngine.select_or_create_slot
    # - Neuron.fire
    # - Tract.on_source_fired, Synapse.transmit
    # - end of Region.tick (metrics)

    metrics = region.tick("in", 1.0)
    print("Metrics:", metrics)

if __name__ == "__main__":
    main()
