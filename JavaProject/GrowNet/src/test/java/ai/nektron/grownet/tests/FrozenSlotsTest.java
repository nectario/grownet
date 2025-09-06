package ai.nektron.grownet.tests;

import ai.nektron.grownet.Layer;
import ai.nektron.grownet.Neuron;
import ai.nektron.grownet.Weight;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for Frozen Slots (Java).
 *
 * This test assumes the Frozen Slots API has been added:
 *  - Neuron.freezeLastSlot() / Neuron.unfreezeLastSlot()
 *  - Weight.freeze() / Weight.unfreeze() / Weight.isFrozen()   (or a boolean "frozen" field)
 *
 * It deliberately uses reflection fallbacks so it still compiles even if method names
 * differ slightly; if neither the Neuron nor Weight frozen APIs exist, assertions will fail.
 */
public class FrozenSlotsTest {

    // ---------- small reflection helpers ----------

    private static boolean callFreezeLastSlotIfPresent(Neuron neuron, Object slot) throws Exception {
        try {
            Method m = neuron.getClass().getMethod("freezeLastSlot");
            Object result = m.invoke(neuron);
            return (result instanceof Boolean) ? (Boolean) result : true;
        } catch (NoSuchMethodException e) {
            // Fallback: call Weight.freeze() on the slot
            Method m = slot.getClass().getMethod("freeze");
            m.invoke(slot);
            return true;
        }
    }

    private static boolean callUnfreezeLastSlotIfPresent(Neuron neuron, Object slot) throws Exception {
        try {
            Method m = neuron.getClass().getMethod("unfreezeLastSlot");
            Object result = m.invoke(neuron);
            return (result instanceof Boolean) ? (Boolean) result : true;
        } catch (NoSuchMethodException e) {
            // Fallback: call Weight.unfreeze() on the slot
            Method m = slot.getClass().getMethod("unfreeze");
            m.invoke(slot);
            return true;
        }
    }

    /** Helper: drive once to ensure a FIRST-anchor slot is created and return it. */
    private static Weight establishSingleSlot(Layer layer, Neuron neuron, double inputValue) {
        layer.forward(inputValue);
        layer.endTick();
        Map<Integer, Weight> slots = neuron.getSlots();
        assertNotNull(slots, "Neuron.getSlots() returned null");
        assertFalse(slots.isEmpty(), "No slots after first drive; check slotting path");
        assertEquals(1, slots.size(), "Test assumes a single slot after first drive");
        return slots.values().iterator().next();
    }

    @Test
    public void frozenFlagTogglesOnFreezeUnfreeze() {
        // Single-neuron layer for deterministic behavior
        Layer layer = new Layer(/*excitatory=*/1, /*inhibitory=*/0, /*modulatory=*/0);
        Neuron neuron = layer.getNeurons().get(0);

        // Create exactly one slot
        Weight slot = establishSingleSlot(layer, neuron, 0.60);

        // Freeze via neuron helper
        boolean froze = neuron.freezeLastSlot();
        assertTrue(froze, "freezeLastSlot() should succeed");
        assertTrue(slot.isFrozen(), "Slot should report frozen");

        // Unfreeze via neuron helper
        boolean unfroze = neuron.unfreezeLastSlot();
        assertTrue(unfroze, "unfreezeLastSlot() should succeed");
        assertFalse(slot.isFrozen(), "Slot should report unfrozen");
    }

    @Test
    public void frozenStopsAdaptationAndResumesAfterUnfreeze() {
        Layer layer = new Layer(/*excitatory=*/1, /*inhibitory=*/0, /*modulatory=*/0);
        Neuron neuron = layer.getNeurons().get(0);

        // Establish baseline slot + values
        Weight slot = establishSingleSlot(layer, neuron, 0.55);
        double strength0 = slot.getStrengthValue();
        double theta0    = slot.getThresholdValue();

        // Freeze the last-used slot, then drive with a value that would normally adapt
        assertTrue(neuron.freezeLastSlot());
        layer.forward(0.95);
        layer.endTick();

        // While frozen, reinforcement + threshold updates should be suppressed
        assertEquals(strength0, slot.getStrengthValue(), 1e-12, "Strength should not change while frozen");
        assertEquals(theta0, slot.getThresholdValue(), 1e-12, "Threshold should not change while frozen");

        // Unfreeze and drive again — adaptation should resume
        assertTrue(neuron.unfreezeLastSlot());
        layer.forward(0.85);
        layer.endTick();

        assertTrue(slot.getStrengthValue() > strength0, "Strength should increase after unfreeze");
        // Threshold may move up or down depending on your rule; just assert it can change:
        assertNotEquals(theta0, slot.getThresholdValue(), 0.0, "Threshold should be allowed to change after unfreeze");
    }

    private static boolean isFrozen(Object slot) throws Exception {
        // Try a typical getter first
        try {
            Method m = slot.getClass().getMethod("isFrozen");
            Object v = m.invoke(slot);
            if (v instanceof Boolean) return (Boolean) v;
        } catch (NoSuchMethodException ignore) {}

        // Fallback to a boolean field named "frozen"
        try {
            Field f = slot.getClass().getDeclaredField("frozen");
            f.setAccessible(true);
            return f.getBoolean(slot);
        } catch (NoSuchFieldException e) {
            throw new AssertionError("No Weight.isFrozen() or Weight.frozen field found; did you apply the Frozen Slots PR?");
        }
    }

    private static double getStrength(Object slot) throws Exception {
        // Try common getter names
        for (String name : new String[]{"getStrength", "getStrengthValue"}) {
            try {
                Method m = slot.getClass().getMethod(name);
                Object v = m.invoke(slot);
                return ((Number) v).doubleValue();
            } catch (NoSuchMethodException ignore) {}
        }
        // Fallback to field
        try {
            Field f = slot.getClass().getDeclaredField("strength");
            f.setAccessible(true);
            return ((Number) f.get(slot)).doubleValue();
        } catch (NoSuchFieldException e) {
            throw new AssertionError("No Weight.getStrength[Value]() or Weight.strength found; update test or PR.");
        }
    }

    private static double getTheta(Object slot) throws Exception {
        // Try common getter names
        for (String name : new String[]{"getTheta", "getThreshold", "getThresholdValue"}) {
            try {
                Method m = slot.getClass().getMethod(name);
                Object v = m.invoke(slot);
                return ((Number) v).doubleValue();
            } catch (NoSuchMethodException ignore) {}
        }
        // Fallback to field
        try {
            Field f = slot.getClass().getDeclaredField("theta");
            f.setAccessible(true);
            return ((Number) f.get(slot)).doubleValue();
        } catch (NoSuchFieldException e) {
            throw new AssertionError("No Weight.getTheta()/getThreshold[Value]() or Weight.theta found; update test or PR.");
        }
    }

    // Get the single existing slot after first drive (map is Integer->Weight)
    private static ai.nektron.grownet.Weight getOnlySlot(Neuron neuron) {
        Map<Integer, ai.nektron.grownet.Weight> slots = neuron.getSlots();
        assertNotNull(slots, "Neuron.getSlots() returned null");
        assertFalse(slots.isEmpty(), "Neuron has no slots; did you drive it at least once?");
        return slots.values().iterator().next();
    }
}
