package ai.nektron.grownet;

import ai.nektron.grownet.metrics.RegionMetrics;

import java.util.Arrays;
import java.util.List;

/**
 * Minimal, step-through friendly demo:
 *  - one region
 *  - two layers
 *  - random fan-out from L0 -> L1 (prob=1.0 here so we always connect)
 *  - a FireHook that logs every neuron firing (set a breakpoint inside)
 *  - drives a single tick and prints RegionMetrics
 *
 * Set breakpoints on the lines tagged "BREAKPOINT" below, and also in:
 *   - Region.tick(...) at: layers.get(idx).forward(value);   // BREAKPOINT
 *   - Layer.forward(...)                                    // BREAKPOINT
 *   - Neuron.onInput(...)                                    // BREAKPOINT
 *   - SlotEngine.selectOrCreateSlot(...)                     // BREAKPOINT
 *   - Neuron.fire(...) / Synapse.transmit(...)               // BREAKPOINT
 *   - Tract.onSourceFired(...) (if you route via tracts)     // BREAKPOINT
 */
public final class TestSingleTick {

    public static void main(String[] args) {
        // ------------------------------------------------------------
        // 1) Region & layers
        // ------------------------------------------------------------
        Region region = new Region("dbg");
        int l0 = region.addLayer(
                /* excitatoryCount */ 1,
                /* inhibitoryCount */ 0,
                /* modulatoryCount */ 0);     // one excitatory neuron to drive

        int l1 = region.addLayer(
                /* excitatoryCount */ 1,
                /* inhibitoryCount */ 0,
                /* modulatoryCount */ 0);     // one neuron to observe fan‑out

        // ------------------------------------------------------------
        // 2) Wiring
        // ------------------------------------------------------------
        region.bindInput("in", Arrays.asList(l0));
        region.bindOutput("out", Arrays.asList(l1));

        int edges = region.connectLayers(l0, l1, /* probability */ 1.0, /* feedback */ false);
        System.out.printf("Connected L%d -> L%d with %d edge(s)%n", l0, l1, edges);

        // ------------------------------------------------------------
        // 3) Fire hook (log without pausing); set a breakpoint inside this
        // ------------------------------------------------------------
        // We'll capture the layer index when registering so the log shows layer info
        for (int layerIndex : Arrays.asList(l0, l1)) {
            final int layerIdx = layerIndex;
            List<Neuron> neurons = region.getLayers().get(layerIndex).getNeurons();
            for (Neuron neuron : neurons) {
                java.util.function.BiConsumer<Double, Neuron> hook = (value, who) -> {
                    // ---- BREAKPOINT: hook (fires on each neuron emission) ----
                    System.out.printf("FIRE id=%s value=%.6f layer=%d%n", who.getId(), value, layerIdx);
                };
                neuron.registerFireHook(hook);
            }
        }

        // ------------------------------------------------------------
        // 4) Optional: suggested breakpoints inside source
        // ------------------------------------------------------------
        // Region.tick(...) -> layers.get(idx).forward(value);          // BREAKPOINT
        // Layer.forward(...);                                          // BREAKPOINT
        // Neuron.onInput(...);                                         // BREAKPOINT
        // SlotEngine.selectOrCreateSlot(...);                          // BREAKPOINT
        // Neuron.fire(...);                                            // BREAKPOINT
        // Synapse.transmit(...);                                       // BREAKPOINT
        // Region.tick(...) end: before returning RegionMetrics         // BREAKPOINT

        // ------------------------------------------------------------
        // 5) Drive one tick
        // ------------------------------------------------------------
        double stimulus = 1.0; // adjust as needed
        RegionMetrics m = region.tick("in", stimulus);

        System.out.printf(
                "Metrics: deliveredEvents=%d, totalSlots=%d, totalSynapses=%d%n",
                m.getDeliveredEvents(), m.getTotalSlots(), m.getTotalSynapses());
    }
}
