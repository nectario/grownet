package ai.nektron.grownet;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

final class NeuronSlotTests {
    @Test
    void slotBinningByPercentDelta() {
        LateralBus bus = new LateralBus();
        Neuron n = new ExcitatoryNeuron("N0", bus);

        n.onInput(10.0);            // first slot
        assertEquals(1, n.slots().size());

        n.onInput(11.0);            // +10% -> new slot
        assertEquals(2, n.slots().size());

        n.onInput(11.2);            // +1.8% from 11 -> same slot
        assertEquals(2, n.slots().size());
    }
}
