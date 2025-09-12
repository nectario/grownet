package ai.nektron.grownet.tests;

import ai.nektron.grownet.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class GrowthGuardsTests {
    private Neuron makeNeuron(SlotConfig cfg) {
        LateralBus bus = new LateralBus();
        return new Neuron("N", bus, cfg, cfg.getSlotLimit());
    }

    @Test
    public void defaultsPreserveBehavior() {
        SlotConfig cfg = SlotConfig.fixed(10.0);
        cfg.setSlotLimit(1);
        Neuron n = makeNeuron(cfg);
        n.onInput(1.0);
        for (int i = 0; i < 3; i++) {
            n.onInput(2.0);
        }
        assertEquals(0, n.fallbackStreak);
    }

    @Test
    public void sameMissingSlotGuardBlocksAlternation() {
        SlotConfig cfg = SlotConfig.fixed(10.0);
        cfg.setSlotLimit(1);
        cfg.setFallbackGrowthRequiresSameMissingSlot(true);
        Neuron n = makeNeuron(cfg);
        n.onInput(1.0);
        double[] sequence = {2.0, 1.8, 2.0, 1.8, 2.0, 1.8};
        for (double value : sequence) {
            n.onInput(value);
        }
        assertTrue(n.fallbackStreak <= 1);
    }

    @Test
    public void minDeltaGateBlocksSmallDeltas() {
        SlotConfig cfg = SlotConfig.fixed(10.0);
        cfg.setSlotLimit(1);
        cfg.setMinDeltaPctForGrowth(70.0);
        Neuron n = makeNeuron(cfg);
        n.onInput(1.0);
        for (int i = 0; i < 3; i++) {
            n.onInput(1.6);
        }
        assertEquals(0, n.fallbackStreak);
        for (int i = 0; i < 3; i++) {
            n.onInput(1.8);
        }
        assertEquals(0, n.fallbackStreak);
    }
}
