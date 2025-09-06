# single_neuron_debug.py
# Run: python single_neuron_debug.py
# Tip: set breakpoints with your IDE or insert `breakpoint()` calls.

from region import Region  # adjust import paths to your layout

def main():
    # breakpoint()  # Inspect initial region state, bus, cfg
    region = Region("dbg")

    layer_id = region.add_layer(1, 0, 0)   # 1 excit, 0 inhib, 0 modul
    region.bind_input("stim", [layer_id])

    layer = region.get_layers()[layer_id]
    n0 = layer.get_neurons()[0]

    # Hook to observe spikes
    def on_fire(who, value: float):
        print(f"[HOOK] {who.get_name()} fired with value={value:.4f}")
        # breakpoint()  # Observe downstream fan-out

    n0.register_fire_hook(on_fire)

    # Critical-period like boost
    region.pulse_modulation(0.25)

    for tick_index in range(3):
        # breakpoint()  # Step into tick -> layer -> neuron -> slot engine
        metrics = region.tick("stim", 0.6)
        print(f"t={t} delivered={metrics.delivered_events} "
              f"slots={metrics.total_slots} synapses={metrics.total_synapses}")

    ps = region.prune(10000, 0.05, 10000, 0.05)
    print(f"Pruned synapses={ps.pruned_synapses} tracts={ps.pruned_edges}")

if __name__ == "__main__":
    main()
