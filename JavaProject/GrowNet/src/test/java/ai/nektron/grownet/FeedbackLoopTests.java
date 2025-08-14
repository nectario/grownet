package ai.nektron.grownet;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Verifies that a tiny feedback loop wires up and runs without recursion issues.
 * We only assert structural facts, not that the child necessarily fires.
 */
final class FeedbackLoopTests {

    @Test
    void feedbackLoopWiresAndRuns() {
        LateralBus bus = new LateralBus();
        SlotConfig cfg = SlotConfig.fixed(10.0);

        ExcitatoryNeuron parent = new ExcitatoryNeuron("P", bus, cfg, -1);
        ExcitatoryNeuron child  = new ExcitatoryNeuron("C", bus, cfg, -1);

        parent.connect(child, /*feedback=*/false);
        child.connect(parent, /*feedback=*/true);

        for (int step = 0; step < 20; ++step) {
            parent.onInput(1.0);
            bus.decay(); // advance the local time constant
        }

        // Parent certainly created at least one slot by being driven externally.
        assertFalse(parent.getSlots().isEmpty(), "parent slots should not be empty");

        // Structural checks: the loop stayed wired
        assertEquals(1, parent.getOutgoing().size(), "parent keeps one outgoing edge");
        assertEquals(1, child.getOutgoing().size(), "child keeps one outgoing edge");
    }
}
