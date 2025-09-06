package ai.nektron.grownet.demo;

import ai.nektron.grownet.Layer;
import ai.nektron.grownet.Neuron;
import ai.nektron.grownet.Region;
import ai.nektron.grownet.metrics.RegionMetrics;

import java.util.Arrays;

/**
 * Minimal 1D demo to step through a single scalar tick path and form 5 slots.
 *
 * Suggested breakpoints for step‑through debugging:
 *  - Region.tick(...)                  // drive scalar into edge and route
 *  - Layer.forward(...)                // fan into neurons for this tick
 *  - Neuron.onInput(...)               // slot selection + learning
 *  - SlotEngine.selectOrCreateSlot(...)// bin computation and fallback (called by onInput)
 */
public final class OneDimSlotDemo {
    public static void main(String[] args) {
        Region region = new Region("one-d-slot-demo");

        // One excitatory neuron layer (no I/M)
        int layerIndex = region.addLayer(1, 0, 0);
        region.bindInput("x", Arrays.asList(layerIndex));

        // FIRST anchor at first value (100.0), then 10% jumps → bins 0..4 (5 slots total)
        double[] values = new double[] { 100.0, 110.0, 120.0, 130.0, 140.0 };

        for (double v : values) {
            // Breakpoint here to follow a single tick
            RegionMetrics m = region.tick("x", v);
            System.out.printf("tick value=%.2f  delivered=%d  slots=%d  synapses=%d%n",
                    v, m.delivered_events, m.total_slots, m.total_synapses);
        }

        Layer L = region.getLayers().get(layerIndex);
        Neuron n = L.getNeurons().get(0);
        int slotCount = n.getSlots().size();
        System.out.println("\nFinal slot count: " + slotCount);
        System.out.println("Slot IDs (bins): " + n.getSlots().keySet());
    }
}

