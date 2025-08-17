package ai.nektron.grownet;

import ai.nektron.grownet.metrics.RegionMetrics;

import java.util.Arrays;
import java.util.List;

/**
 * TestSingleTick: create a tiny 2-layer region and watch a single scalar tick
 * flow through, with an on-fire hook for precise step-through debugging.
 *
 * Breakpoint suggestions (Java):
 *  - Layer.forward(...)
 *  - Neuron.onInput(...)
 *  - SlotEngine.selectOrCreateSlot(...)
 *  - Neuron.fire(...) / Synapse.transmit(...)
 *  - Tract.onSourceFired(...)  (if you route via tracts)
 *  - Region.tick(...) (before return of RegionMetrics)
 */
public final class TestSingleTick {

    public static void main(String[] args) {
        // --------------------------- 1) Region & layers ---------------------------
        Region region = new Region("dbg");

        int l0 = region.addLayer(
                1,  // excitatoryCount: one excitatory neuron to drive
                0,  // inhibitoryCount
                0   // modulatoryCount
        );

        int l1 = region.addLayer(
                1,  // one neuron to observe fan-out
                0,
                0
        );

        // ------------------------------- 2) Wiring -------------------------------
        region.bindInput("in", Arrays.asList(l0));
        region.bindOutput("out", Arrays.asList(l1));

        int edges = region.connectLayers(l0, l1, /* probability */ 1.0, /* feedback */ false);
        System.out.printf("Connected L%d -> L%d with %d edge(s)%n", l0, l1, edges);

        // ---------------------- 3) Fire hook + breakpoints -----------------------
        // NOTE: to avoid ambiguous overloads, we make the lambda a FireHook explicitly.
        // We also include the layer index in the log to see where the event came from.
        for (int layerIdx : Arrays.asList(l0, l1)) {
            final int currentLayer = layerIdx;
            List<Neuron> neurons = region.getLayers().get(layerIdx).getNeurons();
            for (Neuron neuron : neurons) {
//                FireHook hook = (Neuron who, double value) -> {
//                    // ---- BREAKPOINT: this runs on each neuron emission ----
//                    System.out.printf("FIRE id=%s value=%.6f layer=%d%n",
//                            who.getId(), value, currentLayer);
//                };
//                neuron.registerFireHook(hook);
            }
        }

        // If you prefer the BiConsumer overload instead, this is the unambiguous form:
        // neuron.registerFireHook((java.util.function.BiConsumer<Double, Neuron>) (value, who) -> { ... });

        // ------------------------------ 4) One tick ------------------------------
        double stimulus = 1.0;
        RegionMetrics m = region.tick("in", stimulus);

        System.out.printf("Metrics: deliveredEvents=%d, totalSlots=%d, totalSynapses=%d%n",
                m.getDeliveredEvents(), m.getTotalSlots(), m.getTotalSynapses());
    }
}
