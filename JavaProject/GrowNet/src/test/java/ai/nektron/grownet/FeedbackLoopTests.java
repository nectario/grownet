package ai.nektron.grownet;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

final class FeedbackLoopTests {
    @Test
    void feedbackSmoke() {
        LateralBus bus = new LateralBus();
        ExcitatoryNeuron parent = new ExcitatoryNeuron("P", bus);
        ExcitatoryNeuron child  = new ExcitatoryNeuron("C", bus);

        parent.connect(child, false);
        child.connect(parent, true);

        for (int step = 0; step < 20; step++) {
            parent.onInput(1.0);
            bus.decay();
        }
        assertTrue(parent.slots().size() >= 1);
        assertTrue(child.slots().size() >= 1);
    }
}
