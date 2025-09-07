package ai.nektron.grownet.tests;

import ai.nektron.grownet.ExcitatoryNeuron;
import ai.nektron.grownet.LateralBus;
import ai.nektron.grownet.SlotConfig;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

final class SynapsePruneTests {

    @Test
    void connectThenPruneStaleWeakEdges() {
        LateralBus bus = new LateralBus();
        SlotConfig cfg = SlotConfig.fixed(10.0);

        ExcitatoryNeuron a = new ExcitatoryNeuron("A", bus, cfg, -1);
        ExcitatoryNeuron b = new ExcitatoryNeuron("B", bus, cfg, -1);

        a.connect(b, /*feedback=*/false);
        assertEquals(1, a.getOutgoing().size(), "A must have one outgoing edge");

        // Do a few normal steps (not strictly required for pruning)
        for (int step = 0; step < 5; ++step) {
            a.onInput(1.0);
            bus.decay();
        }

        // Advance time so the edge becomes very stale.
        for (int i = 0; i < 20_000; ++i) bus.decay();

        // Prune with high min-strength so the default 0.0-strength edge qualifies.
        int removed = a.pruneSynapses(/*staleWindow=*/10_000, /*minStrength=*/0.9);
        assertEquals(1, removed, "the single weak + stale edge should be pruned");
        assertEquals(0, a.getOutgoing().size(), "no outgoing edges remain");
    }
}
