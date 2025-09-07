package ai.nektron.grownet.tests;

import ai.nektron.grownet.LateralBus;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

public class LateralBusDecayTests {

    @Test
    public void busDecayResetsModulationAndIncrementsStep() {
        LateralBus bus = new LateralBus();
        bus.setInhibitionFactor(1.0);
        bus.setModulationFactor(2.7);
        long before = bus.getCurrentStep();

        bus.decay();

        assertEquals(0.9, bus.getInhibitionFactor(), 1e-12);
        assertEquals(1.0, bus.getModulationFactor(), 0.0);
        assertEquals(before + 1, bus.getCurrentStep());
    }
}

