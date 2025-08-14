package ai.nektron.grownet;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

final class NeuronSlotTests {

    @Test
    void slotBinningByPercentDelta() {
        LateralBus bus = new LateralBus();
        // 10% width, unlimited slots (slotLimit = -1).
        SlotConfig cfg = SlotConfig.fixed(10.0);
        ExcitatoryNeuron neuron = new ExcitatoryNeuron("N0", bus, cfg, -1);

        // First input -> imprint in slot 0
        neuron.onInput(10.0);
        assertEquals(1, neuron.getSlots().size(), "first slot should be created");

        // Δ = 10% exactly -> next bucket -> new slot
        neuron.onInput(11.0);
        assertEquals(2, neuron.getSlots().size(), "10% delta should open a new slot");

        // Δ ~ 1.8% -> stays in the same bucket
        neuron.onInput(11.2);
        assertEquals(2, neuron.getSlots().size(), "small delta must reuse the existing slot");

        assertTrue(neuron.getSlots().containsKey(0), "slot 0 exists");
        assertTrue(neuron.getSlots().containsKey(1), "slot 1 exists after 10% jump");
    }
}
