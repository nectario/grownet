package ai.nektron.grownet;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

final class SynapsePruneTests {
    @Test
    void connectAndPrune() {
        LateralBus bus = new LateralBus();
        ExcitatoryNeuron a = new ExcitatoryNeuron("A", bus);
        ExcitatoryNeuron b = new ExcitatoryNeuron("B", bus);

        a.connect(b, false);
        assertEquals(1, a.outgoing().size());

        // use synapse a few steps
        for (int step = 0; step < 5; step++) {
            a.onInput(1.0);
            bus.decay();
        }

        // advance time without use; force prune
        for (int i = 0; i < 20_000; i++) bus.decay();
        a.pruneSynapses(bus.currentStep(), 10_000, 0.9);
        assertEquals(0, a.outgoing().size());
    }
}
